"""
Vistas para gestión de descuentos.
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView
from django.urls import reverse_lazy

from clientes.models import Descuento, HistorialDescuentos, Segmento
from clientes.forms import DescuentoForm


@method_decorator(login_required, name='dispatch')
class DescuentoListView(UserPassesTestMixin, ListView):
    model = Descuento
    template_name = 'descuentos/lista_descuentos.html'
    context_object_name = 'descuentos'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_queryset(self):
        for segmento in Segmento.objects.all():
            Descuento.objects.get_or_create(
                segmento=segmento,
                defaults={'porcentaje_descuento': 0.00, 'modificado_por': self.request.user}
            )
        return Descuento.objects.all()


@method_decorator(login_required, name='dispatch')
class DescuentoUpdateView(UserPassesTestMixin, UpdateView):
    model = Descuento
    form_class = DescuentoForm
    template_name = 'descuentos/editar_descuento.html'
    success_url = reverse_lazy('clientes:lista_descuentos')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

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
class HistorialDescuentoListView(UserPassesTestMixin, ListView):
    model = HistorialDescuentos
    template_name = 'descuentos/historial_descuentos.html'
    context_object_name = 'historial_descuentos'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser