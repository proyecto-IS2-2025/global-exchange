#divisas
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal, ROUND_HALF_UP
import json
import logging

from .models import Divisa, TasaCambio, CotizacionSegmento
from clientes.models import Cliente, Segmento
from .forms import DivisaForm, TasaCambioForm
from .services import ultimas_por_segmento
from roles.decorators import require_permission  # ← AGREGAR ESTE IMPORT


# ═══════════════════════════════════════════════════════════════════
# VISTAS DE DIVISAS
# ═══════════════════════════════════════════════════════════════════

@method_decorator(require_permission("divisas.view_divisas", check_client_assignment=False), name="dispatch")
class DivisaListView(LoginRequiredMixin, ListView):  # ← ELIMINAR PermissionRequiredMixin
    """
    🔐 PROTEGIDA: divisas.view_divisas

    Vista de lista para gestionar divisas del sistema.
    """
    model = Divisa
    template_name = 'divisas/lista.html'
    context_object_name = 'divisas'
    paginate_by = 20
    
    def get_queryset(self):
        # PYG siempre primero
        return Divisa.objects.all().order_by('-es_moneda_base', 'code')


@method_decorator(require_permission("divisas.manage_divisas", check_client_assignment=False), name="dispatch")
class DivisaCreateView(LoginRequiredMixin, CreateView):  # ← ELIMINAR PermissionRequiredMixin
    """
    🔐 PROTEGIDA: divisas.manage_divisas

    Vista para crear una nueva divisa.
    Asigna `is_active` a `False` por defecto al guardar la nueva divisa.
    """
    model = Divisa
    form_class = DivisaForm
    template_name = 'divisas/form.html'
    success_url = reverse_lazy('divisas:lista')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.is_active = False  # TODA nueva divisa nace deshabilitada
        obj.save()
        messages.success(self.request, f"Divisa {obj.code} creada correctamente (deshabilitada).")
        return redirect(self.success_url)


@method_decorator(require_permission("divisas.manage_divisas", check_client_assignment=False), name="dispatch")
class DivisaUpdateView(LoginRequiredMixin, UpdateView):  # ← ELIMINAR PermissionRequiredMixin
    """
    🔐 PROTEGIDA: divisas.manage_divisas

    Vista para editar una divisa existente.
    Bloquea la edición de la moneda base (PYG).
    """
    model = Divisa
    form_class = DivisaForm
    template_name = 'divisas/form.html'
    success_url = reverse_lazy('divisas:lista')
    
    def dispatch(self, request, *args, **kwargs):
        divisa = self.get_object()
        if divisa.es_moneda_base:
            messages.error(request, "No se puede editar la moneda base del sistema.")
            return redirect('divisas:lista')
        return super().dispatch(request, *args, **kwargs)


@method_decorator(require_permission("divisas.manage_divisas", check_client_assignment=False), name="dispatch")
class DivisaToggleActivaView(LoginRequiredMixin, View):  # ← ELIMINAR PermissionRequiredMixin
    """
    🔐 PROTEGIDA: divisas.manage_divisas

    Vista para activar/desactivar una divisa.
    Bloquea la desactivación de la moneda base (PYG).
    """
    def post(self, request, pk):
        divisa = get_object_or_404(Divisa, pk=pk)
        
        if divisa.es_moneda_base:
            messages.error(request, "No se puede deshabilitar la moneda base del sistema.")
            return redirect('divisas:lista')
        
        divisa.is_active = not divisa.is_active
        divisa.save()
        
        estado = "habilitada" if divisa.is_active else "deshabilitada"
        messages.success(request, f"Divisa {divisa.code} {estado} correctamente.")
        
        return redirect('divisas:lista')


# ═══════════════════════════════════════════════════════════════════
# VISTAS DE TASAS DE CAMBIO
# ═══════════════════════════════════════════════════════════════════

@method_decorator(require_permission("divisas.view_tasas_cambio", check_client_assignment=False), name="dispatch")
class TasaCambioListView(LoginRequiredMixin, ListView):  # ← AGREGAR DECORADOR
    """
    🔐 PROTEGIDA: divisas.view_tasas_cambio

    Vista de lista para las tasas de cambio de una divisa específica.
    Muestra historial de tasas con filtros de fecha.
    """
    model = TasaCambio
    template_name = 'divisas/tasa_list.html'
    context_object_name = 'tasas'
    paginate_by = 20

    def get_queryset(self):
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
        ctx = super().get_context_data(**kwargs)
        ctx['divisa'] = get_object_or_404(Divisa, pk=self.kwargs['divisa_id'])
        return ctx


@method_decorator(require_permission("divisas.manage_tasas_cambio", check_client_assignment=False), name="dispatch")
class TasaCambioCreateView(LoginRequiredMixin, CreateView):  # ← ELIMINAR PermissionRequiredMixin
    """
    🔐 PROTEGIDA: divisas.manage_tasas_cambio

    Permite registrar una nueva tasa de cambio para una divisa.
    Prellena valores con la última tasa registrada.
    Bloquea la creación de tasas para la moneda base (PYG).
    """
    model = TasaCambio
    form_class = TasaCambioForm
    template_name = 'divisas/tasa_form.html'

    def dispatch(self, request, *args, **kwargs):
        divisa = get_object_or_404(Divisa, pk=self.kwargs['divisa_id'])
        if divisa.es_moneda_base:
            messages.error(request, "No se pueden registrar tasas de cambio para la moneda base del sistema.")
            return redirect('divisas:lista')
        return super().dispatch(request, *args, **kwargs)

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
        messages.success(self.request, f"Tasa de cambio registrada para {tasa.divisa.code}.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('divisas:tasas', kwargs={'divisa_id': self.kwargs['divisa_id']})


@method_decorator(require_permission("divisas.view_tasas_cambio", check_client_assignment=False), name="dispatch")
class TasaCambioAllListView(LoginRequiredMixin, ListView):  # ← AGREGAR DECORADOR
    """
    🔐 PROTEGIDA: divisas.view_tasas_cambio

    Vista para ver todas las tasas de cambio de todas las divisas.
    Permite filtrar por divisa y rango de fechas.
    """
    model = TasaCambio
    template_name = 'tasa_list_global.html'
    context_object_name = 'tasas'
    paginate_by = 20

    def get_queryset(self):
        qs = TasaCambio.objects.select_related('divisa').order_by('-fecha')

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
        ctx['f_divisa'] = self.request.GET.get('divisa', '')
        ctx['f_inicio'] = self.request.GET.get('inicio', '')
        ctx['f_fin'] = self.request.GET.get('fin', '')
        return ctx


# ═══════════════════════════════════════════════════════════════════
# VISUALIZADORES DE COTIZACIONES
# ═══════════════════════════════════════════════════════════════════

@login_required
@require_permission("divisas.view_cotizaciones_segmento", check_client_assignment=False)
def visualizador_tasas(request):
    """
    🔐 PROTEGIDA: divisas.view_cotizaciones_segmento
    
    Muestra las tasas de cambio actuales filtradas por el cliente activo en la sesión.
    Si no hay cliente activo, usa el segmento 'general'.
    Solo muestra divisas que tienen cotizaciones para el segmento activo.
    """
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

        # 🔹 SOLO agregar si hay cotizaciones para este segmento
        if cotizaciones_segmento:
            divisas_data.append({
                "divisa": divisa,
                "cotizaciones": cotizaciones_segmento
            })

    return render(request, "visualizador.html", {
        "divisas_data": divisas_data,
        "segmento_activo": segmento_activo
    })


@login_required
@require_permission("divisas.manage_cotizaciones_segmento", check_client_assignment=False)
def visualizador_tasas_admin(request):
    """
    🔐 PROTEGIDA: divisas.manage_cotizaciones_segmento
    
    Vista administrativa que muestra todas las cotizaciones de todos los segmentos.
    Solo accesible para usuarios con permiso de gestión de cotizaciones.
    
    NOTA: Reemplaza @user_passes_test(is_admin_or_staff) por permiso granular.
    """
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


# ═══════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════════════

def redondear(valor, decimales=2):
    """
    Redondea un valor decimal con la cantidad de decimales especificada.
    """
    try:
        return Decimal(valor).quantize(
            Decimal("1") if decimales == 0 else Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
    except Exception:
        return valor
