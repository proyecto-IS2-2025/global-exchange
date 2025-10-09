# transacciones/views.py
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db import transaction
from datetime import datetime, timedelta
from .models import HistorialTransaccion
from clientes.models import Cliente
from divisas.models import Divisa
from clientes.views import get_medio_acreditacion_seleccionado, get_medio_pago_seleccionado
from decimal import Decimal
import logging
from django.contrib import messages
from django.shortcuts import render, redirect
from transacciones.models import Transaccion
logger = logging.getLogger(__name__)
from clientes.services import verificar_limites
from decimal import Decimal, ROUND_HALF_UP
import re  # NUEVO: para enmascarar valores

def redondear(valor, decimales=2):
    """
    Redondea un número Decimal a la cantidad de decimales especificada.
    - 0 → enteros (para Guaraníes)
    - 2 → centavos (para USD/EUR, etc.)
    """
    try:
        return Decimal(valor).quantize(
            Decimal("1") if decimales == 0 else Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
    except Exception:
        return Decimal("0.00")

def determinar_decimales_divisa(codigo_divisa):
    """
    Determina la cantidad de decimales según el código de divisa.
    PYG: 0 decimales, otras: 2 decimales.
    """
    return 0 if codigo_divisa.upper() == 'PYG' else 2


# ==== NUEVO: helpers de presentación de medio de pago/acreditación ====
def _humanize_etiqueta(nombre):
    try:
        s = str(nombre or '').strip()
        if not s:
            return 'Campo'
        return s.replace('_', ' ').replace('.', ' ').strip().title()
    except Exception:
        return 'Campo'

def _mask_generic(valor):
    if not valor:
        return ''
    s = str(valor).strip()
    # Email
    if '@' in s and '.' in s:
        local, _, domain = s.partition('@')
        return (local[:1] + '***@' + domain) if local else '***@' + domain
    # Numéricos largos: últimos 4
    digits = re.sub(r'\D', '', s)
    if len(digits) >= 6:
        return '****' + digits[-4:]
    # Genérico
    if len(s) > 6:
        return s[:2] + '****' + s[-2:]
    return '****'

def _build_medio_display(medio_datos):
    """
    Construye un objeto 'medio' listo para plantilla:
    { nombre, comision, tipo, campos: [ { etiqueta, valor, valor_enmascarado } ] }
    """
    if not isinstance(medio_datos, dict):
        return {}

    nombre = medio_datos.get('nombre') or ''
    comision = medio_datos.get('comision') or ''
    tipo = medio_datos.get('tipo') or ''
    campos_list = medio_datos.get('campos')

    # Si no hay lista de campos, construirla a partir de datos_campos
    if not campos_list:
        campos_list = []
        datos_campos = medio_datos.get('datos_campos') or {}
        if isinstance(datos_campos, dict):
            for key, value in datos_campos.items():
                etiqueta = _humanize_etiqueta(key)
                campos_list.append({
                    'etiqueta': etiqueta,
                    'valor': '' if value is None else str(value),
                    'valor_enmascarado': _mask_generic(value) if value else '',
                })

    return {
        'nombre': nombre,
        'comision': comision,
        'tipo': tipo,
        'campos': campos_list,
    }

@login_required
def crear_transaccion_desde_venta(request):
    """
    Vista para crear una transacción desde el sumario de venta
    """
    if request.method != 'POST':
        messages.error(request, "Método no permitido.")
        return redirect('operacion_divisas:venta_sumario')

    try:
        operacion = request.session.get("operacion")
        medio_inst = get_medio_acreditacion_seleccionado(request)

        if not operacion:
            messages.error(request, "No se encontró información de la operación.")
            return redirect("operacion_divisas:venta")

        if not medio_inst:
            messages.error(request, "No se encontró el medio de acreditación seleccionado.")
            return redirect("clientes:seleccionar_medio_acreditacion")

        # Obtener cliente activo
        cliente_id = request.session.get('cliente_id')
        if not cliente_id:
            messages.error(request, "No se encontró cliente activo.")
            return redirect('clientes:seleccionar_cliente')

        cliente = get_object_or_404(Cliente, id=cliente_id, esta_activo=True)
        
        # Obtener código de divisa desde operación
        codigo_divisa = operacion.get('divisa', '').strip().upper()
        logger.debug(f"Código de divisa desde operación: '{codigo_divisa}'")
        
        if not codigo_divisa:
            messages.error(request, "No se encontró el código de divisa en la operación.")
            return redirect('operacion_divisas:venta_sumario')
        
        # Buscar divisas con manejo de errores más específico
        try:
            divisa_origen = Divisa.objects.get(code__iexact=codigo_divisa)
            logger.debug(f"Divisa origen encontrada: {divisa_origen}")
        except Divisa.DoesNotExist:
            logger.error(f"No se encontró divisa con código: {codigo_divisa}")
            messages.error(request, f"No se encontró la divisa con código: {codigo_divisa}")
            return redirect('operacion_divisas:venta_sumario')
        
        try:
            divisa_destino = Divisa.objects.get(code__iexact='PYG')
            logger.debug(f"Divisa destino encontrada: {divisa_destino}")
        except Divisa.DoesNotExist:
            logger.error("No se encontró la divisa PYG (Guaraní)")
            messages.error(request, "Error: No se encontró la divisa Guaraní (PYG) en el sistema.")
            return redirect('operacion_divisas:venta_sumario')

        # Convertir montos a Decimal de forma segura
        try:
            monto_origen = Decimal(str(operacion.get('monto_divisa', '0')))  # divisa extranjera
            monto_destino = Decimal(str(operacion.get('monto_guaranies', '0')))  # guaraníes
            tasa_cambio = Decimal(str(operacion.get('tasa_cambio', '0')))
        except (ValueError, TypeError) as e:
            logger.error(f"Error al convertir montos a Decimal: {e}")
            messages.error(request, "Error en los datos de la operación.")
            return redirect('operacion_divisas:venta_sumario')

        # 🔹 Aplicar redondeo según regla - MEJORA ESPECÍFICA
        decimales_origen = determinar_decimales_divisa(divisa_origen.code)
        decimales_destino = determinar_decimales_divisa(divisa_destino.code)
        
        monto_origen = redondear(monto_origen, decimales_origen)  # según divisa origen
        monto_destino = redondear(monto_destino, decimales_destino)  # según divisa destino
        tasa_cambio = redondear(tasa_cambio, 2)  # tasa siempre con 2 decimales

        # Validar límites antes de crear
        ok, msg = verificar_limites(cliente, monto_destino)
        if not ok:
            messages.error(request, msg)
            return redirect('operacion_divisas:venta_sumario')

        # Preparar datos del medio
        medio_datos = preparar_datos_medio(medio_inst)

        # Crear transacción
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

        # Limpiar sesión
        limpiar_sesion_operacion(request)

        messages.success(request, f'Transacción {transaccion.numero_transaccion} creada exitosamente.')
        return redirect('transacciones:confirmacion_operacion', numero_transaccion=transaccion.numero_transaccion)

    except Exception as e:
        logger.error(f"Error al crear transacción de venta: {e}")
        messages.error(request, f"Error al procesar la transacción: {str(e)}")
        return redirect('operacion_divisas:venta_sumario')


@login_required
def crear_transaccion_desde_compra(request):
    """
    Vista para crear una transacción desde el sumario de compra
    """
    if request.method != 'POST':
        messages.error(request, "Método no permitido.")
        return redirect('operacion_divisas:compra_sumario')
    
    try:
        # Obtener datos de la sesión
        operacion = request.session.get("operacion")
        medio_inst = get_medio_pago_seleccionado(request)
        
        if not operacion:
            messages.error(request, "No se encontró información de la operación.")
            return redirect("operacion_divisas:compra")
        
        if not medio_inst:
            messages.error(request, "No se encontró el medio de pago seleccionado.")
            return redirect("clientes:seleccionar_medio_pago")

        # Obtener cliente desde la sesión
        cliente_id = request.session.get('cliente_id')
        if not cliente_id:
            messages.error(request, "No se encontró cliente activo.")
            return redirect('clientes:seleccionar_cliente')
        
        cliente = get_object_or_404(Cliente, id=cliente_id, esta_activo=True)
        
        # Obtener código de divisa desde operación
        codigo_divisa = operacion.get('divisa', '').strip().upper()
        logger.debug(f"Código de divisa desde operación: '{codigo_divisa}'")
        
        if not codigo_divisa:
            messages.error(request, "No se encontró el código de divisa en la operación.")
            return redirect('operacion_divisas:compra_sumario')
                
        # Obtener divisas - Para compra: origen=PYG, destino=divisa comprada
        try:
            divisa_origen = Divisa.objects.get(code__iexact='PYG')  # Guaraníes
            logger.debug(f"Divisa origen (PYG) encontrada: {divisa_origen}")
        except Divisa.DoesNotExist:
            logger.error("No se encontró la divisa PYG (Guaraní)")
            messages.error(request, "Error: No se encontró la divisa Guaraní (PYG) en el sistema.")
            return redirect('operacion_divisas:compra_sumario')
            
        try:
            divisa_destino = Divisa.objects.get(code__iexact=codigo_divisa)
            logger.debug(f"Divisa destino encontrada: {divisa_destino}")
        except Divisa.DoesNotExist:
            logger.error(f"No se encontró divisa con código: {codigo_divisa}")
            messages.error(request, f"No se encontró la divisa con código: {codigo_divisa}")
            return redirect('operacion_divisas:compra_sumario')

        # Convertir montos a Decimal de forma segura
        try:
            monto_origen = Decimal(str(operacion.get('monto_guaranies', '0')))  # guaraníes
            monto_destino = Decimal(str(operacion.get('monto_divisa', '0')))    # divisa extranjera
            tasa_cambio = Decimal(str(operacion.get('tasa_cambio', '0')))
        except (ValueError, TypeError) as e:
            logger.error(f"Error al convertir montos a Decimal: {e}")
            messages.error(request, "Error en los datos de la operación.")
            return redirect('operacion_divisas:compra_sumario')

        ok, msg = verificar_limites(cliente, monto_destino)
        if not ok:
            messages.error(request, msg)
            return redirect('operacion_divisas:compra_sumario')
        # Preparar datos del medio de pago
        medio_datos = {}
        if isinstance(medio_inst, dict) and medio_inst.get("id"):
            try:
                from clientes.models import ClienteMedioDePago
                medio_real = ClienteMedioDePago.objects.select_related('medio_de_pago').get(
                    id=medio_inst.get("id")
                )
                
                # Determinar el tipo del medio
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
        
        # 🔹 Aplicar redondeo según regla - MEJORA ESPECÍFICA
        decimales_origen = determinar_decimales_divisa(divisa_origen.code)
        decimales_destino = determinar_decimales_divisa(divisa_destino.code)
        
        monto_origen = redondear(monto_origen, decimales_origen)  # según divisa origen
        monto_destino = redondear(monto_destino, decimales_destino)  # según divisa destino
        tasa_cambio = redondear(tasa_cambio, 2)  # tasa siempre con 2 decimales

        # Preparar datos del medio
        medio_datos = preparar_datos_medio(medio_inst)
        
        # Crear la transacción
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
            
            # Crear historial inicial
            HistorialTransaccion.objects.create(
                transaccion=transaccion,
                estado_anterior='',
                estado_nuevo='pendiente',
                observaciones='Transacción creada',
                modificado_por=request.user
            )
        
        # Limpiar datos de sesión
        limpiar_sesion_operacion(request, ['operacion', 'compra_resultado', 'medio_pago_seleccionado'])
        
        messages.success(request, f'Transacción {transaccion.numero_transaccion} creada exitosamente.')
        
        # Redirigir a la página de confirmación
        return redirect('transacciones:confirmacion_operacion', numero_transaccion=transaccion.numero_transaccion)
        
    except Exception as e:
        logger.error(f"Error al crear transacción de compra: {e}")
        messages.error(request, f"Error al procesar la transacción: {str(e)}")
        return redirect('operacion_divisas:compra_sumario')


def preparar_datos_medio(medio_inst):
    """
    Función auxiliar para preparar los datos del medio de pago/acreditación
    """
    medio_datos = {}
    
    if isinstance(medio_inst, dict) and medio_inst.get("id"):
        try:
            from clientes.models import ClienteMedioDePago
            medio_real = ClienteMedioDePago.objects.select_related('medio_de_pago').get(
                id=medio_inst.get("id")
            )
            medio_model = medio_real.medio_de_pago
            
            # Determinar el tipo
            tipo_label = "No definido"
            if getattr(medio_model, 'tipo_medio', None):
                from medios_pago.models import TIPO_MEDIO_CHOICES
                tipo_dict = dict(TIPO_MEDIO_CHOICES)
                tipo_label = tipo_dict.get(medio_model.tipo_medio, "No definido")
            else:
                api_info = medio_model.get_api_info()
                tipo_label = api_info.get("nombre_usuario", "No definido")

            datos_campos = medio_real.datos_campos or {}

            # NUEVO: construir lista de campos con etiqueta y valor enmascarado
            campos = []
            if isinstance(datos_campos, dict):
                for key, value in datos_campos.items():
                    campos.append({
                        'etiqueta': _humanize_etiqueta(key),
                        'valor': '' if value is None else str(value),
                        'valor_enmascarado': _mask_generic(value) if value else '',
                    })

            medio_datos = {
                'id': medio_inst.get("id"),
                'nombre': medio_model.nombre,
                'tipo': tipo_label,
                'comision': f"{medio_model.comision_porcentaje:.2f}%",
                'datos_campos': datos_campos,
                'campos': campos,  # NUEVO: listo para mostrar en plantillas
                'es_principal': medio_real.es_principal,
            }
            
        except Exception as e:
            logger.error(f"Error al obtener datos del medio: {e}")
            medio_datos = {
                'id': medio_inst.get("id"),
                'nombre': medio_inst.get("nombre", "Medio desconocido"),
                'tipo': "No definido",
                'comision': "0%",
                'datos_campos': {},
                'campos': [],
            }
    
    return medio_datos


def limpiar_sesion_operacion(request, keys_adicionales=None):
    """
    Función auxiliar para limpiar datos de operación de la sesión
    """
    keys_default = ['operacion', 'venta_resultado', 'medio']
    if keys_adicionales:
        keys_default.extend(keys_adicionales)
    
    for key in keys_default:
        request.session.pop(key, None)
    
    request.session.modified = True


@login_required
def confirmacion_operacion(request, numero_transaccion):
    """
    Vista de confirmación de operación exitosa
    """
    transaccion = get_object_or_404(
        Transaccion, 
        numero_transaccion=numero_transaccion
    )
    
    # Verificar que el usuario tenga acceso a esta transacción
    cliente_id = request.session.get('cliente_id')
    if not request.user.is_staff and str(transaccion.cliente.id) != str(cliente_id):
        messages.error(request, "No tiene permisos para ver esta transacción.")
        return redirect('inicio')
    
    # NUEVO: construir medio para la plantilla desde la transacción y adjuntar alias en el objeto
    medio_raw = transaccion.get_medio_pago_info()
    medio = _build_medio_display(medio_raw)

    # Adjuntar propiedades derivadas para plantillas que lean desde transaccion.*
    transaccion.medio_display = medio
    transaccion.medio_campos = medio.get('campos', [])
    transaccion.medio_nombre = medio.get('nombre') or ''
    transaccion.medio_comision = medio.get('comision') or ''
    transaccion.medio_tipo = medio.get('tipo') or ''
    transaccion.tiene_datos_medio = bool(transaccion.medio_campos)

    return render(request, 'confirmacion_operacion.html', {
        'transaccion': transaccion,
        # Alias adicionales en contexto por compatibilidad
        'medio': medio,                   # Objeto listo para plantilla
        'medio_pago': medio,              # Alias opcional
        'medio_campos': transaccion.medio_campos,
        'tiene_datos_medio': transaccion.tiene_datos_medio,
        'medio_datos': medio_raw,         # RAW por si la plantilla lo usa
    })


class HistorialTransaccionesClienteView(LoginRequiredMixin, ListView):
    """
    Vista del historial de transacciones del cliente activo
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


def is_staff_or_admin(user):
    """Verificar si el usuario es staff o admin"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_staff_or_admin)
def historial_admin(request):
    """
    Vista administrativa para ver todas las transacciones
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


class DetalleTransaccionView(LoginRequiredMixin, DetailView):
    """
    Vista detallada de una transacción
    """
    model = Transaccion
    template_name = 'detalle_transaccion.html'
    context_object_name = 'transaccion'
    slug_field = 'numero_transaccion'
    slug_url_kwarg = 'numero_transaccion'

    def get_object(self, queryset=None):
        transaccion = super().get_object(queryset)
        
        # Verificar permisos
        if not self.request.user.is_staff:
            cliente_id = self.request.session.get('cliente_id')
            if not cliente_id or str(transaccion.cliente.id) != str(cliente_id):
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

        # NUEVO: medio listo para renderizado y alias/flags de ayuda
        medio_raw = self.object.get_medio_pago_info()
        medio = _build_medio_display(medio_raw)

        # Adjuntar propiedades derivadas para plantillas que lean desde transaccion.*
        self.object.medio_display = medio
        self.object.medio_campos = medio.get('campos', [])
        self.object.medio_nombre = medio.get('nombre') or ''
        self.object.medio_comision = medio.get('comision') or ''
        self.object.medio_tipo = medio.get('tipo') or ''
        self.object.tiene_datos_medio = bool(self.object.medio_campos)

        # Además incluir en el contexto por compatibilidad
        context['medio'] = medio
        context['medio_pago'] = medio
        context['medio_campos'] = self.object.medio_campos
        context['tiene_datos_medio'] = self.object.tiene_datos_medio
        context['medio_datos'] = medio_raw

        return context


@login_required
@user_passes_test(is_staff_or_admin)
def cambiar_estado_transaccion(request, numero_transaccion):
    """
    Vista para cambiar el estado de una transacción (solo admin)
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
def cancelar_transaccion(request, numero_transaccion):
    """
    Vista para que el cliente cancele su transacción pendiente
    """
    transaccion = get_object_or_404(Transaccion, numero_transaccion=numero_transaccion)
    
    # Verificar permisos
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