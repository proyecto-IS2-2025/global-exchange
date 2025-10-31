from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.db import models
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.crypto import get_random_string
import logging
from django.views.decorators.http import require_http_methods

from .models import (
    Terminal, 
    InventarioDivisaTerminal,
    InventarioDenominacionTerminal,  # ✅ NUEVO
    DesgloseDenominacionOperacion,    # ✅ NUEVO
    RegistroTransaccionTerminal,
    PINTerminalCliente
)
from .forms import TerminalForm, InventarioDivisaTerminalForm
from transacciones.models import Transaccion, HistorialTransaccion
from clientes.models import Cliente
from divisas.models import Denominacion, Divisa, DesgloseDenominacion
from .services import (  # ✅ NUEVO
    calcular_desglose_optimo,
    validar_desglose_cliente,
    generar_resumen_desglose
)

# ==================== VISTAS ADMINISTRATIVAS ADICIONALES ====================
from .views_admin_denominaciones import (
    GestionInventarioDenominacionesView,
    AgregarDenominacionInventarioView,
    AjustarInventarioDenominacionAdminView,
    EliminarInventarioDenominacionView,
    DashboardInventarioView,
    RecargaMasivaView,
    HistorialRecargasView
)

logger = logging.getLogger(__name__)


# ==================== PÁGINA PRINCIPAL EXTERNA ====================

def tauser_home(request):
    """
    Vista principal externa de /tauser/ que muestra todos los tausers
    activos como tarjetas con su stock.
    NO requiere autenticación.
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
    
    context = {
        'terminales_con_stock': terminales_con_stock,
        'titulo': 'Terminales TAUSER'
    }
    
    return render(request, 'tauser_external/home.html', context)


def menu_cliente_tauser(request, terminal_codigo):
    """
    Menú donde el cliente ingresa el código tauser de su transacción.
    NO requiere autenticación.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    context = {
        'terminal': terminal,
        'titulo': f'Terminal {terminal.nombre}'
    }
    
    return render(request, 'tauser_external/menu_cliente.html', context)


# ==================== HELPERS ====================

def es_cliente(user):
    """Verifica si el usuario pertenece al grupo 'cliente'"""
    return user.is_authenticated and user.groups.filter(name='cliente').exists()


# ==================== TERMINAL DE AUTOSERVICIO (CLIENTE) ====================

@login_required
@user_passes_test(es_cliente, login_url='inicio')
def lista_terminales(request):
    """
    Vista para mostrar la lista de terminales activos disponibles.
    Solo accesible para usuarios del grupo 'cliente'.
    """
    terminales = Terminal.objects.filter(is_activa=True).order_by('nombre')
    
    context = {
        'terminales': terminales,
        'titulo': 'Seleccionar Terminal TAUSER'
    }
    
    return render(request, 'teminal_list_cliente.html', context)


@login_required
@user_passes_test(es_cliente, login_url='inicio')
def seleccionar_terminal(request, terminal_codigo):
    """
    Vista intermedia que guarda el terminal en sesión y redirige al PIN.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    # Guardar información del terminal en la sesión
    request.session['terminal_codigo'] = terminal.codigo
    request.session['terminal_nombre'] = terminal.nombre
    request.session['terminal_ubicacion'] = terminal.ubicacion
    
    # Mensaje de bienvenida
    messages.info(
        request, 
        f'Terminal seleccionado: {terminal.nombre}. Por favor ingrese su PIN.'
    )
    
    # Redirigir a la pantalla de ingreso de PIN
    return redirect('tauser:inicio_tauser', terminal_codigo=terminal.codigo)


@login_required
@require_http_methods(["GET", "POST"])
def inicio_tauser(request, terminal_codigo):
    """
    Vista principal del terminal TAUSER donde se ingresa el PIN.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    if request.method == 'POST':
        pin_ingresado = request.POST.get('pin_ingresado', '').strip()
        
        if not pin_ingresado:
            messages.error(request, 'Por favor ingrese su PIN.')
            return render(request, 'inicio_tauser.html', {'terminal': terminal})
        
        # ==================== PIN MAESTRO PARA DESARROLLADORES ====================
        if pin_ingresado == '000000':
            # Verificar que el usuario sea staff o superuser
            #if request.user.is_staff or request.user.is_superuser:
                # Buscar el primer cliente activo para simular acceso
                try:
                    cliente_dev = Cliente.objects.filter(esta_activo=True).first()
                    
                    if not cliente_dev:
                        messages.error(request, 'No hay clientes activos en el sistema.')
                        return render(request, 'inicio_tauser.html', {'terminal': terminal})
                    
                    # Guardar información en la sesión
                    request.session['pin_validado'] = True
                    request.session['pin_acceso_id'] = None  # No hay PIN real
                    request.session['cliente_id'] = cliente_dev.id
                    request.session['terminal_id'] = terminal.id
                    request.session['modo_dev'] = True  # Marcar como modo desarrollo
                    
                    messages.warning(
                        request, 
                        f'⚠️ ACCESO DE DESARROLLO - Cliente: {cliente_dev.nombre_completo}'
                    )
                    
                    logger.warning(
                        f"[DEV MODE] Acceso con PIN maestro - Terminal: {terminal.codigo}, "
                        f"Usuario: {request.user.username}, Cliente simulado: {cliente_dev.nombre_completo}"
                    )
                    
                    # Registrar acceso de desarrollo
                    RegistroTransaccionTerminal.objects.create(
                        terminal=terminal,
                        cliente=cliente_dev,
                        tipo_operacion='CONSULTA',
                        fue_exitoso=True,
                        mensaje_error='[DEV MODE] Acceso con PIN maestro 000000'
                    )
                    
                    # Redirigir al menú principal
                    return redirect('tauser:menu_principal', terminal_codigo=terminal.codigo)
                    
                except Exception as e:
                    logger.error(f"Error en acceso con PIN maestro: {e}")
                    messages.error(request, 'Error al acceder con PIN maestro.')
                    return render(request, 'inicio_tauser.html', {'terminal': terminal})
            #else:
                # Usuario no autorizado para usar PIN maestro
             #   messages.error(
              #      request, 
               #     'PIN inválido. Solo personal autorizado puede usar este PIN.'
                #)
                #logger.warning(
                #    f"Intento de uso de PIN maestro por usuario no autorizado: {request.user.username}"
                #)
                #return render(request, 'inicio_tauser.html', {'terminal': terminal})
        
        # ==================== VALIDACIÓN NORMAL DE PIN ====================
        try:
            # Buscar PIN válido usando PINTerminalCliente
            pin_acceso = PINTerminalCliente.objects.select_related('cliente').get(
                pin=pin_ingresado,
                usado=False,
                fecha_expiracion__gt=timezone.now()
            )
            
            # Marcar el PIN como usado
            pin_acceso.usado = True
            pin_acceso.fecha_uso = timezone.now()
            pin_acceso.save()
            
            # Guardar información en la sesión
            request.session['pin_validado'] = True
            request.session['pin_acceso_id'] = pin_acceso.id
            request.session['cliente_id'] = pin_acceso.cliente.id
            request.session['terminal_id'] = terminal.id
            request.session['modo_dev'] = False
            
            messages.success(
                request, 
                f'¡Bienvenido {pin_acceso.cliente.nombre_completo}! Acceso autorizado al terminal {terminal.nombre}'
            )
            
            logger.info(
                f"Acceso exitoso - Terminal: {terminal.codigo}, "
                f"Cliente: {pin_acceso.cliente.nombre_completo}, PIN: {pin_ingresado}"
            )
            
            # Registrar acceso exitoso
            RegistroTransaccionTerminal.objects.create(
                terminal=terminal,
                cliente=pin_acceso.cliente,
                tipo_operacion='CONSULTA',
                fue_exitoso=True,
                pin_usado=pin_acceso
            )
            
            # Redirigir al menú principal del TAUSER
            return redirect('tauser:menu_principal', terminal_codigo=terminal.codigo)
            
        except PINTerminalCliente.DoesNotExist:
            messages.error(
                request, 
                'PIN inválido, expirado o ya utilizado. Por favor verifique e intente nuevamente.'
            )
            
            logger.warning(
                f"Intento de acceso fallido - Terminal: {terminal.codigo}, PIN: {pin_ingresado}"
            )
            
            # Registrar intento fallido
            RegistroTransaccionTerminal.objects.create(
                terminal=terminal,
                cliente=None,
                tipo_operacion='CONSULTA',
                fue_exitoso=False,
                mensaje_error=f"PIN inválido: {pin_ingresado}"
            )
            
            return render(request, 'inicio_tauser.html', {'terminal': terminal})
    
    # GET request
    return render(request, 'inicio_tauser.html', {'terminal': terminal})

@login_required
def menu_principal(request, terminal_codigo):
    """
    Vista del menú principal después de validar el PIN.
    Muestra las transacciones pendientes del cliente.
    """
    # Verificar que el PIN esté validado
    if not request.session.get('pin_validado'):
        messages.warning(request, 'Debe ingresar un PIN válido primero.')
        return redirect('tauser:inicio_tauser', terminal_codigo=terminal_codigo)
    
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    # Obtener información del cliente desde la sesión
    cliente_id = request.session.get('cliente_id')
    cliente = None
    
    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            messages.error(request, 'Cliente no encontrado.')
            return redirect('tauser:inicio_tauser', terminal_codigo=terminal_codigo)
    
    # ==================== OBTENER TRANSACCIONES ====================
    
    # RETIRO: Cliente compró divisa extranjera y debe retirarla
    # ✅ Solo transacciones PAGADAS (ya pagó, falta retirar la divisa)
    transacciones_retiro = Transaccion.objects.filter(
        cliente=cliente,
        tipo_operacion='compra',
        estado='pagada'
    ).exclude(
        divisa_destino__code='PYG'
    ).select_related('divisa_origen', 'divisa_destino').order_by('-fecha_creacion')
    
    # PAGO: Cliente vendió divisa y debe recibir el pago en guaraníes
    # ✅ Solo transacciones PENDIENTES (se completan por transferencia automática)
    transacciones_pago = Transaccion.objects.filter(
        cliente=cliente,
        tipo_operacion='venta',
        estado='pendiente',
        divisa_destino__code='PYG'
    ).select_related('divisa_origen', 'divisa_destino').order_by('-fecha_creacion')
    
    # Verificar disponibilidad con denominaciones para RETIROS
    transacciones_retiro_disponibles = []
    for trans in transacciones_retiro:
        # Verificar si hay denominaciones suficientes
        tiene_denominaciones, desglose_sugerido = terminal.tiene_denominaciones_suficientes(
            trans.divisa_destino,
            trans.monto_destino
        )
        
        transacciones_retiro_disponibles.append({
            'transaccion': trans,
            'disponible': tiene_denominaciones,
            'desglose_sugerido': desglose_sugerido
        })
    
    # ✅ Para PAGOS (PYG), siempre están disponibles (transferencia digital)
    transacciones_pago_verificadas = []
    for trans in transacciones_pago:
        transacciones_pago_verificadas.append({
            'transaccion': trans,
            'disponible': True  # ✅ Siempre disponible (transferencia digital)
        })
    
    # Registrar consulta
    pin_usado_id = request.session.get('pin_acceso_id')
    pin_usado = None
    if pin_usado_id:
        try:
            pin_usado = PINTerminalCliente.objects.get(id=pin_usado_id)
        except PINTerminalCliente.DoesNotExist:
            pass
    
    RegistroTransaccionTerminal.objects.create(
        terminal=terminal,
        cliente=cliente,
        tipo_operacion='CONSULTA',
        fue_exitoso=True,
        pin_usado=pin_usado,
        mensaje_error='Consulta de transacciones pendientes'
    )
    
    # Contexto para el template
    context = {
        'terminal': terminal,
        'cliente': cliente,
        'cliente_id': cliente_id,
        'now': timezone.now(),
        'transacciones_retiro': transacciones_retiro_disponibles,
        'transacciones_pago': transacciones_pago_verificadas,
        'total_retiros': len(transacciones_retiro_disponibles),
        'total_pagos': len(transacciones_pago_verificadas),
        'efectivo_disponible': None,  # ✅ Ya no es relevante
        'pago_digital': True,  # ✅ Indicador para el template
    }
    
    return render(request, 'transacciones_cliente.html', context)

@login_required
def cerrar_sesion_tauser(request, terminal_codigo):
    """
    Cierra la sesión del TAUSER y limpia la sesión.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    
    # Obtener información del cliente antes de limpiar la sesión
    cliente_id = request.session.get('cliente_id')
    cliente = None
    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            pass
    
    if request.method == 'POST':
        # Registrar cierre de sesión
        if cliente:
            pin_usado_id = request.session.get('pin_acceso_id')
            pin_usado = None
            if pin_usado_id:
                try:
                    pin_usado = PINTerminalCliente.objects.get(id=pin_usado_id)
                except PINTerminalCliente.DoesNotExist:
                    pass
            
            RegistroTransaccionTerminal.objects.create(
                terminal=terminal,
                cliente=cliente,
                tipo_operacion='CIERRE_SESION',
                fue_exitoso=True,
                pin_usado=pin_usado,
                mensaje_error='Sesión cerrada por el usuario'
            )
            
            logger.info(
                f"Sesión cerrada - Terminal: {terminal.codigo}, "
                f"Cliente: {cliente.nombre_completo}"
            )
        
        # Limpiar variables de sesión relacionadas con TAUSER
        request.session.pop('pin_validado', None)
        request.session.pop('pin_acceso_id', None)
        request.session.pop('cliente_id', None)
        request.session.pop('terminal_codigo', None)
        request.session.pop('terminal_nombre', None)
        request.session.pop('terminal_ubicacion', None)
        request.session.pop('terminal_id', None)
        request.session.pop('modo_dev', None)
        
        messages.success(request, '✓ Sesión cerrada exitosamente. ¡Gracias por usar nuestros servicios!')
        
        return redirect('tauser:lista_terminales')
    
    # GET request - mostrar página de confirmación
    context = {
        'terminal': terminal,
        'cliente': cliente,
        'now': timezone.now()
    }
    
    return render(request, 'cerrar_sesion.html', context)

 
@login_required
def seleccionar_denominaciones_retiro(request, terminal_codigo, transaccion_id):
    """
    Permite al cliente ver y confirmar el desglose de denominaciones para un retiro.
    """
    if not request.session.get('pin_validado'):
        messages.warning(request, 'Debe ingresar un PIN válido primero.')
        return redirect('tauser:inicio_tauser', terminal_codigo=terminal_codigo)
    
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    transaccion = get_object_or_404(Transaccion, id=transaccion_id)
    
    # Verificar cliente
    cliente_sesion = request.session.get('cliente_id')
    if str(cliente_sesion) != str(transaccion.cliente.id):
        messages.error(request, "Acceso no autorizado.")
        return redirect('tauser:inicio_tauser', terminal_codigo=terminal_codigo)
    
    divisa = transaccion.divisa_destino
    monto = transaccion.monto_destino
    
    # Obtener inventario de denominaciones disponibles
    inventarios = InventarioDenominacionTerminal.objects.filter(
        terminal=terminal,
        denominacion__divisa=divisa,
        denominacion__is_active=True,
        cantidad__gt=0
    ).select_related('denominacion').order_by('-denominacion__valor')
    
    # Calcular desglose óptimo
    resultado = calcular_desglose_optimo(inventarios, monto)
    
    if not resultado['posible']:
        messages.error(
            request,
            f"No hay suficientes billetes para entregar {monto} {divisa.code}. "
            f"Por favor contacte al personal."
        )
        return redirect('tauser:menu_principal', terminal_codigo=terminal_codigo)
    
    # Generar resumen legible
    resumen_desglose = generar_resumen_desglose(resultado['desglose'])
    
    context = {
        'terminal': terminal,
        'transaccion': transaccion,
        'divisa': divisa,
        'monto': monto,
        'desglose': resultado['desglose'],
        'resumen_desglose': resumen_desglose,
        'total_billetes': sum(d['cantidad'] for d in resultado['desglose'].values()),
    }
    
    return render(request, 'denominaciones/seleccionar_denominaciones_retiro.html', context)


@login_required
def seleccionar_denominaciones_venta(request, terminal_codigo, transaccion_id):
    """
    Permite al cliente ingresar las denominaciones que está entregando en una venta.
    """
    if not request.session.get('pin_validado'):
        messages.warning(request, 'Debe ingresar un PIN válido primero.')
        return redirect('tauser:inicio_tauser', terminal_codigo=terminal_codigo)
    
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    transaccion = get_object_or_404(Transaccion, id=transaccion_id)
    
    # Verificar cliente
    cliente_sesion = request.session.get('cliente_id')
    if str(cliente_sesion) != str(transaccion.cliente.id):
        messages.error(request, "Acceso no autorizado.")
        return redirect('tauser:inicio_tauser', terminal_codigo=terminal_codigo)
    
    divisa = transaccion.divisa_origen  # La divisa que el cliente ENTREGA
    monto = transaccion.monto_origen
    
    # Obtener todas las denominaciones activas de esta divisa
    denominaciones = Denominacion.objects.filter(
        divisa=divisa,
        is_active=True
    ).order_by('-valor')
    
    if request.method == 'POST':
        # Validar desglose ingresado
        desglose_cliente = {}
        for denom in denominaciones:
            cantidad_key = f'denominacion_{denom.id}'
            cantidad = request.POST.get(cantidad_key, 0)
            
            try:
                cantidad = int(cantidad)
                if cantidad > 0:
                    desglose_cliente[denom.id] = cantidad
            except ValueError:
                continue
        
        # Validar que sume el monto correcto
        es_valido, mensaje, monto_calc = validar_desglose_cliente(desglose_cliente, monto)
        
        if not es_valido:
            messages.error(request, mensaje)
        else:
            # Guardar en sesión y redirigir a confirmación
            request.session[f'desglose_venta_{transaccion_id}'] = desglose_cliente
            return redirect(
                'tauser:confirmar_denominaciones_venta',
                terminal_codigo=terminal_codigo,
                transaccion_id=transaccion_id
            )
    
    context = {
        'terminal': terminal,
        'transaccion': transaccion,
        'divisa': divisa,
        'monto': monto,
        'denominaciones': denominaciones,
    }
    
    return render(request, 'denominaciones/seleccionar_denominaciones_venta.html', context)


@login_required
def confirmar_denominaciones_venta(request, terminal_codigo, transaccion_id):
    """
    Muestra resumen y confirma el desglose de denominaciones ingresado.
    """
    if not request.session.get('pin_validado'):
        messages.warning(request, 'Debe ingresar un PIN válido primero.')
        return redirect('tauser:inicio_tauser', terminal_codigo=terminal_codigo)
    
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
    transaccion = get_object_or_404(Transaccion, id=transaccion_id)
    
    # Obtener desglose de sesión
    desglose_key = f'desglose_venta_{transaccion_id}'
    desglose_cliente = request.session.get(desglose_key)
    
    if not desglose_cliente:
        messages.error(request, 'Desglose no encontrado. Intente nuevamente.')
        return redirect(
            'tauser:seleccionar_denominaciones_venta',
            terminal_codigo=terminal_codigo,
            transaccion_id=transaccion_id
        )
    
    # Generar resumen
    resumen = []
    total = Decimal('0')
    
    for denom_id, cantidad in desglose_cliente.items():
        denominacion = Denominacion.objects.get(id=denom_id)
        subtotal = denominacion.valor * cantidad
        total += subtotal
        
        resumen.append({
            'denominacion': denominacion,
            'cantidad': cantidad,
            'subtotal': subtotal,
        })
    
    if request.method == 'POST':
        # Procesar operación
        # Limpiar sesión
        del request.session[desglose_key]
        
        # Redirigir a ejecutar operación con desglose
        return redirect(
            'tauser:ejecutar_operacion',
            terminal_codigo=terminal_codigo,
            transaccion_id=transaccion.id
        )
    
    context = {
        'terminal': terminal,
        'transaccion': transaccion,
        'resumen': resumen,
        'total': total,
        'total_billetes': sum(desglose_cliente.values()),
    }
    
    return render(request, 'denominaciones/confirmar_denominaciones_venta.html', context)

# ==================== OPERACIONES EN TERMINAL ====================

class TransaccionesClienteView(View):
    """Muestra las transacciones pendientes del cliente"""
    template_name = 'transacciones_cliente.html'

    def get(self, request, terminal_codigo, cliente_id):
        # Verificar sesión validada
        if not request.session.get('pin_validado'):
            messages.warning(request, 'Debe ingresar un PIN válido primero.')
            return redirect('tauser:inicio_tauser', terminal_codigo=terminal_codigo)
        
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
        cliente = get_object_or_404(Cliente, pk=cliente_id, esta_activo=True)
        
        # Verificar que el cliente en sesión coincida
        cliente_sesion = request.session.get('cliente_id')
        if str(cliente_sesion) != str(cliente_id):
            messages.error(request, "Acceso no autorizado.")
            return redirect('tauser:inicio_tauser', terminal_codigo=terminal_codigo)
        
        # Obtener transacciones pendientes
        # RETIRO: Cliente compró divisa extranjera y debe retirarla
        transacciones_retiro = Transaccion.objects.filter(
            cliente=cliente,
            tipo_operacion='compra',
            estado='pagada'  # Ya pagó, falta que retire la divisa
        ).exclude(
            divisa_destino__code='PYG'  # Excluir guaraníes
        ).select_related('divisa_origen', 'divisa_destino').order_by('-fecha_creacion')
        
        # PAGO: Cliente vendió divisa y debe recibir el pago en guaraníes
        transacciones_pago = Transaccion.objects.filter(
            cliente=cliente,
            tipo_operacion='venta',
            estado='pendiente',  # Transacción pendiente
            divisa_destino__code='PYG'  # Debe recibir guaraníes
        ).select_related('divisa_origen', 'divisa_destino').order_by('-fecha_creacion')
        
        # Verificar disponibilidad en terminal
        transacciones_retiro_disponibles = []
        for trans in transacciones_retiro:
            disponible = terminal.tiene_inventario_suficiente(
                trans.divisa_destino, 
                trans.monto_destino
            )
            transacciones_retiro_disponibles.append({
                'transaccion': trans,
                'disponible': disponible
            })
        
        context = {
            'terminal': terminal,
            'cliente': cliente,
            'transacciones_retiro': transacciones_retiro_disponibles,
            'transacciones_pago': transacciones_pago,
        }
        
        # Registrar consulta
        pin_usado_id = request.session.get('pin_acceso_id')
        pin_usado = None
        if pin_usado_id:
            try:
                pin_usado = PINTerminalCliente.objects.get(id=pin_usado_id)
            except PINTerminalCliente.DoesNotExist:
                pass
        
        RegistroTransaccionTerminal.objects.create(
            terminal=terminal,
            cliente=cliente,
            tipo_operacion='CONSULTA',
            fue_exitoso=True,
            pin_usado=pin_usado
        )
        
        return render(request, self.template_name, context)


class EjecutarOperacionView(View):
    """Procesa el retiro o pago de una transacción"""

    def post(self, request, terminal_codigo, transaccion_id):
        # Verificar sesión validada
        if not request.session.get('pin_validado'):
            messages.warning(request, 'Debe ingresar un PIN válido primero.')
            return redirect('tauser:inicio_tauser', terminal_codigo=terminal_codigo)
        
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
        transaccion = get_object_or_404(
            Transaccion.objects.select_related('cliente', 'divisa_origen', 'divisa_destino'),
            numero_transaccion=transaccion_id
        )
        tipo_operacion = request.POST.get('tipo_operacion')
        # ✅ NUEVO: Obtener desglose de denominaciones si viene del formulario
        desglose_denominaciones = self._extraer_desglose_post(request.POST)
        
        # Verificar que el cliente en sesión coincida
        cliente_sesion = request.session.get('cliente_id')
        if str(cliente_sesion) != str(transaccion.cliente.id):
            messages.error(request, "Acceso no autorizado.")
            return redirect('tauser:inicio_tauser', terminal_codigo=terminal_codigo)
        
        tipo_operacion = request.POST.get('tipo_operacion')
        
        # Obtener PIN usado
        pin_usado_id = request.session.get('pin_acceso_id')
        pin_usado = None
        if pin_usado_id:
            try:
                pin_usado = PINTerminalCliente.objects.get(id=pin_usado_id)
            except PINTerminalCliente.DoesNotExist:
                pass
        
        try:
            with transaction.atomic():
                if tipo_operacion == 'RETIRO':
                    # ✅ MODIFICADO: Pasar desglose
                    registro = self._procesar_retiro(
                        terminal, transaccion, request, pin_usado, desglose_denominaciones
                    )
                    messages.success(
                        request,
                        f"✓ Retiro exitoso de {transaccion.monto_destino} "
                        f"{transaccion.divisa_destino.code}. Retire los billetes del dispensador."
                    )
                    
                elif tipo_operacion == 'PAGO':
                    # Para ventas: cliente ENTREGA divisas, recibe PYG digitalmente
                    registro = self._procesar_pago(
                        terminal, transaccion, request, pin_usado, desglose_denominaciones
                    )
                    messages.success(
                        request,
                        f"✓ Pago digital de ₲{transaccion.monto_destino:,.0f} realizado. "
                        f"Deposite los billetes en el receptor."
                    )
                    
                else:
                    raise ValueError("Tipo de operación inválido")
                
        except ValueError as e:
            messages.error(request, str(e))
            logger.error(f"Error en operación {tipo_operacion}: {e}")
            
            # Registrar operación fallida
            RegistroTransaccionTerminal.objects.create(
                terminal=terminal,
                transaccion_original=transaccion,
                cliente=transaccion.cliente,
                tipo_operacion=tipo_operacion,
                divisa=transaccion.divisa_destino if tipo_operacion == 'RETIRO' else transaccion.divisa_origen,
                monto_operacion=transaccion.monto_destino if tipo_operacion == 'RETIRO' else transaccion.monto_origen,
                fue_exitoso=False,
                mensaje_error=str(e),
                pin_usado=pin_usado
            )
        
        return redirect('tauser:transacciones_cliente', 
                       terminal_codigo=terminal_codigo, 
                       cliente_id=transaccion.cliente.id)
    
    def _procesar_retiro(self, terminal, transaccion, request, pin_usado, desglose_cliente=None):
        """Procesa el retiro de divisa extranjera"""
        if transaccion.tipo_operacion != 'compra':
            raise ValueError("Esta transacción no es una compra.")
        
        if transaccion.estado != 'pagada':
            raise ValueError("Esta transacción no está lista para retiro.")
        
        divisa_a_retirar = transaccion.divisa_destino
        monto_a_retirar = transaccion.monto_destino
        
        # ✅ NUEVO: Si no viene desglose del cliente, calcularlo automáticamente
        if not desglose_cliente:
            inventarios = InventarioDenominacionTerminal.objects.filter(
                terminal=terminal,
                denominacion__divisa=divisa_a_retirar,
                denominacion__is_active=True,
                cantidad__gt=0
            ).select_related('denominacion')
            
            resultado_desglose = calcular_desglose_optimo(inventarios, monto_a_retirar)
            
            if not resultado_desglose['posible']:
                raise ValueError(
                    f"No hay denominaciones suficientes para entregar "
                    f"{monto_a_retirar} {divisa_a_retirar.code}. "
                    f"Faltante: {resultado_desglose['sobrante']}"
                )
            
            desglose_a_usar = resultado_desglose['desglose']
        else:
            # Validar desglose del cliente
            es_valido, mensaje, monto_calc = validar_desglose_cliente(
                desglose_cliente,
                monto_a_retirar
            )
            
            if not es_valido:
                raise ValueError(mensaje)
            
            # Convertir desglose_cliente a formato esperado
            desglose_a_usar = {}
            for denom_id, cantidad in desglose_cliente.items():
                try:
                    inventario = InventarioDenominacionTerminal.objects.select_for_update().get(
                        terminal=terminal,
                        denominacion_id=denom_id
                    )
                    
                    if inventario.cantidad < cantidad:
                        raise ValueError(
                            f"Inventario insuficiente de {inventario.denominacion}. "
                            f"Disponible: {inventario.cantidad}, Solicitado: {cantidad}"
                        )
                    desglose_a_usar[inventario.id] = {
                        'inventario': inventario,
                        'cantidad': cantidad,
                        'valor_unitario': inventario.denominacion.valor,
                        'subtotal': inventario.denominacion.valor * cantidad
                    }
                    
                except InventarioDenominacionTerminal.DoesNotExist:
                    raise ValueError(f"Denominación no disponible en este terminal: {denom_id}")
        
        # ✅ Descontar denominaciones del inventario
        for datos in desglose_a_usar.values():
            inventario = datos['inventario']
            cantidad = datos['cantidad']
            
            inventario.descontar(cantidad)
            inventario.actualizado_por = request.user if request.user.is_authenticated else None
            inventario.save()
        
        # Actualizar inventario general de divisa (backward compatibility)
        try:
            inventario_divisa = InventarioDivisaTerminal.objects.get(
                terminal=terminal,
                divisa=divisa_a_retirar
            )
            inventario_divisa.cantidad -= monto_a_retirar
            inventario_divisa.save()
        except InventarioDivisaTerminal.DoesNotExist:
            pass
        
        # Actualizar estado de transacción
        transaccion.estado = 'completado'
        transaccion.save()

        # Registrar en historial de transacción
        HistorialTransaccion.objects.create(
            transaccion=transaccion,
            estado_anterior='pagada',
            estado_nuevo='completado',
        )
        
        # ✅ Guardar desglose en DesgloseDenominacion (para la transacción)
        for datos in desglose_a_usar.values():
            DesgloseDenominacion.objects.create(
                transaccion=transaccion,
                denominacion=datos['inventario'].denominacion,
                cantidad=datos['cantidad']
            )
        
        # Registrar operación en terminal
        registro = RegistroTransaccionTerminal.objects.create(
            terminal=terminal,
            transaccion_original=transaccion,
            cliente=transaccion.cliente,
            tipo_operacion='RETIRO',
            divisa=divisa_a_retirar,
            monto_operacion=monto_a_retirar,
            fue_exitoso=True,
            pin_usado=pin_usado
        )

        # ✅ Guardar desglose de operación terminal
        for datos in desglose_a_usar.values():
            DesgloseDenominacionOperacion.objects.create(
                registro_operacion=registro,
                denominacion=datos['inventario'].denominacion,
                cantidad=datos['cantidad'],
                tipo_movimiento='ENTREGA'
            )
        
        logger.info(
            f"Retiro completado con denominaciones - Terminal: {terminal.nombre}, "
            f"Cliente: {transaccion.cliente.nombre_completo}, "
            f"Monto: {monto_a_retirar} {divisa_a_retirar.code}, "
            f"Billetes: {sum(d['cantidad'] for d in desglose_a_usar.values())}"
        )
        
        return registro
    
    def _procesar_pago(self, terminal, transaccion, request, pin_usado, desglose_cliente=None):
        """
        Procesa el pago en guaraníes por venta de divisa.
        ✅ NUEVO: No verifica inventario físico porque se paga por transferencia digital.
        """
        if transaccion.tipo_operacion != 'venta':
            raise ValueError("Esta transacción no es una venta.")
        
        if transaccion.estado != 'pendiente':
            raise ValueError("Esta transacción no está lista para pago.")
        
        divisa_origen = transaccion.divisa_origen  # Divisa que entrega el cliente (USD, EUR, etc.)
        monto_origen = transaccion.monto_origen
        divisa_pago = transaccion.divisa_destino  # Debe ser PYG
        monto_pago = transaccion.monto_destino
        
        # ✅ VALIDAR: El desglose debe ser de la divisa origen (lo que entrega)
        if not desglose_cliente:
            raise ValueError(
                f"Debe especificar las denominaciones de {divisa_origen.code} que está entregando"
            )
        
        # Validar que el desglose sume el monto correcto
        es_valido, mensaje, monto_calc = validar_desglose_cliente(
            desglose_cliente,
            monto_origen
        )
        
        if not es_valido:
            raise ValueError(mensaje)
        
        # ✅ AGREGAR denominaciones al inventario del terminal
        for denom_id, cantidad in desglose_cliente.items():
            denominacion = Denominacion.objects.get(id=denom_id, is_active=True)
            # Verificar que sea de la divisa correcta
            if denominacion.divisa != divisa_origen:
                raise ValueError(
                    f"Denominación incorrecta: esperada {divisa_origen.code}, "
                    f"recibida {denominacion.divisa.code}"
                )
            
            # Obtener o crear inventario de denominación
            inventario, created = InventarioDenominacionTerminal.objects.get_or_create(
                terminal=terminal,
                denominacion=denominacion,
                defaults={'cantidad': 0}
            )
            
            # Agregar al inventario
            inventario.agregar(cantidad)
            inventario.actualizado_por = request.user if request.user.is_authenticated else None
            inventario.save()
            
         # Actualizar inventario general de divisa (backward compatibility)
        try:
            inventario_divisa = InventarioDivisaTerminal.objects.get(
                terminal=terminal,
                divisa=divisa_origen
            )
            inventario_divisa.cantidad += monto_origen
            inventario_divisa.save()
        except InventarioDivisaTerminal.DoesNotExist:
            # Crear si no existe
            InventarioDivisaTerminal.objects.create(
                terminal=terminal,
                divisa=divisa_origen,
                cantidad=monto_origen,
                actualizado_por=request.user if request.user.is_authenticated else None
            ) 

        if divisa_pago.code != 'PYG':
            raise ValueError("El pago debe ser en Guaraníes (PYG).")
        

        # ✅ NUEVO: Realizar transferencia bancaria automática
        try:
            # Importar función de transferencia desde transacciones/views.py
            from transacciones.views import (
                _extraer_cuenta_desde_medio,
                _get_cuenta_empresa,
                realizar_transferencia_bancaria
            )
            
            # Obtener datos del medio de pago del cliente
            medio_datos = transaccion.get_medio_pago_info() or {}
            ent_cli_hint, cta_cli = _extraer_cuenta_desde_medio(medio_datos)
            ent_emp, cta_emp = _get_cuenta_empresa()
            
            logger.info(
                f"[TAUSER-PAGO] Iniciando transferencia: "
                f"Empresa -> Cliente por ₲{monto_pago:,.0f}"
            )
            
            # Verificar que tengamos los datos necesarios
            if not (ent_cli_hint and cta_cli and ent_emp and cta_emp):
                raise ValueError(
                    "Datos bancarios incompletos. No se puede procesar el pago digital."
                )
            
            # Realizar transferencia de EMPRESA -> CLIENTE
            resultado = realizar_transferencia_bancaria(
                entidad_src=ent_emp,
                numero_cuenta_src=cta_emp,
                entidad_dst=ent_cli_hint,
                numero_cuenta_dst=cta_cli,
                monto=monto_pago,
                referencia=transaccion.numero_transaccion
            )
            
            if not resultado.get('ok'):
                raise ValueError(
                    f"Error en transferencia bancaria: {resultado.get('message')} "
                    f"(código {resultado.get('code')})"
                )
            
            # ✅ Transferencia exitosa
            comprobante = resultado.get('comprobante', '')
            
            logger.info(
                f"[TAUSER-PAGO] Transferencia exitosa. "
                f"Comprobante: {comprobante}"
            )
            
        except Exception as e:
            logger.error(f"[TAUSER-PAGO] Error en transferencia: {e}", exc_info=True)
            raise ValueError(f"No se pudo realizar la transferencia bancaria: {str(e)}")
        
        # ✅ Actualizar estado de la transacción a COMPLETADA
        transaccion.estado = 'completado'  # Usar 'completado' según tu modelo
        transaccion.save()
        
        # Registrar en historial
        HistorialTransaccion.objects.create(
            transaccion=transaccion,
            estado_anterior='pendiente',
            estado_nuevo='completado',
            observaciones=(
                f'Pago digital realizado en terminal {terminal.nombre}. '
                f'Comprobante: {comprobante}'
            ),
            modificado_por=request.user if request.user.is_authenticated else None
        )
        
        # Registrar operación exitosa
        RegistroTransaccionTerminal.objects.create(
            terminal=terminal,
            transaccion_original=transaccion,
            cliente=transaccion.cliente,
            tipo_operacion='PAGO',
            divisa=divisa_pago,
            monto_operacion=monto_pago,
            fue_exitoso=True,
            pin_usado=pin_usado,
            mensaje_error=f'Pago digital completado. Comprobante: {comprobante}'
        )
        
        logger.info(
            f"Pago digital completado - Terminal: {terminal.nombre}, "
            f"Cliente: {transaccion.cliente.nombre_completo}, "
            f"Monto: ₲{monto_pago:,.0f}, Comprobante: {comprobante}"
        )

    def _extraer_desglose_post(self, post_data):
        """
        Extrae el desglose de denominaciones del POST.
        
        Espera campos con formato: desglose_denominacion_{id} = cantidad
        """
        desglose = {}
        
        for key, value in post_data.items():
            if key.startswith('desglose_denominacion_'):
                try:
                    denom_id = int(key.split('_')[-1])
                    cantidad = int(value)
                    
                    if cantidad > 0:
                        desglose[denom_id] = cantidad
                        
                except (ValueError, IndexError):
                    continue
        
        return desglose


# ==================== CRUD DE TERMINALES (ADMIN) ====================

class TerminalListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista todas las terminales del sistema"""
    model = Terminal
    template_name = 'terminal_list.html'
    context_object_name = 'terminales'
    permission_required = 'tauser.view_terminal'
    paginate_by = 20

    def get_queryset(self):
        queryset = Terminal.objects.select_related('usuario_responsable').prefetch_related(
            'inventario_denominaciones__denominacion__divisa'
        )
        
        # Filtros
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(
                models.Q(nombre__icontains=buscar) |
                models.Q(codigo__icontains=buscar) |
                models.Q(ubicacion__icontains=buscar)
            )
        
        estado = self.request.GET.get('estado')
        if estado == 'activas':
            queryset = queryset.filter(is_activa=True)
        elif estado == 'inactivas':
            queryset = queryset.filter(is_activa=False)
        
        return queryset.order_by('-is_activa', 'nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_terminales'] = Terminal.objects.count()
        context['terminales_activas'] = Terminal.objects.filter(is_activa=True).count()
        
        # Calcular cantidad de divisas por terminal
        divisas_por_terminal = {}
        for terminal in context['terminales']:
            divisas = terminal.inventario_denominaciones.values_list(
                'denominacion__divisa', flat=True
            ).distinct()
            divisas_por_terminal[terminal.pk] = divisas.count()
        
        context['divisas_por_terminal'] = divisas_por_terminal
        return context


class TerminalCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Crea una nueva terminal"""
    model = Terminal
    form_class = TerminalForm
    template_name = 'terminal_form.html'
    success_url = reverse_lazy('tauser:terminal_list')
    permission_required = 'tauser.add_terminal'

    def form_valid(self, form):
        messages.success(self.request, f'Terminal "{form.instance.nombre}" creada exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nueva Terminal'
        context['boton_texto'] = 'Crear Terminal'
        return context


class TerminalUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Actualiza una terminal existente"""
    model = Terminal
    form_class = TerminalForm
    template_name = 'terminal_form.html'
    success_url = reverse_lazy('tauser:terminal_list')
    permission_required = 'tauser.change_terminal'

    def form_valid(self, form):
        messages.success(self.request, f'Terminal "{form.instance.nombre}" actualizada exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Terminal: {self.object.nombre}'
        context['boton_texto'] = 'Guardar Cambios'
        return context


class TerminalDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Elimina una terminal (soft delete - marca como inactiva)"""
    model = Terminal
    template_name = 'terminal_confirm_delete.html'
    success_url = reverse_lazy('tauser:terminal_list')
    permission_required = 'tauser.delete_terminal'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Soft delete: marcar como inactiva en lugar de eliminar
        self.object.is_activa = False
        self.object.save()
        messages.warning(request, f'Terminal "{self.object.nombre}" desactivada.')
        return redirect(self.success_url)


class TerminalDetailView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Detalle de una terminal con su inventario por denominaciones"""
    permission_required = 'tauser.view_terminal'
    template_name = 'terminal_detail.html'

    def get(self, request, pk):
        terminal = get_object_or_404(Terminal.objects.prefetch_related('inventario__divisa'), pk=pk)
        
        # Obtener inventario de denominaciones agrupado por divisa
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
        
        # Obtener últimas operaciones
        ultimas_operaciones = RegistroTransaccionTerminal.objects.filter(
            terminal=terminal
        ).select_related('cliente', 'divisa', 'transaccion_original').order_by('-fecha_operacion')[:20]
        
        # Estadísticas
        operaciones_exitosas = RegistroTransaccionTerminal.objects.filter(
            terminal=terminal,
            fue_exitoso=True
        ).count()
        
        operaciones_fallidas = RegistroTransaccionTerminal.objects.filter(
            terminal=terminal,
            fue_exitoso=False
        ).count()
        
        context = {
            'terminal': terminal,
            'inventario_por_divisa': inventarios_por_divisa,
            'totales_globales': totales_globales,
            'tiene_inventario': inventarios.exists(),
            'ultimas_operaciones': ultimas_operaciones,
            'operaciones_exitosas': operaciones_exitosas,
            'operaciones_fallidas': operaciones_fallidas,
        }
        
        return render(request, self.template_name, context)


# ==================== GESTIÓN DE INVENTARIO ====================

class InventarioTerminalView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Gestiona el inventario de divisas de una terminal"""
    permission_required = 'tauser.change_inventariodivisaterminal'
    template_name = 'inventario_terminal.html'

    def get(self, request, terminal_pk):
        terminal = get_object_or_404(Terminal, pk=terminal_pk)
        
        # Crear formset para el inventario existente
        from django.forms import inlineformset_factory
        InventarioFormSet = inlineformset_factory(
            Terminal,
            InventarioDivisaTerminal,
            form=InventarioDivisaTerminalForm,
            extra=1,
            can_delete=False
        )
        
        formset = InventarioFormSet(instance=terminal)
        
        context = {
            'terminal': terminal,
            'formset': formset,
        }
        
        return render(request, self.template_name, context)

    def post(self, request, terminal_pk):
        terminal = get_object_or_404(Terminal, pk=terminal_pk)
        
        from django.forms import inlineformset_factory
        InventarioFormSet = inlineformset_factory(
            Terminal,
            InventarioDivisaTerminal,
            form=InventarioDivisaTerminalForm,
            extra=1,
            can_delete=False
        )
        
        formset = InventarioFormSet(request.POST, instance=terminal)
        
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.actualizado_por = request.user
                instance.save()
            
            messages.success(request, 'Inventario actualizado correctamente.')
            return redirect('tauser:terminal_detail', pk=terminal.pk)
        
        context = {
            'terminal': terminal,
            'formset': formset,
        }
        
        return render(request, self.template_name, context)


@login_required
@user_passes_test(lambda u: u.has_perm('tauser.change_terminal'))
def toggle_terminal_activa(request, pk):
    """Activa/desactiva una terminal"""
    terminal = get_object_or_404(Terminal, pk=pk)
    terminal.is_activa = not terminal.is_activa
    terminal.save()
    
    estado = "activada" if terminal.is_activa else "desactivada"
    messages.success(request, f'Terminal "{terminal.nombre}" {estado}.')
    
    return redirect('tauser:terminal_list')


# ==================== GENERACIÓN DE PINES ====================

@login_required
@user_passes_test(lambda u: u.has_perm('clientes.view_cliente'))
def generar_pin_cliente(request, cliente_id):
    """Genera un PIN temporal para un cliente"""
    cliente = get_object_or_404(Cliente, pk=cliente_id, esta_activo=True)
    
    if request.method == 'POST':
        # Generar PIN de 6 dígitos
        pin = get_random_string(length=6, allowed_chars='0123456789')
        
        # Verificar que no exista (muy improbable, pero por seguridad)
        while PINTerminalCliente.objects.filter(pin=pin, usado=False, fecha_expiracion__gt=timezone.now()).exists():
            pin = get_random_string(length=6, allowed_chars='0123456789')
        
        # Calcular fecha de expiración (24 horas por defecto)
        duracion_horas = int(request.POST.get('duracion_horas', 24))
        fecha_expiracion = timezone.now() + timedelta(hours=duracion_horas)
        
        # Crear PIN
        pin_obj = PINTerminalCliente.objects.create(
            cliente=cliente,
            pin=pin,
            fecha_expiracion=fecha_expiracion
        )
        
        messages.success(
            request, 
            f'PIN generado exitosamente: <strong>{pin}</strong> (válido hasta {fecha_expiracion.strftime("%d/%m/%Y %H:%M")})'
        )
        
        # TODO: Enviar PIN por correo electrónico
        # from django.core.mail import send_mail
        # send_mail(...)
        
        logger.info(f"PIN generado para cliente {cliente.nombre_completo}: {pin}")
        
        return redirect('clientes:detalle_cliente', pk=cliente.id)
    
    context = {
        'cliente': cliente,
    }

    return render(request, 'tauser/generar_pin.html', context)

# ... agregar al final del archivo después de las vistas existentes ...

# ==================== GESTIÓN DE INVENTARIO DE DENOMINACIONES ====================

class InventarioDenominacionesView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista para gestionar el inventario de denominaciones de una terminal.
    """
    permission_required = 'tauser.view_inventariodenominacionterminal'
    template_name = 'inventario/gestionar_denominaciones.html'
    
    def get(self, request, terminal_codigo):
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
        
        # Obtener inventario agrupado por divisa
        inventarios = InventarioDenominacionTerminal.objects.filter(
            terminal=terminal
        ).select_related(
            'denominacion__divisa'
        ).order_by(
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
                    'inventarios': [],
                    'valor_total': Decimal('0'),
                    'total_billetes': 0,
                    'alertas': 0
                }
            
            inventarios_por_divisa[divisa_code]['inventarios'].append(inv)
            inventarios_por_divisa[divisa_code]['valor_total'] += inv.valor_total
            inventarios_por_divisa[divisa_code]['total_billetes'] += inv.cantidad
            
            if inv.necesita_reposicion:
                inventarios_por_divisa[divisa_code]['alertas'] += 1
        
        # Obtener denominaciones disponibles que no están en inventario
        denominaciones_disponibles = Denominacion.objects.filter(
            is_active=True
        ).exclude(
            id__in=inventarios.values_list('denominacion_id', flat=True)
        ).select_related('divisa').order_by('divisa__code', '-valor')
        
        context = {
            'terminal': terminal,
            'inventarios_por_divisa': inventarios_por_divisa,
            'denominaciones_disponibles': denominaciones_disponibles,
            'total_divisas': len(inventarios_por_divisa),
            'total_alertas': sum(d['alertas'] for d in inventarios_por_divisa.values()),
        }
        
        return render(request, self.template_name, context)


class ReponerDenominacionesView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista para reponer denominaciones en una terminal.
    """
    permission_required = 'tauser.change_inventariodenominacionterminal'
    template_name = 'inventario/reposicion_denominaciones.html'
    
    def get(self, request, terminal_codigo):
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
        
        # Obtener todas las denominaciones activas
        denominaciones = Denominacion.objects.filter(
            is_active=True
        ).select_related('divisa').order_by('divisa__code', '-valor')
        
        # Obtener inventario actual
        inventarios = InventarioDenominacionTerminal.objects.filter(
            terminal=terminal
        ).select_related('denominacion')
        
        # Crear mapa de inventario actual
        inventario_map = {
            inv.denominacion_id: inv for inv in inventarios
        }
        
        # Agrupar denominaciones por divisa
        denominaciones_por_divisa = {}
        for denom in denominaciones:
            divisa_code = denom.divisa.code
            if divisa_code not in denominaciones_por_divisa:
                denominaciones_por_divisa[divisa_code] = {
                    'divisa': denom.divisa,
                    'denominaciones': []
                }
            
            inventario_actual = inventario_map.get(denom.id)
            denominaciones_por_divisa[divisa_code]['denominaciones'].append({
                'denominacion': denom,
                'inventario_actual': inventario_actual,
                'cantidad_actual': inventario_actual.cantidad if inventario_actual else 0,
                'necesita_reposicion': inventario_actual.necesita_reposicion if inventario_actual else True,
            })
        
        context = {
            'terminal': terminal,
            'denominaciones_por_divisa': denominaciones_por_divisa,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, terminal_codigo):
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
        
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
                            defaults={
                                'cantidad': 0,
                                'actualizado_por': request.user
                            }
                        )
                        
                        cantidad_anterior = inventario.cantidad
                        inventario.cantidad += cantidad
                        inventario.ultima_reposicion = timezone.now()
                        inventario.actualizado_por = request.user
                        inventario.save()
                        
                        reposiciones.append({
                            'denominacion': denominacion,
                            'cantidad_repuesta': cantidad,
                            'cantidad_anterior': cantidad_anterior,
                            'cantidad_nueva': inventario.cantidad,
                        })
                        
                        total_reposiciones += cantidad
                        
                        logger.info(
                            f"Reposición - Terminal: {terminal.codigo}, "
                            f"Denominación: {denominacion}, Cantidad: +{cantidad}, "
                            f"Usuario: {request.user.username}"
                        )
                
                if total_reposiciones > 0:
                    messages.success(
                        request,
                        f"✓ Reposición exitosa: {total_reposiciones} billetes agregados "
                        f"en {len(reposiciones)} denominaciones."
                    )
                    
                    # Registrar en el log de operaciones
                    RegistroTransaccionTerminal.objects.create(
                        terminal=terminal,
                        tipo_operacion='REPOSICION',
                        fue_exitoso=True,
                        mensaje_error=f'Reposición de {total_reposiciones} billetes por {request.user.username}'
                    )
                else:
                    messages.warning(request, "No se realizaron reposiciones.")
                
        except Exception as e:
            messages.error(request, f"Error al reponer denominaciones: {str(e)}")
            logger.error(f"Error en reposición: {e}", exc_info=True)
        
        return redirect('tauser:inventario_denominaciones', terminal_codigo=terminal_codigo)


class AjustarInventarioDenominacionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista para ajustar manualmente el inventario de denominaciones.
    (Para correcciones, auditorías, etc.)
    """
    permission_required = 'tauser.change_inventariodenominacionterminal'
    
    def post(self, request, terminal_codigo):
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
        
        inventario_id = request.POST.get('inventario_id')
        nueva_cantidad = request.POST.get('nueva_cantidad')
        motivo = request.POST.get('motivo', 'Ajuste manual')
        
        try:
            inventario = InventarioDenominacionTerminal.objects.get(
                id=inventario_id,
                terminal=terminal
            )
            
            cantidad_anterior = inventario.cantidad
            inventario.cantidad = int(nueva_cantidad)
            inventario.actualizado_por = request.user
            inventario.save()
            
            diferencia = inventario.cantidad - cantidad_anterior
            signo = '+' if diferencia > 0 else ''
            
            # Registrar ajuste
            RegistroTransaccionTerminal.objects.create(
                terminal=terminal,
                tipo_operacion='AJUSTE',
                divisa=inventario.denominacion.divisa,
                fue_exitoso=True,
                mensaje_error=(
                    f'Ajuste de inventario: {inventario.denominacion} '
                    f'({cantidad_anterior} → {inventario.cantidad}, {signo}{diferencia}). '
                    f'Motivo: {motivo}. Usuario: {request.user.username}'
                )
            )
            
            messages.success(
                request,
                f"✓ Inventario ajustado: {inventario.denominacion} "
                f"({cantidad_anterior} → {inventario.cantidad})"
            )
            
            logger.warning(
                f"Ajuste manual de inventario - Terminal: {terminal.codigo}, "
                f"Denominación: {inventario.denominacion}, "
                f"Anterior: {cantidad_anterior}, Nueva: {inventario.cantidad}, "
                f"Motivo: {motivo}, Usuario: {request.user.username}"
            )
            
        except Exception as e:
            messages.error(request, f"Error al ajustar inventario: {str(e)}")
            logger.error(f"Error en ajuste de inventario: {e}", exc_info=True)
        
        return redirect('tauser:inventario_denominaciones', terminal_codigo=terminal_codigo)


class HistorialDenominacionesView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista para ver el historial de movimientos de denominaciones.
    """
    permission_required = 'tauser.view_registrotransaccionterminal'
    template_name = 'inventario/historial_denominaciones.html'
    context_object_name = 'registros'
    paginate_by = 50
    
    def get_queryset(self):
        terminal_codigo = self.kwargs['terminal_codigo']
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
        
        # Obtener registros con desgloses de denominaciones
        queryset = RegistroTransaccionTerminal.objects.filter(
            terminal=terminal
        ).prefetch_related(
            'desglose_denominaciones__denominacion__divisa'
        ).select_related(
            'cliente',
            'transaccion_original',
            'divisa'
        ).order_by('-fecha')
        
        # Filtros
        tipo_operacion = self.request.GET.get('tipo_operacion')
        if tipo_operacion:
            queryset = queryset.filter(tipo_operacion=tipo_operacion)
        
        divisa_code = self.request.GET.get('divisa')
        if divisa_code:
            queryset = queryset.filter(divisa__code=divisa_code)
        
        fecha_desde = self.request.GET.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        terminal_codigo = self.kwargs['terminal_codigo']
        context['terminal'] = get_object_or_404(Terminal, codigo=terminal_codigo)
        
        # Obtener divisas para filtro
        context['divisas'] = Divisa.objects.filter(is_active=True)
        
        # Filtros aplicados
        context['filtros'] = {
            'tipo_operacion': self.request.GET.get('tipo_operacion', ''),
            'divisa': self.request.GET.get('divisa', ''),
            'fecha_desde': self.request.GET.get('fecha_desde', ''),
            'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
        }
        
        return context


# ==================== REPORTES ====================

class ReporteOperacionesView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista para generar reportes de operaciones del TAUSER.
    """
    permission_required = 'tauser.view_registrotransaccionterminal'
    template_name = 'reportes/operaciones.html'
    
    def get(self, request, terminal_codigo):
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
        
        # Obtener rango de fechas
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        if not fecha_desde:
            fecha_desde = timezone.now().date() - timedelta(days=7)
        else:
            fecha_desde = timezone.datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        
        if not fecha_hasta:
            fecha_hasta = timezone.now().date()
        else:
            fecha_hasta = timezone.datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        
        # Obtener registros del período
        registros = RegistroTransaccionTerminal.objects.filter(
            terminal=terminal,
            fecha__date__gte=fecha_desde,
            fecha__date__lte=fecha_hasta
        ).select_related('divisa', 'cliente')
        
        # Estadísticas por tipo de operación
        from django.db.models import Count, Sum, Q
        
        stats = {
            'total_operaciones': registros.count(),
            'exitosas': registros.filter(fue_exitoso=True).count(),
            'fallidas': registros.filter(fue_exitoso=False).count(),
            'retiros': registros.filter(tipo_operacion='RETIRO').count(),
            'pagos': registros.filter(tipo_operacion='PAGO').count(),
            'consultas': registros.filter(tipo_operacion='CONSULTA').count(),
        }
        
        # Operaciones por divisa
        operaciones_por_divisa = registros.filter(
            divisa__isnull=False
        ).values(
            'divisa__code',
            'divisa__nombre',
            'tipo_operacion'
        ).annotate(
            total=Count('id'),
            monto_total=Sum('monto_operacion')
        ).order_by('divisa__code', 'tipo_operacion')
        
        # Agrupar por divisa
        divisas_stats = {}
        for item in operaciones_por_divisa:
            code = item['divisa__code']
            if code not in divisas_stats:
                divisas_stats[code] = {
                    'nombre': item['divisa__nombre'],
                    'retiros': 0,
                    'pagos': 0,
                    'monto_retiros': Decimal('0'),
                    'monto_pagos': Decimal('0'),
                }
            
            if item['tipo_operacion'] == 'RETIRO':
                divisas_stats[code]['retiros'] = item['total']
                divisas_stats[code]['monto_retiros'] = item['monto_total'] or Decimal('0')
            elif item['tipo_operacion'] == 'PAGO':
                divisas_stats[code]['pagos'] = item['total']
                divisas_stats[code]['monto_pagos'] = item['monto_total'] or Decimal('0')
        
        context = {
            'terminal': terminal,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'stats': stats,
            'divisas_stats': divisas_stats,
            'registros_recientes': registros.order_by('-fecha')[:20],
        }
        
        return render(request, self.template_name, context)


class ReporteDenominacionesView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista para generar reportes de uso de denominaciones.
    """
    permission_required = 'tauser.view_desgloseddenominacionoperacion'
    template_name = 'reportes/denominaciones.html'
    
    def get(self, request, terminal_codigo):
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
        
        # Obtener rango de fechas
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        if not fecha_desde:
            fecha_desde = timezone.now().date() - timedelta(days=7)
        else:
            fecha_desde = timezone.datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        
        if not fecha_hasta:
            fecha_hasta = timezone.now().date()
        else:
            fecha_hasta = timezone.datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        
        # Obtener desgloses del período
        from django.db.models import Sum, Count
        
        desgloses = DesgloseDenominacionOperacion.objects.filter(
            registro_operacion__terminal=terminal,
            registro_operacion__fecha__date__gte=fecha_desde,
            registro_operacion__fecha__date__lte=fecha_hasta
        ).select_related(
            'denominacion__divisa',
            'registro_operacion'
        )
        
        # Estadísticas por denominación
        stats_denominaciones = desgloses.values(
            'denominacion__divisa__code',
            'denominacion__valor',
            'denominacion__nombre',
            'tipo_movimiento'
        ).annotate(
            total_billetes=Sum('cantidad'),
            total_operaciones=Count('registro_operacion', distinct=True)
        ).order_by('denominacion__divisa__code', '-denominacion__valor')
        
        # Agrupar por divisa
        stats_por_divisa = {}
        for item in stats_denominaciones:
            code = item['denominacion__divisa__code']
            if code not in stats_por_divisa:
                stats_por_divisa[code] = {
                    'entregas': [],
                    'recepciones': [],
                }
            
            datos = {
                'valor': item['denominacion__valor'],
                'nombre': item['denominacion__nombre'],
                'total_billetes': item['total_billetes'],
                'total_operaciones': item['total_operaciones'],
            }
            
            if item['tipo_movimiento'] == 'ENTREGA':
                stats_por_divisa[code]['entregas'].append(datos)
            else:
                stats_por_divisa[code]['recepciones'].append(datos)
        
        # Inventario actual
        inventario_actual = InventarioDenominacionTerminal.objects.filter(
            terminal=terminal
        ).select_related('denominacion__divisa').order_by(
            'denominacion__divisa__code',
            '-denominacion__valor'
        )
        
        context = {
            'terminal': terminal,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'stats_por_divisa': stats_por_divisa,
            'inventario_actual': inventario_actual,
        }
        
        return render(request, self.template_name, context)


# ==================== API / AJAX ====================

@login_required
def api_inventario_denominaciones(request, terminal_codigo):
    """
    API endpoint para obtener inventario de denominaciones en tiempo real (AJAX).
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo)
    
    inventarios = InventarioDenominacionTerminal.objects.filter(
        terminal=terminal
    ).select_related('denominacion__divisa').order_by(
        'denominacion__divisa__code',
        '-denominacion__valor'
    )
    
    data = []
    for inv in inventarios:
        data.append({
            'id': inv.id,
            'denominacion_id': inv.denominacion.id,
            'divisa_code': inv.denominacion.divisa.code,
            'divisa_nombre': inv.denominacion.divisa.nombre,
            'valor': float(inv.denominacion.valor),
            'nombre': inv.denominacion.nombre,
            'cantidad': inv.cantidad,
            'valor_total': float(inv.valor_total),
            'necesita_reposicion': inv.necesita_reposicion,
            'cantidad_minima': inv.cantidad_minima,
        })
    
    return JsonResponse({
        'success': True,
        'inventarios': data,
        'total_items': len(data),
    })