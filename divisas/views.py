from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Divisa, TasaCambio
from .forms import DivisaForm, TasaCambioForm
import datetime
from django.db.models import Max
from django.db.models import OuterRef, Subquery


# ----------------------------
# DIVISAS
# ----------------------------
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
    permission_required = 'divisas.change_divisa'

    def post(self, request, pk):
        divisa = get_object_or_404(Divisa, pk=pk)
        divisa.is_active = not divisa.is_active
        divisa.save()
        return redirect('divisas:lista')


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
        qs = TasaCambio.objects.filter(divisa_id=divisa_id).order_by('fecha')

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
    Crear tasa para UNA divisa.
    """
    permission_required = 'divisas.add_tasacambio'
    model = TasaCambio
    form_class = TasaCambioForm
    template_name = 'divisas/tasa_form.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['fecha'] = datetime.date.today()
        return initial

    def get_success_url(self):
        return reverse_lazy('divisas:tasas', kwargs={'divisa_id': self.kwargs['divisa_id']})

    def form_valid(self, form):
        divisa = get_object_or_404(Divisa, pk=self.kwargs['divisa_id'])
        tasa = form.save(commit=False)
        tasa.divisa = divisa
        tasa.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['divisa'] = get_object_or_404(Divisa, pk=self.kwargs['divisa_id'])
        return ctx


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
    latest = TasaCambio.objects.filter(divisa=OuterRef('pk')).order_by('-fecha')

    divisas = (
        Divisa.objects
        .filter(is_active=True)
        .annotate(
            ultima_fecha=Subquery(latest.values('fecha')[:1]),
            ultima_compra=Subquery(latest.values('valor_compra')[:1]),
            ultima_venta=Subquery(latest.values('valor_venta')[:1]),
        )
        .order_by('code')
    )

    return render(request, 'visualizador.html', {'divisas': divisas})