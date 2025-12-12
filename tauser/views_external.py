"""
Vistas externas para el sistema TAUSER (acceso público).
Este módulo contiene las vistas para el acceso externo a los terminales,
separado de las funciones administrativas internas de la casa de cambios.
"""
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Sum
from django.core.paginator import Paginator
from users.models import CustomUser
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import logging

from .models import (
    Terminal, 
    InventarioDivisaTerminal,
    InventarioDenominacionTerminal,
    DesgloseDenominacionOperacion,
    RegistroTransaccionTerminal,
    PINTerminalCliente
)
from transacciones.models import Transaccion, HistorialTransaccion
from clientes.models import Cliente
from divisas.models import Denominacion, Divisa, DesgloseDenominacion
from .services import (
    calcular_desglose_optimo,
    validar_desglose_cliente,
    generar_resumen_desglose
)

logger = logging.getLogger(__name__)


# ==================== HELPERS ====================

def verificar_sesion_tauser(request, terminal_codigo):
    """
    Verifica que haya una sesión válida para el terminal.
    Retorna (valido, mensaje_error, terminal, cliente)
    """
    if not request.session.get('pin_validado_external'):
        return False, 'Debe ingresar un PIN válido primero.', None, None
    
    terminal_sesion = request.session.get('terminal_codigo_external')
    if terminal_sesion != terminal_codigo:
        return False, 'Terminal no coincide con la sesión.', None, None
    
    try:
        terminal = Terminal.objects.get(codigo=terminal_codigo, is_activa=True)
    except Terminal.DoesNotExist:
        return False, 'Terminal no encontrado o inactivo.', None, None
    
    cliente_id = request.session.get('cliente_id_external')
    try:
        cliente = Cliente.objects.get(id=cliente_id, esta_activo=True)
    except Cliente.DoesNotExist:
        return False, 'Cliente no encontrado.', terminal, None
    
    return True, None, terminal, cliente


# ==================== PANTALLA PRINCIPAL ====================

def tauser_home(request):
    """
    Pantalla de inicio del sistema TAUSER externo.
    Muestra todos los terminales activos con su stock.
    """
    terminales = Terminal.objects.filter(is_activa=True).prefetch_related(
        'inventario_denominaciones__denominacion__divisa'
    ).order_by('nombre')
    
    # Calcular stock total por terminal
    terminales_con_stock = []
    for terminal in terminales:
        inventarios = terminal.inventario_denominaciones.filter(
            denominacion__is_active=True
        ).select_related('denominacion__divisa')
        
        # Agrupar por divisa
        stock_por_divisa = {}
        for inv in inventarios:
            divisa_code = inv.denominacion.divisa.code
            divisa_nombre = inv.denominacion.divisa.nombre
            if divisa_code not in stock_por_divisa:
                stock_por_divisa[divisa_code] = {
                    'nombre': divisa_nombre,
                    'total': Decimal('0')
                }
            stock_por_divisa[divisa_code]['total'] += inv.valor_total
        
        terminales_con_stock.append({
            'terminal': terminal,
            'stock_por_divisa': stock_por_divisa
        })
    
    # Verificar estado del MFA desde la configuración
    from mfa.models import MFAConfig
    mfa_config = MFAConfig.get_config()
    
    context = {
        'terminales_con_stock': terminales_con_stock,
        'titulo': 'Terminales TAUSER',
        'mfa_enabled': mfa_config.mfa_tauser_enabled,
    }
    
    return render(request, 'tauser_external/home.html', context)


# ==================== SELECCIÓN DE TERMINAL ====================

def seleccionar_terminal_externo(request):
    """
    Lista de terminales disponibles para selección (acceso externo).
    """
    terminales = Terminal.objects.filter(is_activa=True).order_by('nombre')
    
    context = {
        'terminales': terminales,
        'titulo': 'Seleccionar Terminal'
    }
    
    return render(request, 'tauser_external/seleccionar_terminal.html', context)


# ==================== ACCESO CON PIN ====================

@require_http_methods(["GET", "POST"])
def acceso_terminal(request, terminal_codigo):
    """
    Pantalla de acceso con PIN al terminal (versión externa).
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    if request.method == 'POST':
        pin_ingresado = request.POST.get('pin', '').strip()
        
        if not pin_ingresado:
            messages.error(request, 'Por favor ingrese su PIN.')
            return render(request, 'tauser_external/acceso_terminal.html', {'terminal': terminal})
        
        # ==================== PIN MAESTRO PARA DESARROLLADORES ====================
        if pin_ingresado == '000000':
            try:
                cliente_dev = Cliente.objects.filter(esta_activo=True).first()
                
                if not cliente_dev:
                    messages.error(request, 'No hay clientes activos en el sistema.')
                    return render(request, 'tauser_external/acceso_terminal.html', {'terminal': terminal})
                
                # Guardar información en la sesión (variables con sufijo _external)
                request.session['pin_validado_external'] = True
                request.session['pin_acceso_id_external'] = None
                request.session['cliente_id_external'] = cliente_dev.id
                request.session['terminal_codigo_external'] = terminal.codigo
                request.session['terminal_id_external'] = terminal.id
                request.session['modo_dev_external'] = True
                
                messages.warning(
                    request, 
                    f'⚠️ ACCESO DE DESARROLLO - Cliente: {cliente_dev.nombre_completo}'
                )
                
                logger.warning(
                    f"[TAUSER-EXTERNAL] Acceso con PIN maestro - Terminal: {terminal.codigo}, "
                    f"Usuario: {request.user.username if request.user.is_authenticated else 'Anónimo'}"
                )
                
                RegistroTransaccionTerminal.objects.create(
                    terminal=terminal,
                    cliente=cliente_dev,
                    tipo_operacion='CONSULTA',
                    fue_exitoso=True,
                    mensaje_error='[DEV MODE] Acceso externo con PIN maestro 000000'
                )
                
                return redirect('tauser_external:menu_tauser', terminal_codigo=terminal.codigo)
                
            except Exception as e:
                logger.error(f"Error en acceso con PIN maestro: {e}")
                messages.error(request, 'Error al acceder con PIN maestro.')
                return render(request, 'tauser_external/acceso_terminal.html', {'terminal': terminal})
        
        # ==================== VALIDACIÓN NORMAL DE PIN ====================
        try:
            pin_acceso = PINTerminalCliente.objects.select_related('cliente').get(
                pin=pin_ingresado,
                usado=False,
                fecha_expiracion__gt=timezone.now()
            )
            
            # Marcar el PIN como usado
            pin_acceso.usado = True
            pin_acceso.fecha_uso = timezone.now()
            pin_acceso.save()
            
            # Guardar información en la sesión (variables con sufijo _external)
            request.session['pin_validado_external'] = True
            request.session['pin_acceso_id_external'] = pin_acceso.id
            request.session['cliente_id_external'] = pin_acceso.cliente.id
            request.session['terminal_codigo_external'] = terminal.codigo
            request.session['terminal_id_external'] = terminal.id
            request.session['modo_dev_external'] = False
            
            messages.success(
                request, 
                f'¡Bienvenido {pin_acceso.cliente.nombre_completo}!'
            )
            
            logger.info(
                f"[TAUSER-EXTERNAL] Acceso exitoso - Terminal: {terminal.codigo}, "
                f"Cliente: {pin_acceso.cliente.nombre_completo}"
            )
            
            RegistroTransaccionTerminal.objects.create(
                terminal=terminal,
                cliente=pin_acceso.cliente,
                tipo_operacion='CONSULTA',
                fue_exitoso=True,
                pin_usado=pin_acceso
            )
            
            return redirect('tauser_external:menu_tauser', terminal_codigo=terminal.codigo)
            
        except PINTerminalCliente.DoesNotExist:
            messages.error(
                request, 
                'PIN inválido, expirado o ya utilizado.'
            )
            
            logger.warning(
                f"[TAUSER-EXTERNAL] Intento fallido - Terminal: {terminal.codigo}, PIN: {pin_ingresado}"
            )
            
            RegistroTransaccionTerminal.objects.create(
                terminal=terminal,
                cliente=None,
                tipo_operacion='CONSULTA',
                fue_exitoso=False,
                mensaje_error=f"PIN inválido: {pin_ingresado}"
            )
            
            return render(request, 'tauser_external/acceso_terminal.html', {'terminal': terminal})
    
    # GET request
    return render(request, 'tauser_external/acceso_terminal.html', {'terminal': terminal})


# ==================== MENÚ PRINCIPAL ====================

def menu_tauser(request, terminal_codigo):
    """
    Menú principal del TAUSER - Ingreso de código TAUSER de 8 dígitos.
    No requiere autenticación previa.
    """
    # Obtener el terminal
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    # Renderizar el formulario de ingreso de código TAUSER
    context = {
        'terminal': terminal,
    }
    
    return render(request, 'tauser_external/menu_cliente.html', context)


# ==================== VER TRANSACCIONES ====================

def ver_transacciones(request, terminal_codigo):
    """
    Muestra las transacciones pendientes del cliente.
    """
    valido, mensaje, terminal, cliente = verificar_sesion_tauser(request, terminal_codigo)
    
    if not valido:
        messages.warning(request, mensaje)
        return redirect('tauser_external:acceso_terminal', terminal_codigo=terminal_codigo)
    
    # Transacciones de retiro (compra de divisa extranjera)
    transacciones_retiro = Transaccion.objects.filter(
        cliente=cliente,
        tipo_operacion='compra',
        estado='pagada'
    ).exclude(
        divisa_destino__code='PYG'
    ).select_related('divisa_origen', 'divisa_destino').order_by('-fecha_creacion')
    
    # Transacciones de pago (venta de divisa)
    transacciones_pago = Transaccion.objects.filter(
        cliente=cliente,
        tipo_operacion='venta',
        estado='pendiente',
        divisa_destino__code='PYG'
    ).select_related('divisa_origen', 'divisa_destino').order_by('-fecha_creacion')
    
    # Verificar disponibilidad
    transacciones_retiro_verificadas = []
    for trans in transacciones_retiro:
        tiene_denominaciones, desglose = terminal.tiene_denominaciones_suficientes(
            trans.divisa_destino,
            trans.monto_destino
        )
        transacciones_retiro_verificadas.append({
            'transaccion': trans,
            'disponible': tiene_denominaciones,
            'desglose': desglose
        })
    
    context = {
        'terminal': terminal,
        'cliente': cliente,
        'transacciones_retiro': transacciones_retiro_verificadas,
        'transacciones_pago': transacciones_pago,
    }
    
    return render(request, 'tauser_external/ver_transacciones.html', context)


# ==================== PROCESAR RETIRO ====================

def procesar_retiro(request, terminal_codigo, transaccion_id):
    """
    Procesa un retiro de divisa extranjera.
    """
    valido, mensaje, terminal, cliente = verificar_sesion_tauser(request, terminal_codigo)
    
    if not valido:
        messages.warning(request, mensaje)
        return redirect('tauser_external:acceso_terminal', terminal_codigo=terminal_codigo)
    
    transaccion = get_object_or_404(Transaccion, id=transaccion_id, cliente=cliente)
    
    if request.method == 'POST':
        # TODO: Implementar lógica de retiro
        messages.success(request, 'Retiro procesado exitosamente.')
        return redirect('tauser_external:ver_transacciones', terminal_codigo=terminal_codigo)
    
    # Calcular desglose
    divisa = transaccion.divisa_destino
    monto = transaccion.monto_destino
    
    inventarios = InventarioDenominacionTerminal.objects.filter(
        terminal=terminal,
        denominacion__divisa=divisa,
        cantidad__gt=0
    ).select_related('denominacion')
    
    resultado = calcular_desglose_optimo(inventarios, monto)
    
    context = {
        'terminal': terminal,
        'cliente': cliente,
        'transaccion': transaccion,
        'desglose': resultado.get('desglose', {}),
        'posible': resultado.get('posible', False),
    }
    
    return render(request, 'tauser_external/procesar_retiro.html', context)


# ==================== PROCESAR PAGO ====================

def procesar_pago(request, terminal_codigo, transaccion_id):
    """
    Procesa un pago en guaraníes por venta de divisa.
    """
    valido, mensaje, terminal, cliente = verificar_sesion_tauser(request, terminal_codigo)
    
    if not valido:
        messages.warning(request, mensaje)
        return redirect('tauser_external:acceso_terminal', terminal_codigo=terminal_codigo)
    
    transaccion = get_object_or_404(Transaccion, id=transaccion_id, cliente=cliente)
    
    # Solo permitir procesar transacciones pendientes
    if transaccion.estado != 'pendiente':
        messages.warning(request, f'Esta transacción ya fue procesada. Estado actual: {transaccion.get_estado_display()}')
        return redirect('tauser_external:ver_transacciones', terminal_codigo=terminal_codigo)
    
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '').strip()
        
        try:
            # Cambiar estado de la transacción a completada
            from transacciones.models import HistorialTransaccion
            
            with transaction.atomic():
                transaccion.estado = 'completada'
                transaccion.save()
                
                # Registrar en historial
                HistorialTransaccion.objects.create(
                    transaccion=transaccion,
                    estado_anterior='pendiente',
                    estado_nuevo='completada',
                    observaciones=f'Pago confirmado en terminal {terminal.codigo}. {observaciones}' if observaciones else f'Pago confirmado en terminal {terminal.codigo}',
                    modificado_por=request.user
                )
            
            messages.success(request, f'✓ Pago confirmado exitosamente. Transacción {transaccion.numero_transaccion} completada.')
            return redirect('tauser_external:ver_transacciones', terminal_codigo=terminal_codigo)
            
        except Exception as e:
            logger.error(f"Error al procesar pago en terminal {terminal_codigo}: {e}", exc_info=True)
            messages.error(request, f'Error al procesar el pago: {str(e)}')
    
    context = {
        'terminal': terminal,
        'cliente': cliente,
        'transaccion': transaccion,
    }
    
    return render(request, 'tauser_external/procesar_pago.html', context)


# ==================== REPOSICIÓN (NUEVO) ====================

def menu_reposicion(request, terminal_codigo):
    """
    Menú de reposición de denominaciones en terminal.
    """
    valido, mensaje, terminal, cliente = verificar_sesion_tauser(request, terminal_codigo)
    
    if not valido:
        messages.warning(request, mensaje)
        return redirect('tauser_external:acceso_terminal', terminal_codigo=terminal_codigo)
    
    # Obtener inventario actual por divisa
    inventarios = InventarioDenominacionTerminal.objects.filter(
        terminal=terminal
    ).select_related('denominacion__divisa').order_by(
        'denominacion__divisa__code',
        '-denominacion__valor'
    )
    
    # Agrupar por divisa
    inventarios_por_divisa = {}
    for inv in inventarios:
        divisa_code = inv.denominacion.divisa.code
        if divisa_code not in inventarios_por_divisa:
            inventarios_por_divisa[divisa_code] = {
                'divisa': inv.denominacion.divisa,
                'denominaciones': []
            }
        inventarios_por_divisa[divisa_code]['denominaciones'].append(inv)
    
    # Obtener todas las denominaciones activas para reposición
    todas_denominaciones = Denominacion.objects.filter(
        is_active=True
    ).select_related('divisa').order_by('divisa__code', '-valor')
    
    denominaciones_por_divisa = {}
    for denom in todas_denominaciones:
        divisa_code = denom.divisa.code
        if divisa_code not in denominaciones_por_divisa:
            denominaciones_por_divisa[divisa_code] = {
                'divisa': denom.divisa,
                'denominaciones': []
            }
        
        # Buscar inventario actual
        inventario_actual = next(
            (inv for inv in inventarios if inv.denominacion_id == denom.id),
            None
        )
        
        denominaciones_por_divisa[divisa_code]['denominaciones'].append({
            'denominacion': denom,
            'inventario': inventario_actual,
            'cantidad_actual': inventario_actual.cantidad if inventario_actual else 0,
            'necesita_reposicion': inventario_actual.necesita_reposicion if inventario_actual else True,
        })
    
    context = {
        'terminal': terminal,
        'cliente': cliente,
        'denominaciones_por_divisa': denominaciones_por_divisa,
    }
    
    return render(request, 'tauser_external/menu_reposicion.html', context)


def ejecutar_reposicion(request, terminal_codigo):
    """
    Ejecuta la reposición de denominaciones.
    """
    if request.method != 'POST':
        return redirect('tauser_external:menu_reposicion', terminal_codigo=terminal_codigo)
    
    valido, mensaje, terminal, cliente = verificar_sesion_tauser(request, terminal_codigo)
    
    if not valido:
        messages.warning(request, mensaje)
        return redirect('tauser_external:acceso_terminal', terminal_codigo=terminal_codigo)
    
    try:
        with transaction.atomic():
            reposiciones = []
            total_reposiciones = 0
            
            # Procesar cada denominación del formulario
            for key, value in request.POST.items():
                if key.startswith('reposicion_'):
                    denom_id = int(key.split('_')[1])
                    cantidad = int(value or 0)
                    
                    if cantidad <= 0:
                        continue
                    
                    denominacion = Denominacion.objects.get(id=denom_id)
                    
                    # Obtener o crear inventario
                    inventario, created = InventarioDenominacionTerminal.objects.get_or_create(
                        terminal=terminal,
                        denominacion=denominacion,
                        defaults={'cantidad': 0}
                    )
                    
                    cantidad_anterior = inventario.cantidad
                    inventario.cantidad += cantidad
                    inventario.ultima_reposicion = timezone.now()
                    if request.user.is_authenticated:
                        inventario.actualizado_por = request.user
                    inventario.save()
                    
                    reposiciones.append({
                        'denominacion': denominacion,
                        'cantidad': cantidad,
                        'anterior': cantidad_anterior,
                        'nueva': inventario.cantidad,
                    })
                    
                    total_reposiciones += cantidad
                    
                    logger.info(
                        f"[TAUSER-EXTERNAL] Reposición - Terminal: {terminal.codigo}, "
                        f"Denominación: {denominacion}, Cantidad: +{cantidad}"
                    )
            
            if total_reposiciones > 0:
                messages.success(
                    request,
                    f"✓ Reposición exitosa: {total_reposiciones} billetes agregados."
                )
                
                # Registrar operación
                RegistroTransaccionTerminal.objects.create(
                    terminal=terminal,
                    cliente=cliente,
                    tipo_operacion='REPOSICION',
                    fue_exitoso=True,
                    mensaje_error=f'Reposición de {total_reposiciones} billetes'
                )
            else:
                messages.warning(request, "No se realizaron reposiciones.")
    
    except Exception as e:
        messages.error(request, f"Error al reponer denominaciones: {str(e)}")
        logger.error(f"[TAUSER-EXTERNAL] Error en reposición: {e}", exc_info=True)
    
    return redirect('tauser_external:menu_reposicion', terminal_codigo=terminal_codigo)


# ==================== VERIFICAR CÓDIGO TAUSER ====================

@require_http_methods(["POST"])
def verificar_codigo_tauser(request, terminal_codigo):
    """
    Verifica el código TAUSER ingresado y envía OTP para validación.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    # Obtener código de los 8 campos individuales
    codigo_partes = []
    for i in range(1, 9):
        digit = request.POST.get(f'digit-{i}', '').strip().upper()
        if not digit:
            messages.error(request, 'Por favor, complete todos los dígitos del código.')
            return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
        codigo_partes.append(digit)
    
    tauser_code = ''.join(codigo_partes)
    
    # Buscar transacción por código
    try:
        transaccion = Transaccion.objects.select_related(
            'cliente', 'divisa_origen', 'divisa_destino', 'tauser_terminal'
        ).get(tauser_code=tauser_code)
    except Transaccion.DoesNotExist:
        messages.error(request, f'❌ Código TAUSER "{tauser_code}" no encontrado.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    # NUEVO: Verificar que el código solo sea válido en el terminal asignado (solo para compras)
    if transaccion.tipo_operacion == 'compra' and transaccion.tauser_terminal:
        if transaccion.tauser_terminal.codigo != terminal_codigo:
            messages.error(
                request,
                f'❌ Este código TAUSER solo es válido en el terminal: '
                f'{transaccion.tauser_terminal.nombre} ({transaccion.tauser_terminal.codigo}). '
                f'Por favor, dirígete al terminal correcto para retirar tu divisa.'
            )
            return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    # Verificar estado de la transacción
    if transaccion.tipo_operacion == 'compra':
        # Compras deben estar en estado 'pagada' para retirar
        if transaccion.estado != 'pagada':
            messages.error(
                request,
                f'❌ Esta transacción está en estado "{transaccion.get_estado_display()}". '
                f'Solo se pueden retirar compras pagadas.'
            )
            return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    elif transaccion.tipo_operacion == 'venta':
        # Ventas deben estar en estado 'pendiente' para depositar
        if transaccion.estado not in ['pendiente', 'pagada']:
            messages.error(
                request,
                f'❌ Esta transacción está en estado "{transaccion.get_estado_display()}". '
                f'No se puede procesar.'
            )
            return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    # Guardar transacción en sesión
    request.session['transaccion_tauser_id'] = transaccion.id
    request.session['terminal_tauser_codigo'] = terminal_codigo
    request.session.modified = True
    
    # Verificar si MFA está habilitado para TAUSER desde la configuración
    from mfa.models import MFAConfig
    mfa_config = MFAConfig.get_config()
    
    if not mfa_config.mfa_tauser_enabled:
        # MFA deshabilitado - ir directo a detalles
        request.session['transaccion_mfa_verificada'] = True
        request.session.modified = True
        
        messages.success(request, f'✓ Código TAUSER verificado correctamente.')
        
        if transaccion.tipo_operacion == 'compra':
            return redirect('tauser_external:mostrar_detalle_retiro', terminal_codigo=terminal_codigo)
        else:  # venta
            return redirect('tauser_external:mostrar_detalle_deposito', terminal_codigo=terminal_codigo)
    
    # MFA habilitado - continuar con proceso normal
    # Generar y enviar OTP al correo del cliente
    from mfa.utils import generate_and_send_otp
    
    # Obtener usuario: primero intentar procesado_por, luego el primer usuario asignado al cliente
    cliente_user = transaccion.procesado_por or transaccion.cliente.usuarios.first()
    
    if not cliente_user or not cliente_user.email:
        messages.error(request, '❌ No se pudo enviar el código de verificación. Email no encontrado.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    if generate_and_send_otp(cliente_user, request):
        messages.success(
            request,
            f'✓ Código de verificación enviado a {cliente_user.email[:3]}***@***'
        )
        return redirect('tauser_external:mfa_transaccion', terminal_codigo=terminal_codigo)
    else:
        messages.error(request, '❌ Error al enviar el código de verificación. Intente nuevamente.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)


@require_http_methods(["GET", "POST"])
def mfa_transaccion(request, terminal_codigo):
    """
    Vista para ingresar código MFA y acceder a la transacción.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    transaccion_id = request.session.get('transaccion_tauser_id')
    if not transaccion_id:
        messages.error(request, 'Sesión expirada. Por favor, ingrese el código nuevamente.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    transaccion = get_object_or_404(Transaccion, id=transaccion_id)
    # Obtener usuario: primero intentar procesado_por, luego el primer usuario asignado al cliente
    cliente_user = transaccion.procesado_por or transaccion.cliente.usuarios.first()
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not otp_code:
            messages.error(request, 'Por favor, ingrese el código de verificación.')
            return redirect('tauser_external:mfa_transaccion', terminal_codigo=terminal_codigo)
        
        if len(otp_code) != 6 or not otp_code.isdigit():
            messages.error(request, 'El código debe tener exactamente 6 dígitos.')
            return redirect('tauser_external:mfa_transaccion', terminal_codigo=terminal_codigo)
        
        # Verificar OTP
        from mfa.utils import check_otp_validity
        
        if check_otp_validity(cliente_user, otp_code):
            # Código válido - marcar sesión como verificada
            request.session['transaccion_mfa_verificada'] = True
            request.session.modified = True
            
            messages.success(request, '✓ Código verificado correctamente.')
            
            # Redirigir según tipo de operación
            if transaccion.tipo_operacion == 'compra':
                return redirect('tauser_external:mostrar_detalle_retiro', terminal_codigo=terminal_codigo)
            else:  # venta
                return redirect('tauser_external:mostrar_detalle_deposito', terminal_codigo=terminal_codigo)
        else:
            messages.error(request, '❌ Código incorrecto o expirado. Intente nuevamente.')
            return redirect('tauser_external:mfa_transaccion', terminal_codigo=terminal_codigo)
    
    # Enmascarar email
    email = cliente_user.email
    email_parts = email.split('@')
    if len(email_parts) == 2:
        local = email_parts[0]
        domain = email_parts[1]
        email_masked = f"{local[:3]}***@{domain[:1]}***.com"
    else:
        email_masked = f"{email[:3]}***"
    
    context = {
        'terminal': terminal,
        'transaccion': transaccion,
        'email_masked': email_masked,
    }
    
    return render(request, 'tauser_external/mfa_transaccion.html', context)


def reenviar_mfa(request, terminal_codigo):
    """
    Reenvía el código MFA.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    transaccion_id = request.session.get('transaccion_tauser_id')
    if not transaccion_id:
        messages.error(request, 'Sesión expirada.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    transaccion = get_object_or_404(Transaccion, id=transaccion_id)
    # Obtener usuario: primero intentar procesado_por, luego el primer usuario asignado al cliente
    cliente_user = transaccion.procesado_por or transaccion.cliente.usuarios.first()
    
    from mfa.utils import generate_and_send_otp
    
    if generate_and_send_otp(cliente_user, request):
        messages.success(request, '✓ Código reenviado.')
    else:
        messages.error(request, '❌ Error al reenviar el código.')
    
    return redirect('tauser_external:mfa_transaccion', terminal_codigo=terminal_codigo)


# ==================== VISTAS DE DETALLE ====================

@require_http_methods(["GET"])
def mostrar_detalle_retiro(request, terminal_codigo):
    """
    Muestra el detalle de una compra para retiro de divisas.
    Solo accesible después de validar código tauser + MFA.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    # Verificar que haya MFA validado
    if not request.session.get('transaccion_mfa_verificada'):
        messages.error(request, '❌ Debe verificar su identidad primero.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    transaccion_id = request.session.get('transaccion_tauser_id')
    if not transaccion_id:
        messages.error(request, '❌ Sesión inválida.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    try:
        transaccion = Transaccion.objects.select_related(
            'cliente', 'divisa_origen', 'divisa_destino'
        ).get(id=transaccion_id)
    except Transaccion.DoesNotExist:
        messages.error(request, '❌ Transacción no encontrada.')
        request.session.flush()
        return redirect('tauser_external:home')
    
    # Verificar que sea compra
    if transaccion.tipo_operacion != 'compra':
        messages.error(request, '❌ Esta operación no es un retiro.')
        request.session.flush()
        return redirect('tauser_external:home')
    
    # Verificar estado
    if transaccion.estado != 'pagada':
        messages.error(request, f'❌ Estado inválido: {transaccion.get_estado_display()}')
        request.session.flush()
        return redirect('tauser_external:home')
    
    # Verificar que el terminal tenga denominaciones de esa divisa
    denominaciones = InventarioDenominacionTerminal.objects.filter(
        terminal=terminal,
        denominacion__divisa=transaccion.divisa_destino,
    ).select_related('denominacion').order_by('-denominacion__valor')
    
    if not denominaciones.exists():
        messages.error(request, f'❌ Este terminal no maneja {transaccion.divisa_destino.nombre}.')
        request.session.flush()
        return redirect('tauser_external:home')
    
    # Calcular stock total disponible de esa divisa
    stock_total = sum(
        inv.denominacion.valor * inv.cantidad
        for inv in denominaciones
    )
    
    # Verificar stock suficiente
    if stock_total < transaccion.monto_destino:
        messages.warning(
            request,
            f'⚠️ Stock insuficiente. Disponible: {stock_total} {transaccion.divisa_destino.code}'
        )
    
    # Filtrar solo denominaciones con cantidad > 0 para mostrar
    denominaciones_disponibles = denominaciones.filter(cantidad__gt=0)
    
    context = {
        'terminal': terminal,
        'terminal_codigo': terminal_codigo,
        'transaccion': transaccion,
        'stock_total': stock_total,
        'denominaciones': denominaciones_disponibles,
        'puede_retirar': stock_total >= transaccion.monto_destino,
    }
    
    return render(request, 'tauser_external/detalle_retiro.html', context)


@require_http_methods(["GET"])
def mostrar_detalle_deposito(request, terminal_codigo):
    """
    Muestra el detalle de una venta para depósito de divisas.
    Solo accesible después de validar código tauser + MFA.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    # Verificar que haya MFA validado
    if not request.session.get('transaccion_mfa_verificada'):
        messages.error(request, '❌ Debe verificar su identidad primero.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    transaccion_id = request.session.get('transaccion_tauser_id')
    if not transaccion_id:
        messages.error(request, '❌ Sesión inválida.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    try:
        transaccion = Transaccion.objects.select_related(
            'cliente', 'divisa_origen', 'divisa_destino'
        ).get(id=transaccion_id)
    except Transaccion.DoesNotExist:
        messages.error(request, '❌ Transacción no encontrada.')
        request.session.flush()
        return redirect('tauser_external:home')
    
    # Verificar que sea venta
    if transaccion.tipo_operacion != 'venta':
        messages.error(request, '❌ Esta operación no es un depósito.')
        request.session.flush()
        return redirect('tauser_external:home')
    
    # Verificar estado
    if transaccion.estado not in ['pendiente', 'pagada']:
        messages.error(request, f'❌ Estado inválido: {transaccion.get_estado_display()}')
        request.session.flush()
        return redirect('tauser_external:home')
    
    # Obtener inventario del terminal para la divisa
    try:
        inventario = InventarioDivisaTerminal.objects.get(
            terminal=terminal,
            divisa=transaccion.divisa_origen  # La divisa que vende el cliente
        )
    except InventarioDivisaTerminal.DoesNotExist:
        # Si no existe, se puede crear al depositar
        inventario = None
    
    # Obtener denominaciones aceptadas
    denominaciones = Denominacion.objects.filter(
        divisa=transaccion.divisa_origen,
        is_active=True
    ).order_by('-valor')
    
    context = {
        'terminal': terminal,
        'terminal_codigo': terminal_codigo,
        'transaccion': transaccion,
        'inventario': inventario,
        'denominaciones': denominaciones,
    }
    
    return render(request, 'tauser_external/detalle_deposito.html', context)


# ==================== ACCIONES DE RETIRO Y DEPÓSITO ====================

@require_http_methods(["POST"])
def procesar_retiro(request, terminal_codigo, transaccion_id):
    """
    Procesa el retiro de divisas en el terminal TAUSER.
    Calcula denominaciones óptimas, actualiza inventario y cambia estado de transacción.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    # Verificar que haya MFA validado
    if not request.session.get('transaccion_mfa_verificada'):
        messages.error(request, '❌ Debe verificar su identidad primero.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    # Verificar que la transacción en sesión coincida
    transaccion_sesion_id = request.session.get('transaccion_tauser_id')
    if not transaccion_sesion_id or transaccion_sesion_id != transaccion_id:
        messages.error(request, '❌ Sesión inválida.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    try:
        transaccion = Transaccion.objects.select_related(
            'cliente', 'divisa_origen', 'divisa_destino'
        ).get(id=transaccion_id)
    except Transaccion.DoesNotExist:
        messages.error(request, '❌ Transacción no encontrada.')
        request.session.flush()
        return redirect('tauser_external:home')
    
    # Verificar que sea compra y esté pagada
    if transaccion.tipo_operacion != 'compra' or transaccion.estado != 'pagada':
        messages.error(request, '❌ Esta transacción no puede ser procesada.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    try:
        with transaction.atomic():
            # Obtener inventarios disponibles
            inventarios = InventarioDenominacionTerminal.objects.filter(
                terminal=terminal,
                denominacion__divisa=transaccion.divisa_destino,
                cantidad__gt=0
            ).select_related('denominacion').order_by('-denominacion__valor')
            
            # Calcular desglose óptimo
            from .services import calcular_desglose_optimo
            resultado = calcular_desglose_optimo(inventarios, transaccion.monto_destino)
            
            if not resultado['posible']:
                messages.error(
                    request,
                    f'❌ No hay suficiente stock para completar el retiro. '
                    f'Disponible: {resultado["monto_cubierto"]}, Solicitado: {transaccion.monto_destino}'
                )
                return redirect('tauser_external:mostrar_detalle_retiro', terminal_codigo=terminal_codigo)
            
            # Registrar operación en el terminal PRIMERO
            registro_operacion = RegistroTransaccionTerminal.objects.create(
                terminal=terminal,
                transaccion_original=transaccion,
                cliente=transaccion.cliente,
                tipo_operacion='RETIRO',
                monto_operacion=transaccion.monto_destino,
                divisa=transaccion.divisa_destino,
                fue_exitoso=True,
                mensaje_error=''
            )
            
            # Crear movimiento de inventario
            from .models import MovimientoInventarioTerminal, DetalleMovimientoInventario
            movimiento = MovimientoInventarioTerminal.objects.create(
                terminal=terminal,
                tipo_movimiento='EXTRACCION',
                cliente=transaccion.cliente,
                transaccion=transaccion,
                observaciones=f'Retiro de {transaccion.monto_destino} {transaccion.divisa_destino.code}'
            )
            
            # Aplicar el desglose al inventario
            for datos in resultado['desglose'].values():
                inventario = datos['inventario']
                cantidad = datos['cantidad']
                cantidad_anterior = inventario.cantidad
                
                inventario.cantidad -= cantidad
                inventario.save()
                
                # Registrar el desglose en DesgloseDenominacionOperacion
                DesgloseDenominacionOperacion.objects.create(
                    registro_operacion=registro_operacion,
                    denominacion=inventario.denominacion,
                    cantidad=cantidad,
                    tipo_movimiento='ENTREGA'
                )
                
                # Registrar detalle del movimiento
                DetalleMovimientoInventario.objects.create(
                    movimiento=movimiento,
                    denominacion=inventario.denominacion,
                    cantidad=cantidad,
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=inventario.cantidad
                )
            
            # Cambiar estado de la transacción a completado
            transaccion.estado = 'completado'
            transaccion.save()
            
            # Registrar en historial
            HistorialTransaccion.objects.create(
                transaccion=transaccion,
                estado_anterior='pagada',
                estado_nuevo='completado',
                observaciones=f'Retiro procesado en terminal {terminal.nombre} (TAUSER)',
                modificado_por=None  # Sistema TAUSER
            )
            
            # Guardar información del retiro exitoso en sesión
            request.session['retiro_exitoso'] = {
                'terminal_codigo': terminal_codigo,
                'terminal_nombre': terminal.nombre,
                'monto': str(transaccion.monto_destino),
                'divisa_code': transaccion.divisa_destino.code,
                'divisa_nombre': transaccion.divisa_destino.nombre,
                'divisa_simbolo': transaccion.divisa_destino.simbolo,
                'numero_transaccion': transaccion.numero_transaccion,
                'tauser_code': transaccion.tauser_code,
                'cliente_nombre': transaccion.cliente.nombre_completo,
                'desglose': [
                    {
                        'denominacion': str(datos['valor_unitario']),
                        'cantidad': datos['cantidad'],
                        'divisa_simbolo': datos['inventario'].denominacion.divisa.simbolo,
                    }
                    for datos in resultado['desglose'].values()
                ]
            }
            request.session.modified = True
            
            return redirect('tauser_external:retiro_exitoso', terminal_codigo=terminal_codigo)
            
    except Exception as e:
        logger.error(f"Error al procesar retiro en terminal {terminal_codigo}: {e}", exc_info=True)
        messages.error(request, f'❌ Error al procesar el retiro: {str(e)}')
        return redirect('tauser_external:mostrar_detalle_retiro', terminal_codigo=terminal_codigo)


@require_http_methods(["POST"])
def procesar_pago(request, terminal_codigo, transaccion_id):
    """
    Procesa el depósito de divisas en el terminal TAUSER.
    Simula la aceptación de billetes, actualiza inventario y cambia estado de transacción.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    # Verificar que haya MFA validado
    if not request.session.get('transaccion_mfa_verificada'):
        messages.error(request, '❌ Debe verificar su identidad primero.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    # Verificar que la transacción en sesión coincida
    transaccion_sesion_id = request.session.get('transaccion_tauser_id')
    if not transaccion_sesion_id or transaccion_sesion_id != transaccion_id:
        messages.error(request, '❌ Sesión inválida.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    try:
        transaccion = Transaccion.objects.select_related(
            'cliente', 'divisa_origen', 'divisa_destino'
        ).get(id=transaccion_id)
    except Transaccion.DoesNotExist:
        messages.error(request, '❌ Transacción no encontrada.')
        request.session.flush()
        return redirect('tauser_external:home')
    
    # Verificar que sea venta y esté en estado pendiente o pagada
    if transaccion.tipo_operacion != 'venta' or transaccion.estado not in ['pendiente', 'pagada']:
        messages.error(request, '❌ Esta transacción no puede ser procesada.')
        return redirect('tauser_external:menu_tauser', terminal_codigo=terminal_codigo)
    
    # ✅ NUEVO: Obtener datos de billetes seleccionados
    import json
    billetes_data_str = request.POST.get('billetes_data', '{}')
    
    try:
        billetes_data = json.loads(billetes_data_str)
    except json.JSONDecodeError:
        messages.error(request, '❌ Error al procesar los billetes seleccionados.')
        return redirect('tauser_external:mostrar_detalle_deposito', terminal_codigo=terminal_codigo)
    
    # ✅ VALIDAR: Verificar que se ingresó el monto exacto
    from decimal import Decimal
    monto_ingresado = Decimal('0')
    
    for denom_id, info in billetes_data.items():
        valor = Decimal(str(info.get('valor', 0)))
        cantidad = int(info.get('cantidad', 0))
        monto_ingresado += valor * cantidad
    
    if monto_ingresado != transaccion.monto_origen:
        messages.error(
            request,
            f'❌ El monto ingresado ({monto_ingresado} {transaccion.divisa_origen.code}) '
            f'no coincide con el monto requerido ({transaccion.monto_origen} {transaccion.divisa_origen.code}).'
        )
        return redirect('tauser_external:mostrar_detalle_deposito', terminal_codigo=terminal_codigo)
    
    try:
        with transaction.atomic():
            # ✅ Crear movimiento de inventario
            from .models import MovimientoInventarioTerminal, DetalleMovimientoInventario
            movimiento = MovimientoInventarioTerminal.objects.create(
                terminal=terminal,
                tipo_movimiento='DEPOSITO',
                cliente=transaccion.cliente,
                transaccion=transaccion,
                observaciones=f'Depósito de {transaccion.monto_origen} {transaccion.divisa_origen.code}'
            )
            
            # ✅ NUEVO: Actualizar inventario de denominaciones
            for denom_id, info in billetes_data.items():
                cantidad = int(info.get('cantidad', 0))
                
                if cantidad > 0:
                    # Buscar o crear inventario de denominación
                    denominacion = Denominacion.objects.get(id=int(denom_id))
                    inventario_denom, created = InventarioDenominacionTerminal.objects.get_or_create(
                        terminal=terminal,
                        denominacion=denominacion,
                        defaults={'cantidad': 0}
                    )
                    
                    # Guardar cantidad anterior
                    cantidad_anterior = inventario_denom.cantidad
                    
                    # Incrementar cantidad
                    inventario_denom.cantidad += cantidad
                    inventario_denom.save()
                    
                    # Registrar detalle del movimiento
                    DetalleMovimientoInventario.objects.create(
                        movimiento=movimiento,
                        denominacion=denominacion,
                        cantidad=cantidad,
                        cantidad_anterior=cantidad_anterior,
                        cantidad_nueva=inventario_denom.cantidad
                    )
                    
                    logger.info(
                        f"[DEPOSITO] Terminal {terminal.codigo}: "
                        f"Se agregaron {cantidad} billetes de {denominacion.valor} {denominacion.divisa.code}. "
                        f"Stock actual: {inventario_denom.cantidad}"
                    )
            
            # Actualizar inventario general de divisa (opcional, para referencia)
            from tauser.models import InventarioDivisaTerminal
            inventario_general, created = InventarioDivisaTerminal.objects.get_or_create(
                terminal=terminal,
                divisa=transaccion.divisa_origen,
                defaults={'cantidad': Decimal('0')}
            )
            inventario_general.cantidad += transaccion.monto_origen
            inventario_general.save()
            
            # Registrar operación en el terminal
            RegistroTransaccionTerminal.objects.create(
                terminal=terminal,
                transaccion_original=transaccion,
                cliente=transaccion.cliente,
                tipo_operacion='PAGO',
                monto_operacion=transaccion.monto_origen,
                divisa=transaccion.divisa_origen,
                fue_exitoso=True,
                mensaje_error=''
            )
            
            # Cambiar estado de la transacción
            estado_anterior = transaccion.estado
            transaccion.estado = 'completado'
            transaccion.save()
            
            # Registrar en historial
            HistorialTransaccion.objects.create(
                transaccion=transaccion,
                estado_anterior=estado_anterior,
                estado_nuevo='completado',
                observaciones=f'Depósito procesado en terminal {terminal.nombre} (TAUSER)',
                modificado_por=None  # Sistema TAUSER
            )
            
            # Guardar información del depósito exitoso en sesión
            desglose_depositado = []
            for denom_id, info in billetes_data.items():
                cantidad = int(info.get('cantidad', 0))
                valor = info.get('valor', 0)
                if cantidad > 0:
                    desglose_depositado.append({
                        'denominacion': str(valor),
                        'cantidad': cantidad,
                        'divisa_simbolo': transaccion.divisa_origen.simbolo,
                    })
            
            # Limpiar datos de MFA pero mantener info de depósito
            request.session.pop('transaccion_mfa_verificada', None)
            request.session.pop('transaccion_tauser_id', None)
            request.session.pop('terminal_tauser_codigo', None)
            
            request.session['deposito_exitoso'] = {
                'terminal_codigo': terminal_codigo,
                'terminal_nombre': terminal.nombre,
                'monto_depositado': str(transaccion.monto_origen),
                'divisa_depositada_code': transaccion.divisa_origen.code,
                'divisa_depositada_nombre': transaccion.divisa_origen.nombre,
                'divisa_depositada_simbolo': transaccion.divisa_origen.simbolo,
                'monto_recibido': str(transaccion.monto_destino),
                'divisa_recibida_code': transaccion.divisa_destino.code,
                'divisa_recibida_nombre': transaccion.divisa_destino.nombre,
                'divisa_recibida_simbolo': transaccion.divisa_destino.simbolo,
                'numero_transaccion': transaccion.numero_transaccion,
                'tauser_code': transaccion.tauser_code,
                'cliente_nombre': transaccion.cliente.nombre_completo,
                'desglose': desglose_depositado
            }
            request.session.modified = True
            
            return redirect('tauser_external:deposito_exitoso', terminal_codigo=terminal_codigo)
            
    except Exception as e:
        logger.error(f"Error al procesar depósito en terminal {terminal_codigo}: {e}", exc_info=True)
        messages.error(request, f'❌ Error al procesar el depósito: {str(e)}')
        return redirect('tauser_external:mostrar_detalle_deposito', terminal_codigo=terminal_codigo)


# ==================== PANTALLA DE RETIRO EXITOSO ====================

@require_http_methods(["GET"])
def retiro_exitoso(request, terminal_codigo):
    """
    Muestra una pantalla de confirmación después de un retiro exitoso.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    # Obtener información del retiro de la sesión
    retiro_info = request.session.get('retiro_exitoso')
    
    if not retiro_info:
        messages.warning(request, '⚠️ No hay información de retiro disponible.')
        return redirect('tauser_external:home')
    
    # Limpiar la información del retiro de la sesión después de obtenerla
    request.session.pop('retiro_exitoso', None)
    request.session.pop('transaccion_mfa_verificada', None)
    request.session.pop('transaccion_tauser_id', None)
    request.session.modified = True
    
    context = {
        'terminal': terminal,
        'terminal_codigo': terminal_codigo,
        'retiro': retiro_info,
    }
    
    return render(request, 'tauser_external/retiro_exitoso.html', context)


# ==================== PANTALLA DE DEPÓSITO EXITOSO ====================

@require_http_methods(["GET"])
def deposito_exitoso(request, terminal_codigo):
    """
    Muestra una pantalla de confirmación después de un depósito exitoso.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    # Obtener información del depósito de la sesión
    deposito_info = request.session.get('deposito_exitoso')
    
    if not deposito_info:
        messages.warning(request, '⚠️ No hay información de depósito disponible.')
        return redirect('tauser_external:home')
    
    # Limpiar la información del depósito de la sesión después de obtenerla
    request.session.pop('deposito_exitoso', None)
    request.session.modified = True
    
    context = {
        'terminal': terminal,
        'terminal_codigo': terminal_codigo,
        'deposito': deposito_info,
    }
    
    return render(request, 'tauser_external/deposito_exitoso.html', context)


# ==================== CERRAR SESIÓN ====================

def cerrar_sesion_external(request, terminal_codigo):
    """
    Cierra la sesión del TAUSER externo.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
    
    if request.method == 'POST':
        # Limpiar variables de sesión
        request.session.pop('pin_validado_external', None)
        request.session.pop('pin_acceso_id_external', None)
        request.session.pop('cliente_id_external', None)
        request.session.pop('terminal_codigo_external', None)
        request.session.pop('terminal_id_external', None)
        request.session.pop('modo_dev_external', None)
        
        messages.success(request, '✓ Sesión cerrada exitosamente.')
        
        logger.info(f"[TAUSER-EXTERNAL] Sesión cerrada - Terminal: {terminal.codigo}")
        
        return redirect('tauser_external:home')
    
    context = {
        'terminal': terminal,
    }
    
    return render(request, 'tauser_external/cerrar_sesion.html', context)


# ==================== GESTIÓN DE INVENTARIO (PÚBLICA) ====================

def gestion_inventario_denominaciones(request, terminal_pk):
    """
    Vista para gestionar inventario de denominaciones del terminal.
    Versión pública sin restricciones de autenticación (independiente de sesión Global Exchange).
    """
    terminal = get_object_or_404(Terminal, pk=terminal_pk)
    
    # Obtener inventario actual agrupado por divisa
    inventarios = InventarioDenominacionTerminal.objects.filter(
        terminal=terminal
    ).select_related('denominacion__divisa').order_by(
        'denominacion__divisa__code',
        '-denominacion__valor'
    )
    
    # Agrupar por divisa
    inventarios_por_divisa = {}
    totales_globales = {
        'total_billetes': 0,
        'total_alertas': 0,
        'divisas_count': 0
    }
    
    for inv in inventarios:
        divisa_code = inv.denominacion.divisa.code
        if divisa_code not in inventarios_por_divisa:
            inventarios_por_divisa[divisa_code] = {
                'divisa': inv.denominacion.divisa,
                'inventarios': [],
                'valor_total': 0,
                'total_billetes': 0,
                'alertas': 0
            }
            totales_globales['divisas_count'] += 1
        
        inventarios_por_divisa[divisa_code]['inventarios'].append(inv)
        inventarios_por_divisa[divisa_code]['valor_total'] += inv.valor_total
        inventarios_por_divisa[divisa_code]['total_billetes'] += inv.cantidad
        totales_globales['total_billetes'] += inv.cantidad
        
        if inv.necesita_reposicion:
            inventarios_por_divisa[divisa_code]['alertas'] += 1
            totales_globales['total_alertas'] += 1
    
    # Obtener denominaciones NO configuradas (disponibles para agregar)
    denominaciones_configuradas_ids = inventarios.values_list('denominacion_id', flat=True)
    denominaciones_disponibles = Denominacion.objects.filter(
        is_active=True
    ).exclude(
        id__in=denominaciones_configuradas_ids
    ).select_related('divisa').order_by('divisa__code', '-valor')
    
    context = {
        'terminal': terminal,
        'inventario_por_divisa': inventarios_por_divisa,
        'inventario_alertas': [inv for inv in inventarios if inv.necesita_reposicion],
        'denominaciones_disponibles': denominaciones_disponibles,
        'totales_globales': totales_globales,
        'tiene_inventario': inventarios.exists(),
    }
    
    return render(request, 'tauser_external/gestion_inventario_denominaciones.html', context)


# ==================== VISTAS PÚBLICAS DE REABASTECIMIENTO ====================

def dashboard_inventario_externo(request, terminal_codigo):
    """
    Dashboard público de inventario sin requerir autenticación.
    Versión externa del dashboard de reabastecimiento.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
    
    # Inventario actual (excluir PYG)
    inventarios = InventarioDenominacionTerminal.objects.filter(
        terminal=terminal
    ).exclude(
        denominacion__divisa__code='PYG'
    ).select_related('denominacion__divisa').order_by(
        'denominacion__divisa__code',
        '-denominacion__valor'
    )
    
    # Clasificar alertas por criticidad
    alertas_criticas = []  # cantidad == 0 o < 50% del mínimo
    alertas_moderadas = []  # cantidad < cantidad_minima
    inventarios_ok = []  # cantidad >= cantidad_minima
    
    for inv in inventarios:
        # Calcular porcentaje respecto al mínimo (100% = cantidad_minima)
        if inv.cantidad_minima > 0:
            porcentaje = (inv.cantidad / inv.cantidad_minima * 100)
        else:
            porcentaje = 100 if inv.cantidad > 0 else 0
        
        if inv.cantidad == 0 or porcentaje < 50:
            # Sin stock o menos del 50% del mínimo
            alertas_criticas.append({
                'inventario': inv,
                'porcentaje': porcentaje,
                'nivel': 'CRÍTICO',
                'color': 'danger'
            })
        elif porcentaje < 100:
            # Por debajo del mínimo pero no crítico
            alertas_moderadas.append({
                'inventario': inv,
                'porcentaje': porcentaje,
                'nivel': 'ADVERTENCIA',
                'color': 'warning'
            })
        else:
            # Por encima o igual al mínimo
            inventarios_ok.append({
                'inventario': inv,
                'porcentaje': porcentaje,
                'nivel': 'NORMAL',
                'color': 'success'
            })
    
    # Últimas recargas (excluir PYG)
    from .models import LogRecargaInventario
    ultimas_recargas = LogRecargaInventario.objects.filter(
        terminal=terminal
    ).exclude(
        denominacion__divisa__code='PYG'
    ).select_related(
        'denominacion__divisa',
        'usuario'
    ).order_by('-fecha')[:10]
    
    # Estadísticas de recargas (últimos 30 días, excluir PYG)
    desde = timezone.now() - timedelta(days=30)
    recargas_mes = LogRecargaInventario.objects.filter(
        terminal=terminal,
        fecha__gte=desde
    ).exclude(
        denominacion__divisa__code='PYG'
    )
    
    total_recargas = recargas_mes.count()
    valor_total_recargado = sum(r.valor_total_agregado for r in recargas_mes)
    
    # Denominaciones más recargadas
    from django.db.models import Count, Sum
    denominaciones_frecuentes = recargas_mes.values(
        'denominacion__divisa__code',
        'denominacion__valor'
    ).annotate(
        total_recargas=Count('id'),
        total_cantidad=Sum('cantidad_agregada')
    ).order_by('-total_recargas')[:5]
    
    context = {
        'terminal': terminal,
        'alertas_criticas': alertas_criticas,
        'alertas_moderadas': alertas_moderadas,
        'inventarios_ok': inventarios_ok,
        'ultimas_recargas': ultimas_recargas,
        'total_recargas_mes': total_recargas,
        'valor_total_recargado': valor_total_recargado,
        'denominaciones_frecuentes': denominaciones_frecuentes,
        'total_denominaciones': inventarios.count(),
    }
    
    return render(request, 'tauser_external/dashboard_inventario.html', context)


def recarga_masiva_externo(request, terminal_codigo):
    """
    Vista pública para recarga masiva de inventario.
    Muestra TODAS las denominaciones activas del sistema, no solo las que tienen inventario.
    GET: Muestra formulario agrupado por divisa
    POST: Procesa la recarga masiva
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
    
    if request.method == 'GET':
        # Obtener TODAS las denominaciones activas del sistema (excepto PYG)
        denominaciones = Denominacion.objects.filter(
            is_active=True
        ).exclude(
            divisa__code='PYG'  # No permitir recarga de Guaraníes
        ).select_related('divisa').order_by(
            'divisa__code',
            '-valor'
        )
        
        # Obtener inventario existente para mostrar stock actual
        inventarios_existentes = {
            inv.denominacion_id: inv
            for inv in InventarioDenominacionTerminal.objects.filter(
                terminal=terminal
            ).select_related('denominacion')
        }
        
        # Agrupar por divisa y crear/obtener inventarios
        inventarios_por_divisa = {}
        for denominacion in denominaciones:
            divisa_code = denominacion.divisa.code
            
            if divisa_code not in inventarios_por_divisa:
                inventarios_por_divisa[divisa_code] = {
                    'divisa': denominacion.divisa,
                    'inventarios': []
                }
            
            # Si ya existe inventario, usarlo; si no, crear objeto temporal
            if denominacion.id in inventarios_existentes:
                inv = inventarios_existentes[denominacion.id]
            else:
                # Crear inventario temporal (no guardado) para mostrar en el formulario
                inv = InventarioDenominacionTerminal(
                    terminal=terminal,
                    denominacion=denominacion,
                    cantidad=0,
                    cantidad_minima=10  # Default
                )
                # Marcar como nuevo para identificarlo en el template
                inv.es_nuevo = True
            
            inventarios_por_divisa[divisa_code]['inventarios'].append(inv)
        
        context = {
            'terminal': terminal,
            'inventarios_por_divisa': inventarios_por_divisa,
        }
        
        return render(request, 'tauser_external/recarga_masiva.html', context)
    
    # POST: Procesar recarga masiva
    observaciones_generales = request.POST.get('observaciones', '').strip()
    
    recargas_realizadas = []
    errores = []
    
    # Procesar cada denominación
    with transaction.atomic():
        # Crear movimiento de inventario para agrupar todas las recargas
        from .models import MovimientoInventarioTerminal, DetalleMovimientoInventario
        movimiento = MovimientoInventarioTerminal.objects.create(
            terminal=terminal,
            tipo_movimiento='RECARGA',
            observaciones=observaciones_generales or 'Recarga masiva (acceso público)'
        )
        
        for key, value in request.POST.items():
            if key.startswith('cantidad_') and value:
                try:
                    denominacion_id = key.replace('cantidad_', '')
                    cantidad = int(value)
                    
                    if cantidad <= 0:
                        continue  # Saltar si no hay cantidad
                    
                    # Obtener la denominación
                    denominacion = Denominacion.objects.get(id=denominacion_id, is_active=True)
                    
                    # Validar que no sea PYG
                    if denominacion.divisa.code == 'PYG':
                        errores.append(f"No se permite recargar {denominacion.divisa.nombre} (PYG)")
                        continue
                    
                    # Obtener o crear el inventario
                    inventario, created = InventarioDenominacionTerminal.objects.get_or_create(
                        terminal=terminal,
                        denominacion=denominacion,
                        defaults={
                            'cantidad': 0,
                            'cantidad_minima': 10
                        }
                    )
                    
                    # Bloquear para actualización
                    inventario = InventarioDenominacionTerminal.objects.select_for_update().get(id=inventario.id)
                    
                    # Guardar valores anteriores
                    cantidad_anterior = inventario.cantidad
                    
                    # Actualizar cantidad
                    inventario.cantidad += cantidad
                    inventario.ultima_reposicion = timezone.now()
                    inventario.save()
                    
                    # Crear log de recarga (mantener compatibilidad)
                    from .models import LogRecargaInventario
                    log = LogRecargaInventario.objects.create(
                        terminal=terminal,
                        usuario=None,  # Sin usuario (acceso público)
                        denominacion=inventario.denominacion,
                        cantidad_agregada=cantidad,
                        cantidad_anterior=cantidad_anterior,
                        cantidad_nueva=inventario.cantidad,
                        observaciones=observaciones_generales or 'Recarga masiva (acceso público)'
                    )
                    
                    # Registrar detalle del movimiento
                    DetalleMovimientoInventario.objects.create(
                        movimiento=movimiento,
                        denominacion=denominacion,
                        cantidad=cantidad,
                        cantidad_anterior=cantidad_anterior,
                        cantidad_nueva=inventario.cantidad
                    )
                    
                    recargas_realizadas.append({
                        'denominacion': inventario.denominacion,
                        'cantidad': cantidad,
                        'valor_total': log.valor_total_agregado,
                        'creado': created
                    })
                    
                    logger.info(
                        f"[RECARGA MASIVA EXTERNA] Terminal: {terminal.codigo}, "
                        f"Denominación: {inventario.denominacion}, "
                        f"Cantidad: {cantidad}, Creado: {created}"
                    )
                    
                except Denominacion.DoesNotExist:
                    errores.append(f"Denominación ID {denominacion_id} no encontrada")
                except ValueError:
                    errores.append(f"Cantidad inválida para denominación {denominacion_id}")
                except Exception as e:
                    errores.append(f"Error procesando denominación {denominacion_id}: {str(e)}")
                    logger.error(f"[RECARGA MASIVA EXTERNA ERROR] {e}")
    
    # Mensajes de resultado
    if recargas_realizadas:
        total_recargas = len(recargas_realizadas)
        valor_total = sum(r['valor_total'] for r in recargas_realizadas)
        messages.success(
            request,
            f'✓ Se realizaron {total_recargas} recargas exitosamente. Valor total: ${valor_total:,.2f}'
        )
    
    if errores:
        for error in errores:
            messages.error(request, f'❌ {error}')
    
    if not recargas_realizadas and not errores:
        messages.warning(request, '⚠️ No se ingresaron cantidades para recargar')
    
    return redirect('tauser_external:dashboard_inventario', terminal_codigo=terminal_codigo)


def historial_recargas_externo(request, terminal_codigo):
    """
    Vista pública del historial completo de movimientos de inventario (recargas, depósitos, extracciones).
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
    
    from .models import MovimientoInventarioTerminal
    
    # Obtener todos los movimientos
    movimientos = MovimientoInventarioTerminal.objects.filter(
        terminal=terminal
    ).select_related(
        'cliente',
        'transaccion',
        'usuario'
    ).prefetch_related(
        'detalles__denominacion__divisa'
    ).order_by('-fecha')
    
    # Filtros opcionales
    tipo_filtro = request.GET.get('tipo')
    divisa_filtro = request.GET.get('divisa')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if tipo_filtro:
        movimientos = movimientos.filter(tipo_movimiento=tipo_filtro)
    
    if divisa_filtro:
        movimientos = movimientos.filter(detalles__denominacion__divisa__code=divisa_filtro).distinct()
    
    if fecha_desde:
        from datetime import datetime
        movimientos = movimientos.filter(fecha__date__gte=datetime.strptime(fecha_desde, '%Y-%m-%d').date())
    
    if fecha_hasta:
        from datetime import datetime
        movimientos = movimientos.filter(fecha__date__lte=datetime.strptime(fecha_hasta, '%Y-%m-%d').date())
    
    # Estadísticas del período filtrado
    from django.db.models import Sum, Count
    estadisticas = {
        'total_movimientos': movimientos.count(),
        'total_recargas': movimientos.filter(tipo_movimiento='RECARGA').count(),
        'total_depositos': movimientos.filter(tipo_movimiento='DEPOSITO').count(),
        'total_extracciones': movimientos.filter(tipo_movimiento='EXTRACCION').count(),
    }
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(movimientos, 25)  # 25 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener listas para filtros
    from .models import DetalleMovimientoInventario
    divisas_disponibles = DetalleMovimientoInventario.objects.filter(
        movimiento__terminal=terminal
    ).exclude(
        denominacion__divisa__code='PYG'
    ).values_list('denominacion__divisa__code', flat=True).distinct()
    
    context = {
        'terminal': terminal,
        'page_obj': page_obj,
        'estadisticas': estadisticas,
        'divisas_disponibles': divisas_disponibles,
        # Mantener valores de filtros
        'tipo_filtro': tipo_filtro,
        'divisa_filtro': divisa_filtro,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        # Opciones de tipo de movimiento
        'tipos_movimiento': MovimientoInventarioTerminal.TIPO_MOVIMIENTO_CHOICES,
    }
    
    return render(request, 'tauser_external/historial_recargas.html', context)


def detalle_movimiento_inventario(request, terminal_codigo, movimiento_id):
    """
    Vista de detalle de un movimiento de inventario específico.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
    
    from .models import MovimientoInventarioTerminal
    movimiento = get_object_or_404(
        MovimientoInventarioTerminal.objects.select_related(
            'terminal',
            'cliente',
            'transaccion',
            'usuario'
        ).prefetch_related(
            'detalles__denominacion__divisa'
        ),
        id=movimiento_id,
        terminal=terminal
    )
    
    context = {
        'terminal': terminal,
        'movimiento': movimiento,
    }
    
    return render(request, 'tauser_external/detalle_movimiento.html', context)
