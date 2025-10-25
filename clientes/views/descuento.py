"""
Vistas para gestión de descuentos.
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView
from django.urls import reverse_lazy

from clientes.models import Descuento, HistorialDescuentos, Segmento
from clientes.forms import DescuentoForm
from roles.decorators import require_permission


@method_decorator(login_required, name='dispatch')
@method_decorator(require_permission("clientes.view_descuentos_segmento", check_client_assignment=False), name='dispatch')
class DescuentoListView(LoginRequiredMixin, ListView):
    model = Descuento
    template_name = 'descuentos/lista_descuentos.html'
    context_object_name = 'descuentos'

    def get_queryset(self):
        for segmento in Segmento.objects.all():
            Descuento.objects.get_or_create(
                segmento=segmento,
                defaults={'porcentaje_descuento': 0.00, 'modificado_por': self.request.user}
            )
        return Descuento.objects.all()


@method_decorator(login_required, name='dispatch')
@method_decorator(require_permission("clientes.manage_descuentos_segmento", check_client_assignment=False), name='dispatch')
class DescuentoUpdateView(LoginRequiredMixin, UpdateView):
    model = Descuento
    form_class = DescuentoForm
    template_name = 'descuentos/editar_descuento.html'
    success_url = reverse_lazy('clientes:lista_descuentos')

    def form_valid(self, form):
        anterior_descuento = self.get_object().porcentaje_descuento
        response = super().form_valid(form)

        if anterior_descuento != self.object.porcentaje_descuento:
            HistorialDescuentos.objects.create(
                descuento=self.object,
                porcentaje_descuento_anterior=anterior_descuento,
                porcentaje_descuento_nuevo=self.object.porcentaje_descuento,
                modificado_por=self.request.user
            )

        return response


@method_decorator(login_required, name='dispatch')
@method_decorator(require_permission("clientes.view_historial_descuentos", check_client_assignment=False), name='dispatch')
class HistorialDescuentoListView(LoginRequiredMixin, ListView):
    model = HistorialDescuentos
    template_name = 'descuentos/historial_descuentos.html'
    context_object_name = 'historial_descuentos'