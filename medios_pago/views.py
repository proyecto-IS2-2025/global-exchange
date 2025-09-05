from django.shortcuts import render

# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy

from .models import MedioDePago
from .forms import MedioDePagoForm


class MedioDePagoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'medios_pago.view_mediodepago'
    model = MedioDePago
    template_name = 'medios_pago/lista.html'
    context_object_name = 'medios_pago'
    paginate_by = 20


class MedioDePagoCreateAdminView(LoginRequiredMixin,PermissionRequiredMixin, CreateView):
    permission_required = 'medios_pago.view_mediodepago'
    model = MedioDePago
    form_class = MedioDePagoForm
    template_name = 'medios_pago/form.html'
    success_url = reverse_lazy('medios_pago:lista')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.is_active = False  # Nace deshabilitado por defecto
        obj.save()
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Crear'
        return ctx

class MedioDePagoCreateView(LoginRequiredMixin, CreateView):
    model = MedioDePago
    form_class = MedioDePagoForm
    template_name = 'medios_pago/seleccionar_medio_pago_crear.html'
    success_url = reverse_lazy('inicio')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.is_active = False  # Nace deshabilitado por defecto
        obj.save()
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Crear'
        return ctx

class ChequeFormView(LoginRequiredMixin, CreateView):
    model = MedioDePago
    form_class = MedioDePagoForm
    template_name = 'medios_pago/cheque_form.html'
    success_url = reverse_lazy('medios_pago:seleccionar_medio_pago_crear.html')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.is_active = False  # Nace deshabilitado por defecto
        obj.save()
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Crear-Cheque'
        return ctx

class MedioDePagoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'medios_pago.change_mediodepago'
    model = MedioDePago
    form_class = MedioDePagoForm
    template_name = 'medios_pago/form.html'
    success_url = reverse_lazy('medios_pago:lista')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Editar'
        return ctx


class MedioDePagoToggleActivoView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'medios_pago.change_mediodepago'

    def post(self, request, pk):
        medio_de_pago = get_object_or_404(MedioDePago, pk=pk)
        medio_de_pago.is_active = not medio_de_pago.is_active
        medio_de_pago.save()
        return redirect('medios_pago:lista')