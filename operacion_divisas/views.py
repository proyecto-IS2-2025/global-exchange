#operacion_divisas
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.test import RequestFactory
import json
from decimal import Decimal, ROUND_HALF_UP
import logging

from divisas.models import Divisa
from .forms import VentaDivisaForm, CompraDivisaForm
from simulador.views import calcular_simulacion_api
from clientes.views import get_medio_acreditacion_seleccionado, get_medio_pago_seleccionado
from divisas.views import redondear
# MFA para compra
from mfa.utils import generate_and_send_otp, check_otp_validity
from mfa.models import MFAConfig
from roles.decorators import require_permission  # ← AGREGAR ESTE IMPORT

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES (SIN CAMBIOS)
# ═══════════════════════════════════════════════════════════════════

def decimal_to_str(data):
    """
    Convierte todos los Decimal en dict/list a str (recursivo).
    """
    if isinstance(data, dict):
        return {k: decimal_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [decimal_to_str(v) for v in data]
    elif isinstance(data, Decimal):
        return str(data)
    return data


def determinar_decimales_divisa(codigo_divisa):
    """
    Determina cuántos decimales usar según la divisa.
    PYG = 0, resto = 2
    """
    return 0 if codigo_divisa.upper() == 'PYG' else 2


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
# VISTAS DE VENTA
# ═══════════════════════════════════════════════════════════════════

@method_decorator(require_permission("divisas.realizar_operacion", check_client_assignment=True), name="dispatch")
class VentaDivisaView(LoginRequiredMixin, FormView):
    """
    🔐 PROTEGIDA: divisas.realizar_operacion + validación cliente activo
    
    Vista para iniciar el proceso de venta de divisas.
    Solicita monto y divisa a vender.
    """
    template_name = "operaciones/venta/venta.html"
    form_class = VentaDivisaForm

    def get(self, request, *args, **kwargs):
        """Manejar peticiones AJAX para calcular conversión"""
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                divisa_id = request.GET.get('divisa_id')
                monto = request.GET.get('monto')
                
                if not divisa_id or not monto:
                    return JsonResponse({'success': False, 'error': 'Datos incompletos'})
                
                divisa = Divisa.objects.get(id=divisa_id)
                
                payload = {
                    "tipo_operacion": "venta",
                    "monto": str(monto),
                    "moneda": divisa.code
                }
                
                rf = RequestFactory()
                post_req = rf.post(
                    '/simulador/calcular/',
                    data=json.dumps(payload),
                    content_type='application/json'
                )
                post_req.session = request.session
                post_req.user = request.user
                
                resp = calcular_simulacion_api(post_req)
                data = json.loads(resp.content)
                
                return JsonResponse(data)
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        divisa = form.cleaned_data['divisa']
        monto = form.cleaned_data['monto']

        payload = {
            "tipo_operacion": "venta",
            "monto": str(monto),
            "moneda": divisa.code
        }

        rf = RequestFactory()
        post_req = rf.post(
            '/simulador/calcular/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        post_req.session = self.request.session
        post_req.user = self.request.user

        resp = calcular_simulacion_api(post_req)
        try:
            data = json.loads(resp.content)
        except Exception:
            form.add_error(None, "Error interno al comunicarse con el simulador.")
            return self.form_invalid(form)

        if not data.get("success"):
            form.add_error(None, data.get("error", "Error en la simulación"))
            return self.form_invalid(form)

        # Convertir Decimals antes de guardar
        self.request.session['venta_resultado'] = decimal_to_str(data)
        self.request.session.modified = True

        return redirect('operacion_divisas:venta_confirmacion')


@method_decorator(require_permission("divisas.realizar_operacion", check_client_assignment=True), name="dispatch")
class VentaConfirmacionView(LoginRequiredMixin, TemplateView):
    """
    🔐 PROTEGIDA: divisas.realizar_operacion + validación cliente activo
    
    Vista de confirmación de simulación de venta.
    Muestra los resultados antes de proceder.
    """
    template_name = "operaciones/venta/venta_confirmacion.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['resultado'] = self.request.session.get('venta_resultado')
        return ctx

    def post(self, request, *args, **kwargs):
        resultado = request.session.get("venta_resultado")
        if not resultado:
            messages.error(request, "No hay simulación para confirmar.")
            return redirect("operacion_divisas:venta")

        operacion = {
            "tipo": "venta",
            "divisa": (resultado.get("moneda_code") or "").strip().upper(),
            "divisa_nombre": resultado.get("moneda_nombre"),
            "monto_divisa": str(redondear(resultado.get("monto_original"), 2)),
            "monto_guaranies": str(redondear(resultado.get("monto_resultado"), 0)),
            "tasa_cambio": str(redondear(resultado.get("tasa_aplicada"), 2)),
            "comision": resultado.get("comision_aplicada"),
        }
        request.session["operacion"] = operacion
        request.session.modified = True

        return redirect("clientes:seleccionar_medio_acreditacion")


@method_decorator(require_permission("divisas.realizar_operacion", check_client_assignment=True), name="dispatch")
class SumarioVentaView(LoginRequiredMixin, TemplateView):
    """
    🔐 PROTEGIDA: divisas.realizar_operacion + validación cliente activo
    
    Vista del sumario final antes de confirmar la venta.
    Muestra operación + medio de acreditación seleccionado.
    """
    template_name = "operaciones/venta/venta_sumario.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["operacion"] = self.request.session.get("operacion")

        medio_inst = get_medio_acreditacion_seleccionado(self.request)
        medio_ctx = None

        if medio_inst:
            # Caso 1: instancia de ClienteMedioDePago
            if hasattr(medio_inst, "medio_de_pago"):
                medio_model = medio_inst.medio_de_pago
                
                tipo_label = "No definido"
                try:
                    if medio_model.tipo_medio:
                        from medios_pago.models import TIPO_MEDIO_CHOICES
                        tipo_dict = dict(TIPO_MEDIO_CHOICES)
                        tipo_label = tipo_dict.get(medio_model.tipo_medio, f"Tipo desconocido: {medio_model.tipo_medio}")
                    else:
                        api_info = medio_model.get_api_info()
                        tipo_label = api_info.get("nombre_usuario", "No definido")
                except Exception:
                    tipo_label = "No definido"

                try:
                    com = Decimal(str(medio_model.comision_porcentaje))
                    com_str = f"{com:.2f}%"
                except Exception:
                    com_str = str(medio_model.comision_porcentaje)

                medio_ctx = {
                    "id": medio_inst.id,
                    "nombre": medio_model.nombre,
                    "tipo": tipo_label,
                    "comision": com_str,
                }

            # Caso 2: dict
            elif isinstance(medio_inst, dict):
                medio_id = medio_inst.get("id")
                if medio_id:
                    try:
                        from clientes.models import ClienteMedioDePago
                        medio_real = ClienteMedioDePago.objects.select_related('medio_de_pago').get(id=medio_id)
                        medio_model = medio_real.medio_de_pago
                        
                        tipo_label = "No definido"
                        try:
                            if medio_model.tipo_medio:
                                from medios_pago.models import TIPO_MEDIO_CHOICES
                                tipo_dict = dict(TIPO_MEDIO_CHOICES)
                                tipo_label = tipo_dict.get(medio_model.tipo_medio, f"Tipo desconocido: {medio_model.tipo_medio}")
                            else:
                                api_info = medio_model.get_api_info()
                                tipo_label = api_info.get("nombre_usuario", "No definido")
                        except Exception:
                            tipo_label = "No definido"
                        
                        try:
                            com = Decimal(str(medio_model.comision_porcentaje))
                            com_str = f"{com:.2f}%"
                        except Exception:
                            com_str = str(medio_model.comision_porcentaje)
                        
                        medio_ctx = {
                            "id": medio_id,
                            "nombre": medio_inst.get("nombre", medio_model.nombre),
                            "tipo": tipo_label,
                            "comision": com_str,
                        }
                        
                    except Exception as e:
                        logger.error(f"Error al obtener medio real: {e}")
                        medio_ctx = {
                            "id": medio_inst.get("id"),
                            "nombre": medio_inst.get("nombre"),
                            "tipo": "Error al determinar tipo",
                            "comision": "No aplica" if medio_inst.get("comision") == "0.000" else f"{medio_inst.get('comision', '0')}%",
                        }
                else:
                    medio_ctx = {
                        "id": medio_inst.get("id"),
                        "nombre": medio_inst.get("nombre"),
                        "tipo": medio_inst.get("tipo") or medio_inst.get("tipo_legible") or "No definido",
                        "comision": "No aplica" if medio_inst.get("comision") == "0.000" else f"{medio_inst.get('comision', '0')}%",
                    }

        ctx["medio"] = medio_ctx
        return ctx

    def post(self, request, *args, **kwargs):
        medio_id = request.POST.get("medio_id")
        if not medio_id:
            messages.error(request, "Debe seleccionar un medio de acreditación.")
            return redirect("clientes:seleccionar_medio_acreditacion")

        try:
            from clientes.models import ClienteMedioDePago
            medio = ClienteMedioDePago.objects.get(id=medio_id, cliente=request.user)

            request.session["medio"] = {
                "nombre": medio.medio_de_pago.nombre,
                "comision": str(medio.comision) if medio.comision else None,
            }
            request.session.modified = True

            return redirect("operacion_divisas:venta_sumario")
        except Exception as e:
            messages.error(request, f"Error al procesar el medio de acreditación: {str(e)}")
            return redirect("clientes:seleccionar_medio_acreditacion")


# ═══════════════════════════════════════════════════════════════════
# VISTAS DE COMPRA
# ═══════════════════════════════════════════════════════════════════

@method_decorator(require_permission("divisas.realizar_operacion", check_client_assignment=True), name="dispatch")
class CompraDivisaView(LoginRequiredMixin, FormView):
    """
    🔐 PROTEGIDA: divisas.realizar_operacion + validación cliente activo
    
    Vista para iniciar el proceso de compra de divisas.
    Solicita monto en guaraníes y divisa a comprar.
    """
    template_name = "operaciones/compra/compra.html"
    form_class = CompraDivisaForm

    def get(self, request, *args, **kwargs):
        """Manejar peticiones AJAX para calcular conversión"""
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                divisa_id = request.GET.get('divisa_id')
                monto = request.GET.get('monto')
                
                if not divisa_id or not monto:
                    return JsonResponse({'success': False, 'error': 'Datos incompletos'})
                
                divisa = Divisa.objects.get(id=divisa_id)
                
                payload = {
                    "tipo_operacion": "compra",
                    "monto": str(monto),
                    "moneda": divisa.code
                }
                
                rf = RequestFactory()
                post_req = rf.post(
                    '/simulador/calcular/',
                    data=json.dumps(payload),
                    content_type='application/json'
                )
                post_req.session = request.session
                post_req.user = request.user
                
                resp = calcular_simulacion_api(post_req)
                data = json.loads(resp.content)
                
                return JsonResponse(data)
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        divisa = form.cleaned_data['divisa']
        monto = form.cleaned_data['monto']

        payload = {
            "tipo_operacion": "compra",
            "monto": str(monto),
            "moneda": divisa.code
        }

        rf = RequestFactory()
        post_req = rf.post(
            '/simulador/calcular/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        post_req.session = self.request.session
        post_req.user = self.request.user

        resp = calcular_simulacion_api(post_req)
        try:
            data = json.loads(resp.content)
        except Exception:
            form.add_error(None, "Error interno al comunicarse con el simulador.")
            return self.form_invalid(form)

        if not data.get("success"):
            form.add_error(None, data.get("error", "Error en la simulación"))
            return self.form_invalid(form)

        # Convertir Decimals y redondear
        if "monto_original" in data:
            data["monto_original"] = str(redondear(data["monto_original"]))
        if "monto_resultado" in data:
            data["monto_resultado"] = str(redondear(data["monto_resultado"]))
        if "tasa_aplicada" in data:
            data["tasa_aplicada"] = str(redondear(data["tasa_aplicada"]))

        self.request.session['compra_resultado'] = decimal_to_str(data)
        self.request.session.modified = True

        return redirect('operacion_divisas:compra_confirmacion')


@method_decorator(require_permission("divisas.realizar_operacion", check_client_assignment=True), name="dispatch")
class CompraConfirmacionView(LoginRequiredMixin, TemplateView):
    """
    🔐 PROTEGIDA: divisas.realizar_operacion + validación cliente activo
    
    Vista de confirmación de simulación de compra.
    Muestra los resultados antes de proceder.
    """
    template_name = "operaciones/compra/compra_confirmacion.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['resultado'] = self.request.session.get('compra_resultado')
        return ctx

    def post(self, request, *args, **kwargs):
        resultado = request.session.get("compra_resultado")
        if not resultado:
            messages.error(request, "No hay simulación para confirmar.")
            return redirect("operacion_divisas:compra")

        operacion = {
            "tipo": "compra",
            "divisa": (resultado.get("moneda_code") or "").strip().upper(),
            "divisa_nombre": resultado.get("moneda_nombre"),
            "monto_guaranies": str(redondear(resultado.get("monto_original"), 0)),
            "monto_divisa": str(redondear(resultado.get("monto_resultado"), 2)),
            "tasa_cambio": str(redondear(resultado.get("tasa_aplicada"), 2)),
            "comision": resultado.get("comision_aplicada"),
        }
        request.session["operacion"] = operacion
        request.session.modified = True

        return redirect("clientes:seleccionar_medio_pago")


@method_decorator(require_permission("divisas.realizar_operacion", check_client_assignment=True), name="dispatch")
class SumarioCompraView(LoginRequiredMixin, TemplateView):
    """
    🔐 PROTEGIDA: divisas.realizar_operacion + validación cliente activo
    
    Vista del sumario final antes de confirmar la compra.
    Muestra operación + medio de pago seleccionado.
    """
    template_name = "operaciones/compra/compra_sumario.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["operacion"] = self.request.session.get("operacion")
        
        medio_inst = get_medio_pago_seleccionado(self.request)
        medio_ctx = None

        if medio_inst:
            if hasattr(medio_inst, "medio_de_pago"):
                medio_model = medio_inst.medio_de_pago
                tipo_label = "No definido"
                try:
                    if medio_model.tipo_medio:
                        from medios_pago.models import TIPO_MEDIO_CHOICES
                        tipo_dict = dict(TIPO_MEDIO_CHOICES)
                        tipo_label = tipo_dict.get(medio_model.tipo_medio, f"Tipo desconocido: {medio_model.tipo_medio}")
                    else:
                        api_info = medio_model.get_api_info()
                        tipo_label = api_info.get("nombre_usuario", "No definido")
                except Exception:
                    tipo_label = "No definido"

                try:
                    com = Decimal(str(medio_model.comision_porcentaje))
                    com_str = f"{com:.2f}%"
                except Exception:
                    com_str = str(medio_model.comision_porcentaje)

                medio_ctx = {
                    "id": medio_inst.id,
                    "nombre": medio_model.nombre,
                    "tipo": tipo_label,
                    "comision": com_str,
                }

            elif isinstance(medio_inst, dict):
                medio_id = medio_inst.get("id")
                if medio_id:
                    try:
                        from clientes.models import ClienteMedioDePago
                        medio_real = ClienteMedioDePago.objects.select_related('medio_de_pago').get(id=medio_id)
                        medio_model = medio_real.medio_de_pago
                        
                        tipo_label = "No definido"
                        try:
                            if medio_model.tipo_medio:
                                from medios_pago.models import TIPO_MEDIO_CHOICES
                                tipo_dict = dict(TIPO_MEDIO_CHOICES)
                                tipo_label = tipo_dict.get(medio_model.tipo_medio, f"Tipo desconocido: {medio_model.tipo_medio}")
                            else:
                                api_info = medio_model.get_api_info()
                                tipo_label = api_info.get("nombre_usuario", "No definido")
                        except Exception:
                            tipo_label = "No definido"
                        
                        try:
                            com = Decimal(str(medio_model.comision_porcentaje))
                            com_str = f"{com:.2f}%"
                        except Exception:
                            com_str = str(medio_model.comision_porcentaje)
                        
                        medio_ctx = {
                            "id": medio_id,
                            "nombre": medio_inst.get("nombre", medio_model.nombre),
                            "tipo": tipo_label,
                            "comision": com_str,
                        }
                        
                    except Exception as e:
                        logger.error(f"Error al obtener medio real: {e}")
                        medio_ctx = {
                            "id": medio_inst.get("id"),
                            "nombre": medio_inst.get("nombre"),
                            "tipo": "Error al determinar tipo",
                            "comision": "No aplica" if medio_inst.get("comision") == "0.000" else f"{medio_inst.get('comision', '0')}%",
                        }

        ctx["medio"] = medio_ctx
        return ctx

    def post(self, request, *args, **kwargs):
        """
        Maneja la confirmación de compra.
        Genera OTP y redirige a verificación MFA antes de crear la transacción.
        """
        operacion = request.session.get("operacion")
        medio = request.session.get("medio_pago_seleccionado")
        
        if not operacion:
            messages.error(request, "No hay operación activa para confirmar.")
            return redirect("operacion_divisas:compra")
        
        if not medio:
            messages.error(request, "Debe seleccionar un medio de pago.")
            return redirect("clientes:seleccionar_medio_pago")
        
        # ==========================================================
        # === VERIFICAR SI MFA ESTÁ ACTIVO ===
        # ==========================================================
        mfa_config = MFAConfig.get_config()
        
        if mfa_config.mfa_compra_enabled:
            # MFA ACTIVO: Iniciar flujo de verificación
            # Guardar flag en sesión
            request.session['mfa_compra_pending'] = True
            request.session['mfa_compra_user_id'] = request.user.id
            request.session.modified = True
            
            # Generar y enviar código OTP
            if generate_and_send_otp(request.user, request):
                return redirect("operacion_divisas:compra_mfa_verify")
            else:
                messages.error(request, "Error al enviar el código de verificación.")
                return redirect("operacion_divisas:compra_sumario")
        else:
            # MFA DESACTIVADO: Crear transacción directamente
            request.method = 'POST'
            request.POST = request.POST.copy()
            messages.success(request, "Procesando tu compra...")
            
            from transacciones.views import crear_transaccion_desde_compra
            return crear_transaccion_desde_compra(request)


# ============================================================================
# VISTAS MFA PARA CONFIRMACIÓN DE COMPRA
# ============================================================================

def compra_mfa_verify_view(request):
    """Vista de verificación MFA específica para confirmación de compra."""
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión.")
        return redirect('login')
    

    def post(self, request, *args, **kwargs):
        """Procesar confirmación de pago"""
        logger.info(f"\n{'='*60}")
        logger.info(f"POST EN SUMARIO COMPRA - INICIANDO CONFIRMACIÓN DE PAGO")
        logger.info(f"{'='*60}")
        
        operacion = request.session.get("operacion")
        medio_pago = get_medio_pago_seleccionado(request)
        
        logger.info(f"Operación: {operacion}")
        logger.info(f"Medio pago tipo: {type(medio_pago)}")
        logger.info(f"Medio pago: {medio_pago}")
        
        if not operacion or not medio_pago:
            logger.error("❌ No hay operación o medio de pago")
            messages.error(request, "No hay operación o medio de pago seleccionado.")
            return redirect("operacion_divisas:compra")
        
        # Verificar si el medio de pago es Stripe
        logger.info(f"\n🔍 Verificando si el medio de pago es Stripe...")
        es_stripe = self._es_medio_stripe(medio_pago, request)
        logger.info(f"Resultado: es_stripe = {es_stripe}\n")
        
        if es_stripe:
            logger.info(f"➡️ REDIRIGIENDO A PROCESAMIENTO STRIPE")
            # Procesar pago con Stripe
            return self._procesar_pago_stripe(request, operacion, medio_pago)
        else:
            logger.info(f"➡️ REDIRIGIENDO A PROCESAMIENTO NORMAL (BANCO)")
            # Procesar pago normal (sin Stripe)
            return self._procesar_pago_normal(request, operacion, medio_pago)
    
    def _es_medio_stripe(self, medio_pago, request):
        """Verifica si el medio de pago debe procesarse con Stripe"""
        try:
            from clientes.models import ClienteMedioDePago
            
            logger.info(f"🔍 VERIFICANDO SI ES STRIPE...")
            logger.info(f"Tipo de medio_pago: {type(medio_pago)}")
            
            # Si medio_pago es un dict, obtener el objeto real
            if isinstance(medio_pago, dict):
                medio_id = medio_pago.get('id')
                logger.info(f"Es dict, ID: {medio_id}")
                if medio_id:
                    medio_obj = ClienteMedioDePago.objects.select_related('medio_de_pago').get(id=medio_id)
                else:
                    logger.warning("Dict sin ID, retornando False")
                    return False
            else:
                medio_obj = medio_pago
                logger.info(f"Es objeto ClienteMedioDePago")
            
            logger.info(f"Medio de pago: {medio_obj.medio_de_pago.nombre}")
            logger.info(f"Tipo medio: {medio_obj.medio_de_pago.tipo_medio}")
            logger.info(f"Datos campos: {medio_obj.datos_campos}")
            
            # MÉTODO 1: Verificar por tipo_medio
            if medio_obj.medio_de_pago.tipo_medio == 'stripe':
                logger.info(f"✅ DETECTADO COMO STRIPE por tipo_medio='stripe'")
                return True
            
            # MÉTODO 2: Verificar campo Entidad en datos_campos
            if 'Entidad' in medio_obj.datos_campos:
                entidad = str(medio_obj.datos_campos.get('Entidad', '')).lower()
                logger.info(f"Campo 'Entidad' encontrado: '{entidad}'")
                if 'stripe' in entidad:
                    logger.info(f"✅ DETECTADO COMO STRIPE por campo Entidad='{entidad}'")
                    return True
            
            # MÉTODO 3: Buscar en cualquier campo que contenga "stripe"
            for campo_nombre, valor in medio_obj.datos_campos.items():
                if 'stripe' in str(valor).lower():
                    logger.info(f"✅ DETECTADO COMO STRIPE por campo '{campo_nombre}' = '{valor}'")
                    return True
            
            logger.warning(f"❌ NO ES STRIPE - retornando False")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error al verificar si es Stripe: {e}", exc_info=True)
            return False
    
    def _procesar_pago_stripe(self, request, operacion, medio_pago):
        """Procesa el pago usando Stripe"""
        try:
            from stripe_payments.services import process_stripe_payment
            from clientes.models import ClienteMedioDePago
            
            logger.info(f"=== PROCESANDO PAGO CON STRIPE ===")
            logger.info(f"Tipo de medio_pago recibido: {type(medio_pago)}")
            
            # Si medio_pago es un dict, obtener el objeto real
            if isinstance(medio_pago, dict):
                medio_id = medio_pago.get('id')
                if medio_id:
                    logger.info(f"Obteniendo ClienteMedioDePago con ID: {medio_id}")
                    medio_pago_obj = ClienteMedioDePago.objects.select_related('medio_de_pago').get(id=medio_id)
                else:
                    logger.error("medio_pago es un dict sin ID")
                    messages.error(request, 'Error: No se pudo identificar el medio de pago')
                    return redirect('operacion_divisas:compra_sumario')
            else:
                medio_pago_obj = medio_pago
            
            logger.info(f"Medio de pago: {medio_pago_obj.medio_de_pago.nombre}")
            logger.info(f"Datos campos disponibles: {list(medio_pago_obj.datos_campos.keys())}")
            
            # Obtener IP del cliente
            client_ip = self._get_client_ip(request)
            
            # Procesar el pago
            logger.info(f"Llamando a process_stripe_payment...")
            success, transaction, error = process_stripe_payment(
                cliente=request.user,
                medio_pago_data=medio_pago_obj,  # Pasar el objeto, no el dict
                operacion_data=operacion,
                client_ip=client_ip
            )
            
            if success:
                logger.info(f"✅ Pago exitoso - Transaction ID: {transaction.id}")
                
                # Limpiar sesión
                request.session.pop('operacion', None)
                request.session.pop('medio_pago_seleccionado', None)
                request.session.pop('compra_resultado', None)
                request.session.modified = True
                
                messages.success(
                    request,
                    f'¡Pago procesado exitosamente con Stripe! ID de transacción: {transaction.payment_intent_id}'
                )
                
                # Redirigir a página de éxito con el ID de transacción
                return redirect('stripe_payments:transaction_detail', transaction_id=transaction.id)
            else:
                logger.error(f"❌ Pago fallido: {error}")
                messages.error(
                    request,
                    f'Error al procesar el pago con Stripe: {error}'
                )
                return redirect('operacion_divisas:compra_sumario')
                
        except Exception as e:
            logger.error(f"Error al procesar pago con Stripe: {e}", exc_info=True)
            messages.error(
                request,
                f'Error inesperado al procesar el pago: {str(e)}'
            )
            return redirect('operacion_divisas:compra_sumario')
    
    def _procesar_pago_normal(self, request, operacion, medio_pago):
        """Procesa el pago sin Stripe (método tradicional) - llama directamente a crear transacción"""
        logger.info(f"=== PROCESANDO PAGO NORMAL (BANCO) ===")
        logger.info(f"Llamando a crear_transaccion_desde_compra para procesamiento bancario")
        
        # Importar la vista de transacciones y llamarla directamente
        from transacciones.views import crear_transaccion_desde_compra
        
        # Llamar directamente a la vista (que espera POST)
        return crear_transaccion_desde_compra(request)
    
    def _get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    

    # Verificar que hay una compra pendiente de MFA
    mfa_compra_pending = request.session.get('mfa_compra_pending')
    mfa_compra_user_id = request.session.get('mfa_compra_user_id')
    
    if not mfa_compra_pending or mfa_compra_user_id != request.user.id:
        messages.error(request, "No hay una compra pendiente de verificación.")
        return redirect("operacion_divisas:compra")
    
    # ============================================================
    # === VERIFICAR SI MFA SIGUE ACTIVO ===
    # ============================================================
    # Si el admin desactivó MFA mientras el usuario estaba en el proceso,
    # procesar la compra directamente sin pedir código
    mfa_config = MFAConfig.get_config()
    
    if not mfa_config.mfa_compra_enabled:
        # MFA fue desactivado - procesar directamente
        if 'mfa_compra_pending' in request.session:
            del request.session['mfa_compra_pending']
        if 'mfa_compra_user_id' in request.session:
            del request.session['mfa_compra_user_id']
        
        request.method = 'POST'
        request.POST = request.POST.copy()
        messages.info(request, "Verificación MFA desactivada. Procesando tu compra...")
        
        from transacciones.views import crear_transaccion_desde_compra
        response = crear_transaccion_desde_compra(request)
        
        # NUEVO: Generar factura automáticamente
        if response.status_code == 302 and 'confirmacion' in response.url:
            try:
                from transacciones.models import Transaccion
                numero_transaccion = response.url.split('/')[-2]
                transaccion = Transaccion.objects.get(numero_transaccion=numero_transaccion)
                
                if transaccion.estado == 'pagada':
                    from facturacion_electronica.services import generar_factura_automatica
                    success, factura, error = generar_factura_automatica(transaccion)
                    
                    if success:
                        logger.info(f"✅ Factura generada (MFA off): {factura.numero_factura}")
                        messages.success(request, f"¡Factura {factura.numero_factura} generada exitosamente!")
                    else:
                        logger.warning(f"⚠️ Error generando factura (MFA off): {error}")
                        messages.warning(request, "La compra fue exitosa pero hubo un problema al generar la factura.")
            except Exception as e:
                logger.error(f"Error al generar factura (MFA off): {e}", exc_info=True)
        
        return response
    
    # Verificar que existan los datos de operación y medio
    operacion = request.session.get("operacion")
    medio = request.session.get("medio_pago_seleccionado")
    
    if not operacion or not medio:
        messages.error(request, "Datos de operación incompletos.")
        if 'mfa_compra_pending' in request.session:
            del request.session['mfa_compra_pending']
        if 'mfa_compra_user_id' in request.session:
            del request.session['mfa_compra_user_id']
        return redirect("operacion_divisas:compra")
    
    if request.method == 'POST':
        entered_code = request.POST.get('otp_code', '').strip()
        
        if not entered_code:
            messages.error(request, "Por favor, ingresa el código de verificación.")
        elif len(entered_code) != 6 or not entered_code.isdigit():
            messages.error(request, "El código debe tener exactamente 6 dígitos.")
        elif check_otp_validity(request.user, entered_code):
            # Código válido - limpiar flags de MFA y proceder a crear transacción
            if 'mfa_compra_pending' in request.session:
                del request.session['mfa_compra_pending']
            if 'mfa_compra_user_id' in request.session:
                del request.session['mfa_compra_user_id']
            request.session.modified = True
            
            # Crear un POST request simulado para crear_transaccion_desde_compra
            # Django requiere que el método sea POST
            request.method = 'POST'
            request.POST = request.POST.copy()  # Hacer mutable si es necesario
            
            messages.success(request, "Código verificado. Procesando tu compra...")
            
            # Importar y llamar directamente a la vista
            from transacciones.views import crear_transaccion_desde_compra
            response = crear_transaccion_desde_compra(request)
            
            # NUEVO: Generar factura automáticamente después de crear la transacción
            # Obtener la transacción creada desde la URL de redirección
            if response.status_code == 302 and 'confirmacion' in response.url:
                try:
                    # Extraer número de transacción de la URL
                    from transacciones.models import Transaccion
                    numero_transaccion = response.url.split('/')[-2]
                    transaccion = Transaccion.objects.get(numero_transaccion=numero_transaccion)
                    
                    # Generar factura si la transacción está pagada
                    if transaccion.estado == 'pagada':
                        from facturacion_electronica.services import generar_factura_automatica
                        success, factura, error = generar_factura_automatica(transaccion)
                        
                        if success:
                            logger.info(f"✅ Factura {factura.numero_factura} generada para transacción {transaccion.numero_transaccion}")
                            messages.success(request, f"¡Factura {factura.numero_factura} generada exitosamente!")
                        else:
                            logger.warning(f"⚠️ No se pudo generar factura para {transaccion.numero_transaccion}: {error}")
                            messages.warning(request, "La compra fue exitosa pero hubo un problema al generar la factura. Contacte a soporte.")
                except Exception as e:
                    logger.error(f"Error al generar factura automática: {e}", exc_info=True)
                    # No fallar la operación si falla la facturación
            
            return response
        else:
            messages.error(request, "El código es incorrecto o ha expirado. Por favor, intenta nuevamente.")
    
    # Generar máscara de email
    email_parts = request.user.email.split('@')
    if len(email_parts) == 2:
        local = email_parts[0]
        domain = email_parts[1]
        email_masked = f"{local[:3]}***@{domain[:1]}***.com"
    else:
        email_masked = f"{request.user.email[:3]}***"
    
    context = {
        'email_masked': email_masked,
        'user': request.user,
        'operacion': operacion,
        'medio': medio
    }
    return render(request, 'mfa/compra_mfa_verify.html', context)


def compra_mfa_resend_view(request):
    """Vista para reenviar código OTP en confirmación de compra."""
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión.")
        return redirect('login')
    
    mfa_compra_pending = request.session.get('mfa_compra_pending')
    mfa_compra_user_id = request.session.get('mfa_compra_user_id')
    
    if not mfa_compra_pending or mfa_compra_user_id != request.user.id:
        messages.error(request, "No hay una compra pendiente de verificación.")
        return redirect("operacion_divisas:compra")
    
    # Reenviar código
    if generate_and_send_otp(request.user, request):
        return redirect("operacion_divisas:compra_mfa_verify")
    else:
        messages.error(request, "Error al reenviar el código.")
        return redirect("operacion_divisas:compra_sumario")


# ═══════════════════════════════════════════════════════════════════
# VISTA DE SELECCIÓN DE OPERACIÓN
# ═══════════════════════════════════════════════════════════════════

@login_required
@require_permission("divisas.realizar_operacion", check_client_assignment=True)
def seleccionar_operacion_view(request):
    """
    🔐 PROTEGIDA: divisas.realizar_operacion + validación cliente activo
    
    Vista para seleccionar entre compra o venta de divisas.
    Punto de entrada principal para operaciones.
    """
    return render(request, "operaciones/seleccionar_operacion.html")
