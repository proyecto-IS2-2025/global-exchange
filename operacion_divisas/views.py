#operacion_divisas
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View, FormView, TemplateView
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from divisas.models import Divisa, TasaCambio, CotizacionSegmento
from clientes.models import Cliente, AsignacionCliente, Descuento, Segmento, ClienteMedioDePago
from divisas.forms import DivisaForm, TasaCambioForm
from .forms import VentaDivisaForm, CompraDivisaForm
from django.db.models import Max
from django.db.models import OuterRef, Subquery
from django.contrib.auth.decorators import login_required
#Visualización tasas inicio
from divisas.services import ultimas_por_segmento
from divisas.models import Divisa
from simulador.views import calcular_simulacion_api
from django.http import JsonResponse
import json
from django.test import RequestFactory
from clientes.views import get_medio_acreditacion_seleccionado, get_medio_pago_seleccionado
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import logging
from django.contrib import messages
from divisas.views import redondear








# --- VISTAS PARA VENTA USANDO LOGICA DEL SIMULADOR ---
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


class VentaDivisaView(LoginRequiredMixin, FormView):
    template_name = "operaciones/venta/venta.html"
    form_class = VentaDivisaForm

    def form_valid(self, form):
        divisa = form.cleaned_data['divisa']
        monto = form.cleaned_data['monto']

        payload = {
            "tipo_operacion": "venta",
            "monto": str(monto),  # ya es str
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

        # 🔹 Convertir Decimals antes de guardar
        self.request.session['venta_resultado'] = decimal_to_str(data)
        self.request.session.modified = True

        return redirect('operacion_divisas:venta_confirmacion')


class VentaConfirmacionView(LoginRequiredMixin, TemplateView):
    template_name = "operaciones/venta/venta_confirmacion.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['resultado'] = self.request.session.get('venta_resultado')
        return ctx

    def post(self, request, *args, **kwargs):
        resultado = request.session.get("venta_resultado")
        if not resultado:
            messages.error(request, "No hay simulación para confirmar.")
            return redirect("divisas:venta")

        operacion = {
            "tipo": "venta",
            "divisa": (resultado.get("moneda_code") or "").strip().upper(),
            "divisa_nombre": resultado.get("moneda_nombre"),
            # 🔹 divisa_origen (extranjera) → 2 decimales
            "monto_divisa": str(redondear(resultado.get("monto_original"), 2)),
            # 🔹 divisa_destino (guaraní) → 0 decimales
            "monto_guaranies": str(redondear(resultado.get("monto_resultado"), 0)),
            "tasa_cambio": str(redondear(resultado.get("tasa_aplicada"), 2)),
            "comision": resultado.get("comision_aplicada"),
        }
        request.session["operacion"] = operacion
        request.session.modified = True

        return redirect("clientes:seleccionar_medio_acreditacion")


logger = logging.getLogger(__name__)

class SumarioVentaView(TemplateView):
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
                
                # Determinar el tipo
                tipo_label = "No definido"
                try:
                    if medio_model.tipo_medio:
                        from medios_pago.models import TIPO_MEDIO_CHOICES
                        tipo_dict = dict(TIPO_MEDIO_CHOICES)
                        tipo_label = tipo_dict.get(medio_model.tipo_medio, f"Tipo desconocido: {medio_model.tipo_medio}")
                    else:
                        # Si no tiene tipo_medio, usar la lógica de inferencia
                        api_info = medio_model.get_api_info()
                        tipo_label = api_info.get("nombre_usuario", "No definido")
                except Exception:
                    tipo_label = "No definido"

                # Comisión
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

            # Caso 2: dict (el caso actual)
            elif isinstance(medio_inst, dict):
                # Obtener el objeto real desde la base de datos usando el ID
                medio_id = medio_inst.get("id")
                if medio_id:
                    try:
                        from clientes.models import ClienteMedioDePago
                        medio_real = ClienteMedioDePago.objects.select_related('medio_de_pago').get(id=medio_id)
                        medio_model = medio_real.medio_de_pago
                        
                        # Determinar el tipo usando el objeto real
                        tipo_label = "No definido"
                        try:
                            if medio_model.tipo_medio:
                                from medios_pago.models import TIPO_MEDIO_CHOICES
                                tipo_dict = dict(TIPO_MEDIO_CHOICES)
                                tipo_label = tipo_dict.get(medio_model.tipo_medio, f"Tipo desconocido: {medio_model.tipo_medio}")
                            else:
                                # Si no tiene tipo_medio, usar la lógica de inferencia
                                api_info = medio_model.get_api_info()
                                tipo_label = api_info.get("nombre_usuario", "No definido")
                        except Exception:
                            tipo_label = "No definido"
                        
                        # Usar la comisión del medio real
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
                        # Fallback si no se puede obtener el objeto real
                        logger.error(f"Error al obtener medio real: {e}")
                        medio_ctx = {
                            "id": medio_inst.get("id"),
                            "nombre": medio_inst.get("nombre"),
                            "tipo": "Error al determinar tipo",
                            "comision": "No aplica" if medio_inst.get("comision") == "0.000" else f"{medio_inst.get('comision', '0')}%",
                        }
                else:
                    # Si no hay ID, usar los datos del dict tal como están
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

            # Guardar en sesión como diccionario simple
            request.session["medio"] = {
                "nombre": medio.medio_de_pago.nombre,
                "comision": str(medio.comision) if medio.comision else None,
            }
            request.session.modified = True

            return redirect("divisas:venta_sumario")
        except Exception as e:
            messages.error(request, f"Error al procesar el medio de acreditación: {str(e)}")
            return redirect("clientes:seleccionar_medio_acreditacion")
        
        
def post(self, request, *args, **kwargs):
    medio_id = request.POST.get("medio_id")
    if not medio_id:
        messages.error(request, "Debe seleccionar un medio de acreditación.")
        return redirect("clientes:seleccionar_medio_acreditacion")

    medio = ClienteMedioDePago.objects.get(id=medio_id, cliente=request.user)

    # Guardar en sesión como diccionario simple
    request.session["medio"] = {
        "nombre": medio.medio_de_pago.nombre,
        "comision": str(medio.comision) if medio.comision else None,
    }
    request.session.modified = True

    return redirect("divisas:venta_sumario")




class CompraDivisaView(LoginRequiredMixin, FormView):
    template_name = "operaciones/compra/compra.html"
    form_class = CompraDivisaForm

    def form_valid(self, form):
        divisa = form.cleaned_data['divisa']
        monto = form.cleaned_data['monto']

        payload = {
            "tipo_operacion": "compra",
            "monto": str(monto),  # Monto en guaraníes
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
        # Redondear valores sensibles
        if "monto_original" in data:
            data["monto_original"] = str(redondear(data["monto_original"]))
        if "monto_resultado" in data:
            data["monto_resultado"] = str(redondear(data["monto_resultado"]))
        if "tasa_aplicada" in data:
            data["tasa_aplicada"] = str(redondear(data["tasa_aplicada"]))

        # Guardar en sesión ya limpio
        self.request.session['compra_resultado'] = decimal_to_str(data)
        self.request.session.modified = True

        self.request.session.modified = True

        return redirect('operacion_divisas:compra_confirmacion')


class CompraConfirmacionView(LoginRequiredMixin, TemplateView):
    template_name = "operaciones/compra/compra_confirmacion.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['resultado'] = self.request.session.get('compra_resultado')
        return ctx

    def post(self, request, *args, **kwargs):
        resultado = request.session.get("compra_resultado")
        if not resultado:
            messages.error(request, "No hay simulación para confirmar.")
            return redirect("divisas:compra")

        operacion = {
            "tipo": "compra",
            "divisa": (resultado.get("moneda_code") or "").strip().upper(),
            "divisa_nombre": resultado.get("moneda_nombre"),
            # 🔹 divisa_origen (guaraníes) → 0 decimales
            "monto_guaranies": str(redondear(resultado.get("monto_original"), 0)),
            # 🔹 divisa_destino (extranjera) → 2 decimales
            "monto_divisa": str(redondear(resultado.get("monto_resultado"), 2)),
            "tasa_cambio": str(redondear(resultado.get("tasa_aplicada"), 2)),
            "comision": resultado.get("comision_aplicada"),
        }
        request.session["operacion"] = operacion
        request.session.modified = True

        return redirect("clientes:seleccionar_medio_pago")



class SumarioCompraView(TemplateView):
    template_name = "operaciones/compra/compra_sumario.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["operacion"] = self.request.session.get("operacion")
        
        # Para compra usamos medio de pago (no acreditación)
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
    

def seleccionar_operacion_view(request):
    return render(request, "operaciones/seleccionar_operacion.html")
