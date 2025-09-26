#divisas
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View, FormView, TemplateView
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Divisa, TasaCambio, CotizacionSegmento
from clientes.models import Cliente, AsignacionCliente, Descuento, Segmento, ClienteMedioDePago
from .forms import DivisaForm, TasaCambioForm, VentaDivisaForm
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


"""
Vistas para la gestión de divisas y tasas de cambio.

Este módulo define vistas basadas en clases (CBV) y funciones
que permiten listar, crear, actualizar y visualizar divisas
y sus tasas de cambio, incluyendo un visualizador para clientes
y otro para administradores.
"""
class DivisaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista de lista para mostrar todas las divisas.

    Requiere que el usuario esté autenticado y tenga el permiso `divisas.view_divisa`.
    Muestra las divisas en una tabla paginada.
    """
    permission_required = 'divisas.view_divisa'
    model = Divisa
    template_name = 'divisas/lista.html'
    context_object_name = 'divisas'
    paginate_by = 20


class DivisaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear una nueva divisa.

    Requiere que el usuario esté autenticado y tenga el permiso `divisas.add_divisa`.
    Asigna `is_active` a `False` por defecto al guardar la nueva divisa.
    """
    permission_required = 'divisas.add_divisa'
    model = Divisa
    form_class = DivisaForm
    template_name = 'divisas/form.html'
    success_url = reverse_lazy('divisas:lista')

    def form_valid(self, form):
        """
        Maneja el guardado del formulario válido.

        Establece `is_active` a `False` antes de guardar el objeto.
        
        :param form: El formulario de la divisa.
        :type form: :class:`~divisas.forms.DivisaForm`
        :return: Un objeto de respuesta HTTP.
        :rtype: django.http.HttpResponse
        """
        obj = form.save(commit=False)
        obj.is_active = False  # TODA nueva divisa nace deshabilitada
        obj.save()
        return redirect(self.success_url)


class DivisaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para editar una divisa existente.
    Requiere que el usuario esté autenticado y tenga el permiso 'divisas.change_divisa'
    """
    permission_required = 'divisas.change_divisa'
    model = Divisa
    form_class = DivisaForm
    template_name = 'divisas/form.html'
    success_url = reverse_lazy('divisas:lista')


class DivisaToggleActivaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Alterna el estado de activación de una divisa.

    Requiere autenticación y el permiso `divisas.change_divisa`.
    """
    permission_required = 'divisas.change_divisa'

    def post(self, request, pk):
        divisa = get_object_or_404(Divisa, pk=pk)
        divisa.is_active = not divisa.is_active
        divisa.save()
        return redirect('divisas:lista')


def redondear(valor, decimales=2):
    try:
        return Decimal(valor).quantize(
            Decimal("1") if decimales == 0 else Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
    except Exception:
        return valor

# ----------------------------
# TASAS DE CAMBIO
# ----------------------------
class TasaCambioListView(LoginRequiredMixin, ListView):
    """
    Vista de lista para las tasas de cambio de una divisa específica.

    Requiere que el usuario esté autenticado y tenga el permiso `divisas.view_tasacambio`.
    Muestra una tabla con las tasas de cambio históricas de una divisa.

    :param divisa_id: ID de la divisa. Se pasa a través de la URL.
    :type divisa_id: int
    """
    model = TasaCambio
    template_name = 'divisas/tasa_list.html'
    context_object_name = 'tasas'
    paginate_by = 20

    def get_queryset(self):
        """
        Filtra el queryset para mostrar solo las tasas de la divisa especificada.

        :return: El queryset filtrado de tasas de cambio.
        :rtype: django.db.models.query.QuerySet
        """
        divisa_id = self.kwargs['divisa_id']
        qs = TasaCambio.objects.filter(divisa_id=divisa_id).order_by('-fecha')

        ini = self.request.GET.get('inicio')
        fin = self.request.GET.get('fin')
        if ini:
            qs = qs.filter(fecha__gte=ini)
        if fin:
            qs = qs.filter(fecha__lte=fin)
        return qs

    def get_context_data(self, **kwargs):
        """
        Agrega la divisa al contexto de la plantilla.
        """
        ctx = super().get_context_data(**kwargs)
        ctx['divisa'] = get_object_or_404(Divisa, pk=self.kwargs['divisa_id'])
        return ctx


class TasaCambioCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Permite registrar una nueva tasa de cambio para una divisa.

    Requiere autenticación y el permiso `divisas.add_tasacambio`.
    Prellena valores con la última tasa registrada.
    """
    permission_required = 'divisas.add_tasacambio'
    model = TasaCambio
    form_class = TasaCambioForm
    template_name = 'divisas/tasa_form.html'


    def get_initial(self):
        initial = super().get_initial()
        divisa = get_object_or_404(Divisa, pk=self.kwargs['divisa_id'])
        ultima = TasaCambio.objects.filter(divisa=divisa).order_by('-fecha').first()
        if ultima:
            initial.update({
                'precio_base': ultima.precio_base,
                'comision_compra': ultima.comision_compra,
                'comision_venta': ultima.comision_venta,
            })
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['divisa'] = get_object_or_404(Divisa, pk=self.kwargs['divisa_id'])
        return kwargs

    def form_valid(self, form):
        tasa = form.save(commit=False)
        tasa.divisa = form.divisa
        tasa.creado_por = self.request.user
        tasa.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        # redirige al listado de tasas de la misma divisa
        return reverse('divisas:tasas', kwargs={'divisa_id': self.kwargs['divisa_id']})


class TasaCambioAllListView(LoginRequiredMixin, ListView):
    """
    Vista para ver todas las tasas de cambio de todas las divisas.

    Permite filtrar por divisa y rango de fechas.
    """
    model = TasaCambio
    template_name = 'tasa_list_global.html'
    context_object_name = 'tasas'
    paginate_by = 20

    def get_queryset(self):
        """
        Filtra el queryset de tasas de cambio basado en los parámetros de la URL.

        Los filtros disponibles son:
        * `divisa`: ID o código de la divisa.
        * `inicio`: Fecha de inicio del rango (formato YYYY-MM-DD).
        * `fin`: Fecha de fin del rango (formato YYYY-MM-DD).

        :return: El queryset filtrado de tasas de cambio.
        :rtype: django.db.models.query.QuerySet
        """
        qs = TasaCambio.objects.select_related('divisa').order_by('fecha')

        divisa_param = self.request.GET.get('divisa')
        ini = self.request.GET.get('inicio')
        fin = self.request.GET.get('fin')

        if divisa_param:
            if divisa_param.isdigit():
                qs = qs.filter(divisa_id=int(divisa_param))
            else:
                qs = qs.filter(divisa__code__iexact=divisa_param)

        if ini:
            qs = qs.filter(fecha__gte=ini)
        if fin:
            qs = qs.filter(fecha__lte=fin)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['divisas'] = Divisa.objects.order_by('code')
        # Mantener valores del filtro en el form
        ctx['f_divisa'] = self.request.GET.get('divisa', '')
        ctx['f_inicio'] = self.request.GET.get('inicio', '')
        ctx['f_fin'] = self.request.GET.get('fin', '')
        return ctx





def visualizador_tasas(request):
    """
    Muestra las tasas de cambio actuales filtradas por el cliente activo en la sesión.
    Si no hay cliente activo, usa el segmento 'general'.
    """
    from clientes.models import Cliente, Segmento
    from .services import ultimas_por_segmento

    segmento_activo = None

    # 1. Detectar cliente activo en la sesión
    cliente_id = request.session.get("cliente_id")

    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id, esta_activo=True)
            segmento_activo = cliente.segmento
        except Cliente.DoesNotExist:
            pass

    # 2. Si no hay cliente activo, usar segmento "general"
    if not segmento_activo:
        segmento_activo, _ = Segmento.objects.get_or_create(name="general")

    # 3. Obtener divisas activas
    divisas_activas = Divisa.objects.filter(is_active=True).order_by("code")
    divisas_data = []

    for divisa in divisas_activas:
        # Obtener las últimas cotizaciones
        ultimas_cotizaciones = ultimas_por_segmento(divisa)

        # Filtrar SOLO el segmento activo
        cotizaciones_segmento = [
            cot for cot in ultimas_cotizaciones
            if cot.segmento == segmento_activo
        ]

        divisas_data.append({
            "divisa": divisa,
            "cotizaciones": cotizaciones_segmento
        })

    return render(request, "visualizador.html", {
        "divisas_data": divisas_data,
        "segmento_activo": segmento_activo
    })

#Para administradores
from django.contrib.auth.decorators import user_passes_test

def is_admin_or_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(is_admin_or_staff)
def visualizador_tasas_admin(request):
    """
    Vista administrativa que muestra todas las cotizaciones de todos los segmentos.
    Solo accesible para staff y superusuarios.
    """
    from .services import ultimas_por_segmento
    
    divisas_activas = Divisa.objects.filter(is_active=True).order_by('code')
    divisas_data = []
    
    for divisa in divisas_activas:
        # Obtener las últimas cotizaciones para esta divisa (todos los segmentos)
        ultimas_cotizaciones = ultimas_por_segmento(divisa)
        
        divisas_data.append({
            'divisa': divisa,
            'cotizaciones': list(ultimas_cotizaciones)
        })
    
    return render(request, 'visualizador_admin.html', {
        'divisas_data': divisas_data,
        'is_admin_view': True
    })


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
    template_name = "operaciones/venta.html"
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

        return redirect('divisas:venta_confirmacion')


class VentaConfirmacionView(LoginRequiredMixin, TemplateView):
    template_name = "operaciones/venta_confirmacion.html"

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


class VentaMediosView(LoginRequiredMixin, TemplateView):
    template_name = "operaciones/venta_medios.html"



logger = logging.getLogger(__name__)

class SumarioOperacionView(TemplateView):
    template_name = "operaciones/venta_sumario.html"

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



from .forms import CompraDivisaForm

class CompraDivisaView(LoginRequiredMixin, FormView):
    template_name = "operaciones/compra.html"
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

        return redirect('divisas:compra_confirmacion')


class CompraConfirmacionView(LoginRequiredMixin, TemplateView):
    template_name = "operaciones/compra_confirmacion.html"

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
    template_name = "operaciones/compra_sumario.html"

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
    

from django.shortcuts import render

def seleccionar_operacion_view(request):
    return render(request, "operaciones/seleccionar_operacion.html")
