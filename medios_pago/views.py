# views.py - REEMPLAZA TODO EL CONTENIDO
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.contrib import messages

from .models import MedioDePago, CampoMedioDePago
from .forms import MedioDePagoForm, CampoMedioDePagoFormSet


class MedioDePagoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'medios_pago.view_mediodepago'
    model = MedioDePago
    template_name = 'medios_pago/lista.html'
    context_object_name = 'medios_pago'
    paginate_by = 20


class MedioDePagoCreateAdminView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'medios_pago.add_mediodepago'
    model = MedioDePago
    form_class = MedioDePagoForm
    template_name = 'medios_pago/form.html'
    success_url = reverse_lazy('medios_pago:lista')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Crear'
        ctx['is_edit'] = False
        
        if self.request.POST:
            ctx['campos_formset'] = CampoMedioDePagoFormSet(
                self.request.POST,
                instance=None
            )
        else:
            ctx['campos_formset'] = CampoMedioDePagoFormSet(
                instance=None
            )
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        campos_formset = CampoMedioDePagoFormSet(
            request.POST,
            instance=None
        )
        
        if form.is_valid() and campos_formset.is_valid():
            return self.form_valid(form, campos_formset)
        else:
            return self.form_invalid(form, campos_formset)

    def form_valid(self, form, campos_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                campos_formset.instance = self.object
                campos_formset.save()
                
                messages.success(self.request, f'Medio de pago "{self.object.nombre}" creado exitosamente.')
                return redirect(self.success_url)
                
        except Exception as e:
            messages.error(self.request, f'Error al crear el medio de pago: {str(e)}')
            return self.form_invalid(form, campos_formset)

    def form_invalid(self, form, campos_formset):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return self.render_to_response(
            self.get_context_data(form=form, campos_formset=campos_formset)
        )


class MedioDePagoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'medios_pago.change_mediodepago'
    model = MedioDePago
    form_class = MedioDePagoForm
    template_name = 'medios_pago/form.html'
    success_url = reverse_lazy('medios_pago:lista')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Editar'
        ctx['is_edit'] = True
        
        if self.request.POST:
            ctx['campos_formset'] = CampoMedioDePagoFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            ctx['campos_formset'] = CampoMedioDePagoFormSet(
                instance=self.object
            )
        return ctx
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        campos_formset = CampoMedioDePagoFormSet(
            request.POST,
            instance=self.object
        )
        
        if form.is_valid() and campos_formset.is_valid():
            return self.form_valid(form, campos_formset)
        else:
            return self.form_invalid(form, campos_formset)

    def form_valid(self, form, campos_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                campos_formset.save()
                
                messages.success(self.request, f'Medio de pago "{self.object.nombre}" actualizado exitosamente.')
                return redirect(self.success_url)
                
        except Exception as e:
            messages.error(self.request, f'Error al actualizar el medio de pago: {str(e)}')
            return self.form_invalid(form, campos_formset)

    def form_invalid(self, form, campos_formset):
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return self.render_to_response(
            self.get_context_data(form=form, campos_formset=campos_formset)
        )


class MedioDePagoToggleActivoView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'medios_pago.change_mediodepago'

    def post(self, request, pk):
        medio_de_pago = get_object_or_404(MedioDePago, pk=pk)
        estado_anterior = medio_de_pago.is_active
        medio_de_pago.is_active = not medio_de_pago.is_active
        medio_de_pago.save()
        
        estado = 'activado' if medio_de_pago.is_active else 'desactivado'
        messages.success(request, f'Medio de pago "{medio_de_pago.nombre}" {estado} exitosamente.')
        
        return redirect('medios_pago:lista')