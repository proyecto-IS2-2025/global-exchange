# transacciones/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import logging

from clientes.decorators import require_permission  # ← IMPORT PRINCIPAL
from .models import Transaccion, HistorialTransaccion
from clientes.models import Cliente
from divisas.models import Divisa
from clientes.views import get_medio_acreditacion_seleccionado, get_medio_pago_seleccionado
from clientes.services import verificar_limites

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES (SIN CAMBIOS)
# ═══════════════════════════════════════════════════════════════════

def get_cliente_from_session(request):
    """
    Obtiene el cliente activo desde la sesión.
    Retorna None si no hay cliente activo o no existe.
    """
    cliente_id = request.session.get('cliente_id')
    if not cliente_id:
        return None
    try:
        return Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return None


def calcular_monto_final(monto_base, es_compra=True):
    """
    Calcula el monto final aplicando las tasas correspondientes.
    """
    # ...existing code...
    pass


def generar_numero_transaccion():
    """
    Genera un número único de transacción basado en timestamp.
    """
    # ...existing code...
    pass


def determinar_decimales_divisa(codigo_divisa):
    """
    Determina cuántos decimales usar según la divisa.
    PYG = 0, resto = 2
    """
    return 0 if codigo_divisa.upper() == 'PYG' else 2


def redondear(valor, decimales=2):
    """
    Redondea un valor decimal con la cantidad de decimales especificada.
    """
    try:
        return Decimal(valor).quantize(
            Decimal("1") if decimales == 0 else Decimal("0." + "0" * decimales),
            rounding=ROUND_HALF_UP
        )
    except Exception:
        return valor


def preparar_datos_medio(medio_inst):
    """
    Prepara datos del medio de pago/acreditación para guardar en transacción.
    """
    medio_datos = {}
    if isinstance(medio_inst, dict) and medio_inst.get("id"):
        try:
            from clientes.models import ClienteMedioDePago
            medio_real = ClienteMedioDePago.objects.select_related('medio_de_pago').get(
                id=medio_inst.get("id")
            )
            medio_model = medio_real.medio_de_pago
            
            tipo_label = "No definido"
            if medio_model.tipo_medio:
                from medios_pago.models import TIPO_MEDIO_CHOICES
                tipo_dict = dict(TIPO_MEDIO_CHOICES)
                tipo_label = tipo_dict.get(medio_model.tipo_medio, "No definido")
            else:
                api_info = medio_model.get_api_info()
                tipo_label = api_info.get("nombre_usuario", "No definido")
            
            medio_datos = {
                'id': medio_inst.get("id"),
                'nombre': medio_model.nombre,
                'tipo': tipo_label,
                'comision': f"{medio_model.comision_porcentaje:.2f}%",
                'datos_campos': medio_real.datos_campos or {},
                'es_principal': medio_real.es_principal,
            }
        except Exception as e:
            logger.error(f"Error al obtener datos del medio: {e}")
            medio_datos = {
                'id': medio_inst.get("id"),
                'nombre': medio_inst.get("nombre", "Medio desconocido"),
                'tipo': "No definido",
                'comision': "0%",
            }
    return medio_datos


def limpiar_sesion_operacion(request, claves=None):
    """
    Limpia datos de operación de la sesión.
    """
    if claves is None:
        claves = ['operacion', 'venta_resultado', 'compra_resultado', 
                  'medio_acreditacion_seleccionado', 'medio_pago_seleccionado']
    
    for clave in claves:
        if clave in request.session:
            del request.session[clave]
    
    request.session.modified = True


# ═══════════════════════════════════════════════════════════════════
# VISTAS DE CREACIÓN DE TRANSACCIONES (YA PROTEGIDAS CORRECTAMENTE)
# ═══════════════════════════════════════════════════════════════════

@login_required
@require_permission("transacciones.add_transaccion", check_client_assignment=True)
def crear_transaccion_desde_venta(request):
    """
    🔐 PROTEGIDA: transacciones.add_transaccion + validación cliente asignado
    
    Vista para crear una transacción desde el sumario de venta.
    """
    if request.method != 'POST':
        messages.error(request, "Método no permitido.")
        return redirect('divisas:venta_sumario')

    try:
        operacion = request.session.get("operacion")
        medio_inst = get_medio_acreditacion_seleccionado(request)

        if not operacion:
            messages.error(request, "No se encontró información de la operación.")
            return redirect("divisas:venta")

        if not medio_inst:
            messages.error(request, "No se encontró el medio de acreditación seleccionado.")
            return redirect("clientes:seleccionar_medio_acreditacion")

        cliente_id = request.session.get('cliente_id')
        if not cliente_id:
            messages.error(request, "No se encontró cliente activo.")
            return redirect('clientes:seleccionar_cliente')

        cliente = get_object_or_404(Cliente, id=cliente_id, esta_activo=True)
        
        codigo_divisa = operacion.get('divisa', '').strip().upper()
        logger.debug(f"Código de divisa desde operación: '{codigo_divisa}'")
        
        if not codigo_divisa:
            messages.error(request, "No se encontró el código de divisa en la operación.")
            return redirect('divisas:venta_sumario')
        
        try:
            divisa_origen = Divisa.objects.get(code__iexact=codigo_divisa)
            logger.debug(f"Divisa origen encontrada: {divisa_origen}")
        except Divisa.DoesNotExist:
            logger.error(f"No se encontró divisa con código: {codigo_divisa}")
            messages.error(request, f"No se encontró la divisa con código: {codigo_divisa}")
            return redirect('divisas:venta_sumario')
        
        try:
            divisa_destino = Divisa.objects.get(code__iexact='PYG')
            logger.debug(f"Divisa destino encontrada: {divisa_destino}")
        except Divisa.DoesNotExist:
            logger.error("No se encontró la divisa PYG (Guaraní)")
            messages.error(request, "Error: No se encontró la divisa Guaraní (PYG) en el sistema.")
            return redirect('divisas:venta_sumario')

        try:
            monto_origen = Decimal(str(operacion.get('monto_divisa', '0')))
            monto_destino = Decimal(str(operacion.get('monto_guaranies', '0')))
            tasa_cambio = Decimal(str(operacion.get('tasa_cambio', '0')))
        except (ValueError, TypeError) as e:
            logger.error(f"Error al convertir montos a Decimal: {e}")
            messages.error(request, "Error en los datos de la operación.")
            return redirect('divisas:venta_sumario')

        decimales_origen = determinar_decimales_divisa(divisa_origen.code)
        decimales_destino = determinar_decimales_divisa(divisa_destino.code)
        
        monto_origen = redondear(monto_origen, decimales_origen)
        monto_destino = redondear(monto_destino, decimales_destino)
        tasa_cambio = redondear(tasa_cambio, 2)

        ok, msg = verificar_limites(cliente, monto_destino)
        if not ok:
            messages.error(request, msg)
            return redirect('divisas:venta_sumario')

        medio_datos = preparar_datos_medio(medio_inst)

        with transaction.atomic():
            transaccion = Transaccion.objects.create(
                tipo_operacion='venta',
                cliente=cliente,
                divisa_origen=divisa_origen,
                divisa_destino=divisa_destino,
                monto_origen=monto_origen,
                monto_destino=monto_destino,
                tasa_de_cambio_aplicada=tasa_cambio,
                estado='pendiente',
                medio_pago_datos=medio_datos,
                procesado_por=request.user,
                observaciones=f"Transacción creada desde venta de {divisa_origen.code} por {monto_origen} {divisa_origen.code}"
            )

            HistorialTransaccion.objects.create(
                transaccion=transaccion,
                estado_anterior='',
                estado_nuevo='pendiente',
                observaciones='Transacción creada',
                modificado_por=request.user
            )

        limpiar_sesion_operacion(request)

        messages.success(request, f'Transacción {transaccion.numero_transaccion} creada exitosamente.')
        return redirect('transacciones:confirmacion_operacion', numero_transaccion=transaccion.numero_transaccion)

    except Exception as e:
        logger.error(f"Error al crear transacción de venta: {e}")
        messages.error(request, f"Error al procesar la transacción: {str(e)}")
        return redirect('divisas:venta_sumario')


@login_required
@require_permission("transacciones.add_transaccion", check_client_assignment=True)
def crear_transaccion_desde_compra(request):
    """
    🔐 PROTEGIDA: transacciones.add_transaccion + validación cliente asignado
    
    Vista para crear una transacción desde el sumario de compra.
    """
    if request.method != 'POST':
        messages.error(request, "Método no permitido.")
        return redirect('divisas:compra_sumario')
    
    try:
        operacion = request.session.get("operacion")
        medio_inst = get_medio_pago_seleccionado(request)
        
        if not operacion:
            messages.error(request, "No se encontró información de la operación.")
            return redirect("divisas:compra")
        
        if not medio_inst:
            messages.error(request, "No se encontró el medio de pago seleccionado.")
            return redirect("clientes:seleccionar_medio_pago")

        cliente_id = request.session.get('cliente_id')
        if not cliente_id:
            messages.error(request, "No se encontró cliente activo.")
            return redirect('clientes:seleccionar_cliente')
        
        cliente = get_object_or_404(Cliente, id=cliente_id, esta_activo=True)
        
        codigo_divisa = operacion.get('divisa', '').strip().upper()
        logger.debug(f"Código de divisa desde operación: '{codigo_divisa}'")
        
        if not codigo_divisa:
            messages.error(request, "No se encontró el código de divisa en la operación.")
            return redirect('divisas:compra_sumario')
                
        try:
            divisa_origen = Divisa.objects.get(code__iexact='PYG')
            logger.debug(f"Divisa origen (PYG) encontrada: {divisa_origen}")
        except Divisa.DoesNotExist:
            logger.error("No se encontró la divisa PYG (Guaraní)")
            messages.error(request, "Error: No se encontró la divisa Guaraní (PYG) en el sistema.")
            return redirect('divisas:compra_sumario')
            
        try:
            divisa_destino = Divisa.objects.get(code__iexact=codigo_divisa)
            logger.debug(f"Divisa destino encontrada: {divisa_destino}")
        except Divisa.DoesNotExist:
            logger.error(f"No se encontró divisa con código: {codigo_divisa}")
            messages.error(request, f"No se encontró la divisa con código: {codigo_divisa}")
            return redirect('divisas:compra_sumario')

        try:
            monto_origen = Decimal(str(operacion.get('monto_guaranies', '0')))
            monto_destino = Decimal(str(operacion.get('monto_divisa', '0')))
            tasa_cambio = Decimal(str(operacion.get('tasa_cambio', '0')))
        except (ValueError, TypeError) as e:
            logger.error(f"Error al convertir montos a Decimal: {e}")
            messages.error(request, "Error en los datos de la operación.")
            return redirect('divisas:compra_sumario')

        ok, msg = verificar_limites(cliente, monto_destino)
        if not ok:
            messages.error(request, msg)
            return redirect('divisas:compra_sumario')

        decimales_origen = determinar_decimales_divisa(divisa_origen.code)
        decimales_destino = determinar_decimales_divisa(divisa_destino.code)
        
        monto_origen = redondear(monto_origen, decimales_origen)
        monto_destino = redondear(monto_destino, decimales_destino)
        tasa_cambio = redondear(tasa_cambio, 2)

        medio_datos = preparar_datos_medio(medio_inst)
        
        with transaction.atomic():
            transaccion = Transaccion.objects.create(
                tipo_operacion='compra',
                cliente=cliente,
                divisa_origen=divisa_origen,
                divisa_destino=divisa_destino,
                monto_origen=monto_origen,
                monto_destino=monto_destino,
                tasa_de_cambio_aplicada=tasa_cambio,
                estado='pendiente',
                medio_pago_datos=medio_datos,
                procesado_por=request.user,
                observaciones=f"Transacción creada desde compra de {divisa_destino.code} por {monto_origen} Gs."
            )
            
            HistorialTransaccion.objects.create(
                transaccion=transaccion,
                estado_anterior='',
                estado_nuevo='pendiente',
                observaciones='Transacción creada',
                modificado_por=request.user
            )
        
        limpiar_sesion_operacion(request, ['operacion', 'compra_resultado', 'medio_pago_seleccionado'])
        
        messages.success(request, f'Transacción {transaccion.numero_transaccion} creada exitosamente.')
        
        return redirect('transacciones:confirmacion_operacion', numero_transaccion=transaccion.numero_transaccion)
        
    except Exception as e:
        logger.error(f"Error al crear transacción de compra: {e}")
        messages.error(request, f"Error al procesar la transacción: {str(e)}")
        return redirect('divisas:compra_sumario')


# ═══════════════════════════════════════════════════════════════════
# VISTAS DE CONFIRMACIÓN Y HISTORIAL
# ═══════════════════════════════════════════════════════════════════

@login_required
@require_permission("transacciones.view_transaccion", check_client_assignment=True)
def confirmacion_operacion(request, numero_transaccion):
    """
    🔐 PROTEGIDA: transacciones.view_transaccion + validación cliente asignado
    
    Vista de confirmación de operación exitosa.
    El decorador valida automáticamente que el cliente tenga acceso a su transacción.
    """
    transaccion = get_object_or_404(
        Transaccion, 
        numero_transaccion=numero_transaccion
    )
    
    # Validación adicional: verificar que la transacción pertenece al cliente activo
    if not request.user.is_staff:
        cliente_id = request.session.get('cliente_id')
        if not cliente_id or str(transaccion.cliente.id) != str(cliente_id):
            messages.error(request, "No tiene permisos para ver esta transacción.")
            return redirect('inicio')
    
    return render(request, 'confirmacion_operacion.html', {
        'transaccion': transaccion,
    })


@method_decorator(require_permission("transacciones.view_transacciones_asignadas", check_client_assignment=True), name="dispatch")
class HistorialTransaccionesClienteView(LoginRequiredMixin, ListView):
    """
    🔐 PROTEGIDA: transacciones.view_transacciones_asignadas + validación cliente activo
    
    Vista del historial de transacciones del cliente activo.
    El decorador valida automáticamente que el usuario tenga el cliente asignado.
    """
    model = Transaccion
    template_name = 'historial_cliente.html'
    context_object_name = 'transacciones'
    paginate_by = 20

    def get_queryset(self):
        # Obtener cliente activo de la sesión
        cliente_id = self.request.session.get('cliente_id')
        if not cliente_id:
            return Transaccion.objects.none()
        
        try:
            cliente = Cliente.objects.get(id=cliente_id, esta_activo=True)
        except Cliente.DoesNotExist:
            return Transaccion.objects.none()
        
        # Filtros base
        queryset = Transaccion.objects.filter(
            cliente=cliente
        ).select_related(
            'divisa_origen', 'divisa_destino', 'cliente'
        ).order_by('-fecha_creacion')
        
        # Aplicar filtros adicionales
        tipo_filtro = self.request.GET.get('tipo', 'todos')
        if tipo_filtro in ['compra', 'venta']:
            queryset = queryset.filter(tipo_operacion=tipo_filtro)
        
        estado_filtro = self.request.GET.get('estado')
        if estado_filtro:
            queryset = queryset.filter(estado=estado_filtro)
        
        # Filtros de fecha
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
                queryset = queryset.filter(fecha_creacion__gte=fecha_desde_dt)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(fecha_creacion__lt=fecha_hasta_dt)
            except ValueError:
                pass
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        cliente_id = self.request.session.get('cliente_id')
        if cliente_id:
            try:
                context['cliente_activo'] = Cliente.objects.get(id=cliente_id, esta_activo=True)
            except Cliente.DoesNotExist:
                context['cliente_activo'] = None
        
        # Estadísticas del cliente
        if context.get('cliente_activo'):
            cliente = context['cliente_activo']
            context['estadisticas'] = {
                'total_transacciones': Transaccion.objects.filter(cliente=cliente).count(),
                'total_compras': Transaccion.objects.filter(cliente=cliente, tipo_operacion='compra').count(),
                'total_ventas': Transaccion.objects.filter(cliente=cliente, tipo_operacion='venta').count(),
                'pendientes': Transaccion.objects.filter(cliente=cliente, estado='pendiente').count(),
            }
        
        # Mantener valores de filtros en el contexto
        context['filtros'] = {
            'tipo': self.request.GET.get('tipo', 'todos'),
            'estado': self.request.GET.get('estado', ''),
            'fecha_desde': self.request.GET.get('fecha_desde', ''),
            'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
        }
        
        # Opciones para filtros
        context['estados_disponibles'] = Transaccion.ESTADO_CHOICES
        
        return context


@login_required
@require_permission("transacciones.view_transacciones_globales", check_client_assignment=False)
def historial_admin(request):
    """
    🔐 PROTEGIDA: transacciones.view_transacciones_globales
    
    Vista administrativa para ver TODAS las transacciones del sistema.
    Solo accesible para usuarios con permiso de visualización global.
    """
    # Filtros base
    transacciones = Transaccion.objects.select_related(
        'cliente', 'divisa_origen', 'divisa_destino', 'procesado_por'
    ).order_by('-fecha_creacion')
    
    # Aplicar filtros
    cliente_id = request.GET.get('cliente')
    if cliente_id:
        transacciones = transacciones.filter(cliente_id=cliente_id)
    
    tipo_filtro = request.GET.get('tipo')
    if tipo_filtro in ['compra', 'venta']:
        transacciones = transacciones.filter(tipo_operacion=tipo_filtro)
    
    estado_filtro = request.GET.get('estado')
    if estado_filtro:
        transacciones = transacciones.filter(estado=estado_filtro)
    
    # Filtros de fecha
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            transacciones = transacciones.filter(fecha_creacion__gte=fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d') + timedelta(days=1)
            transacciones = transacciones.filter(fecha_creacion__lt=fecha_hasta_dt)
        except ValueError:
            pass
    
    # Búsqueda por número de transacción o nombre de cliente
    busqueda = request.GET.get('busqueda')
    if busqueda:
        transacciones = transacciones.filter(
            Q(numero_transaccion__icontains=busqueda) |
            Q(cliente__nombre_completo__icontains=busqueda) |
            Q(cliente__cedula__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(transacciones, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas generales
    total_transacciones = Transaccion.objects.count()
    estadisticas = {
        'total': total_transacciones,
        'compras': Transaccion.objects.filter(tipo_operacion='compra').count(),
        'ventas': Transaccion.objects.filter(tipo_operacion='venta').count(),
        'pendientes': Transaccion.objects.filter(estado='pendiente').count(),
        'pagadas': Transaccion.objects.filter(estado='pagada').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'transacciones': page_obj,
        'clientes': Cliente.objects.filter(esta_activo=True).order_by('nombre_completo'),
        'estadisticas': estadisticas,
        'filtros': {
            'cliente': cliente_id or '',
            'tipo': tipo_filtro or '',
            'estado': estado_filtro or '',
            'fecha_desde': fecha_desde or '',
            'fecha_hasta': fecha_hasta or '',
            'busqueda': busqueda or '',
        },
        'estados_disponibles': Transaccion.ESTADO_CHOICES,
    }
    
    return render(request, 'historial_admin.html', context)


@method_decorator(require_permission("transacciones.view_transaccion", check_client_assignment=True), name="dispatch")
class DetalleTransaccionView(LoginRequiredMixin, DetailView):
    """
    🔐 PROTEGIDA: transacciones.view_transaccion + validación cliente asignado
    
    Vista detallada de una transacción.
    El decorador valida automáticamente los permisos y asignaciones.
    """
    model = Transaccion
    template_name = 'detalle_transaccion.html'
    context_object_name = 'transaccion'
    slug_field = 'numero_transaccion'
    slug_url_kwarg = 'numero_transaccion'

    def get_object(self, queryset=None):
        transaccion = super().get_object(queryset)
        
        # Validación adicional según rol
        if not self.request.user.is_staff:
            # Clientes solo ven sus propias transacciones
            cliente_id = self.request.session.get('cliente_id')
            if not cliente_id or str(transaccion.cliente.id) != str(cliente_id):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("No tiene permisos para ver esta transacción.")
        elif not self.request.user.has_perm('transacciones.view_transacciones_globales'):
            # Operadores solo ven transacciones de clientes asignados
            from clientes.models import AsignacionCliente
            if not AsignacionCliente.objects.filter(
                operador=self.request.user,
                cliente=transaccion.cliente,
                activa=True
            ).exists():
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("No tiene permisos para ver esta transacción.")
        
        return transaccion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar historial
        context['historial'] = self.object.historial.select_related('modificado_por').order_by('-fecha_cambio')
        
        # Información adicional
        context['puede_cancelar'] = self.object.puede_cancelarse
        context['puede_anular'] = self.object.puede_anularse
        context['es_admin'] = self.request.user.is_staff
        
        return context


# ═══════════════════════════════════════════════════════════════════
# VISTAS DE GESTIÓN (CAMBIO DE ESTADO, CANCELACIÓN)
# ═══════════════════════════════════════════════════════════════════

@login_required
@require_permission("transacciones.manage_estados_transacciones", check_client_assignment=False)
def cambiar_estado_transaccion(request, numero_transaccion):
    """
    🔐 PROTEGIDA: transacciones.manage_estados_transacciones
    
    Vista para cambiar el estado de una transacción.
    Solo accesible para usuarios con permiso de gestión de estados.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    transaccion = get_object_or_404(Transaccion, numero_transaccion=numero_transaccion)
    nuevo_estado = request.POST.get('nuevo_estado')
    observaciones = request.POST.get('observaciones', '')
    
    if nuevo_estado not in dict(Transaccion.ESTADO_CHOICES):
        return JsonResponse({'success': False, 'error': 'Estado no válido'})
    
    try:
        transaccion.cambiar_estado(
            nuevo_estado=nuevo_estado,
            observacion=observaciones,
            usuario=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Estado cambiado a {transaccion.get_estado_display()}',
            'nuevo_estado': nuevo_estado,
            'nuevo_estado_display': transaccion.get_estado_display()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_permission("transacciones.cancel_propias_transacciones", check_client_assignment=True)
def cancelar_transaccion(request, numero_transaccion):
    """
    🔐 PROTEGIDA: transacciones.cancel_propias_transacciones + validación cliente activo
    
    Vista para que el cliente cancele su transacción pendiente.
    El decorador valida automáticamente que el usuario tenga el permiso
    y que la transacción pertenezca al cliente activo.
    """
    transaccion = get_object_or_404(Transaccion, numero_transaccion=numero_transaccion)
    
    # Validación adicional: el cliente solo cancela sus propias transacciones
    if not request.user.is_staff:
        cliente_id = request.session.get('cliente_id')
        if not cliente_id or str(transaccion.cliente.id) != str(cliente_id):
            messages.error(request, "No tiene permisos para modificar esta transacción.")
            return redirect('transacciones:historial_cliente')
    
    if not transaccion.puede_cancelarse:
        messages.error(request, "Esta transacción no puede cancelarse.")
        return redirect('transacciones:detalle', numero_transaccion=numero_transaccion)
    
    if request.method == 'POST':
        try:
            # Obtener razón de cancelación si se proporcionó
            razon_cancelacion = request.POST.get('razon_cancelacion', '').strip()
            
            # Construir observación
            observacion_base = 'Transacción cancelada por el cliente'
            if razon_cancelacion:
                observacion_completa = f'{observacion_base}. Razón: {razon_cancelacion}'
            else:
                observacion_completa = observacion_base
            
            transaccion.cambiar_estado(
                nuevo_estado='cancelada',
                observacion=observacion_completa,
                usuario=request.user
            )
            messages.success(
                request, 
                f'Transacción {numero_transaccion} cancelada exitosamente.'
            )
            
            return redirect('transacciones:historial_cliente')
            
        except Exception as e:
            logger.error(f'Error al cancelar transacción {numero_transaccion}: {e}')
            messages.error(request, f'Error al cancelar la transacción: {str(e)}')
            return redirect('transacciones:detalle', numero_transaccion=numero_transaccion)
    
    # GET request - mostrar página de confirmación
    return render(request, 'confirmar_cancelacion.html', {
        'transaccion': transaccion
    })