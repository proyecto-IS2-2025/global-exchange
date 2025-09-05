# views.py - Versión mejorada
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json

from .models import MedioDePago, CampoMedioDePago
from .forms import MedioDePagoForm, CampoMedioDePagoFormSet


class MedioDePagoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'medios_pago.view_mediodepago'
    model = MedioDePago
    template_name = 'medios_pago/lista.html'
    context_object_name = 'medios_pago'
    paginate_by = 20

    def get_queryset(self):
        # Mostrar solo medios activos (no eliminados)
        return MedioDePago.active.all()


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
        ctx['can_edit_freely'] = True  # En creación siempre se puede editar todo
        
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
        ctx['can_edit_freely'] = self.object.can_be_edited_freely
        
        if self.request.POST:
            # Incluir campos eliminados en el formset para mantener consistencia
            campos_queryset = self.object.campos.all()
            ctx['campos_formset'] = CampoMedioDePagoFormSet(
                self.request.POST,
                instance=self.object,
                queryset=campos_queryset
            )
        else:
            # Solo mostrar campos activos en la vista
            campos_queryset = self.object.campos.filter(deleted_at__isnull=True)
            ctx['campos_formset'] = CampoMedioDePagoFormSet(
                instance=self.object,
                queryset=campos_queryset
            )
        return ctx
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        
        # Manejar eliminación de campos via AJAX
        if request.headers.get('Content-Type') == 'application/json':
            return self.handle_ajax_field_delete(request)
        
        campos_formset = CampoMedioDePagoFormSet(
            request.POST,
            instance=self.object,
            queryset=self.object.campos.all()
        )
        
        if form.is_valid() and campos_formset.is_valid():
            return self.form_valid(form, campos_formset)
        else:
            return self.form_invalid(form, campos_formset)

    def handle_ajax_field_delete(self, request):
        """Manejar eliminación de campos via AJAX"""
        try:
            data = json.loads(request.body)
            field_id = data.get('field_id')
            
            if not field_id:
                return JsonResponse({'success': False, 'error': 'ID de campo requerido'})
            
            campo = get_object_or_404(CampoMedioDePago, id=field_id, medio_de_pago=self.object)
            
            if self.object.can_be_edited_freely:
                campo.soft_delete()
                return JsonResponse({'success': True, 'message': 'Campo eliminado exitosamente'})
            else:
                return JsonResponse({'success': False, 'error': 'No se puede eliminar este campo'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

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
        medio_de_pago = get_object_or_404(MedioDePago.active, pk=pk)
        estado_anterior = medio_de_pago.is_active
        medio_de_pago.is_active = not medio_de_pago.is_active
        medio_de_pago.save()
        
        estado = 'activado' if medio_de_pago.is_active else 'desactivado'
        messages.success(request, f'Medio de pago "{medio_de_pago.nombre}" {estado} exitosamente.')
        
        return redirect('medios_pago:lista')


class MedioDePagoSoftDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Vista para eliminación suave de medios de pago"""
    permission_required = 'medios_pago.delete_mediodepago'

    def post(self, request, pk):
        medio_de_pago = get_object_or_404(MedioDePago.active, pk=pk)
        
        # Verificar si se puede eliminar (lógica de negocio)
        # Por ejemplo, verificar si no tiene transacciones asociadas
        
        try:
            medio_de_pago.soft_delete()
            messages.success(request, f'Medio de pago "{medio_de_pago.nombre}" eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el medio de pago: {str(e)}')
        
        return redirect('medios_pago:lista')


@method_decorator(csrf_exempt, name='dispatch')
class CampoSoftDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Vista para eliminación suave de campos via AJAX"""
    permission_required = 'medios_pago.change_mediodepago'

    def post(self, request, medio_pk, campo_pk):
        try:
            medio = get_object_or_404(MedioDePago, pk=medio_pk)
            campo = get_object_or_404(CampoMedioDePago, pk=campo_pk, medio_de_pago=medio)
            
            if not medio.can_be_edited_freely:
                return JsonResponse({
                    'success': False, 
                    'error': 'No se pueden eliminar campos de este medio de pago'
                })
            
            campo.soft_delete()
            
            return JsonResponse({
                'success': True, 
                'message': f'Campo "{campo.nombre_campo}" eliminado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
# views.py - Agregar estas nuevas vistas

class MedioDePagoDeletedListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Vista para mostrar medios de pago eliminados (papelera)"""
    permission_required = 'medios_pago.view_mediodepago'
    model = MedioDePago
    template_name = 'medios_pago/papelera.html'
    context_object_name = 'medios_eliminados'
    paginate_by = 20

    def get_queryset(self):
        # Mostrar solo medios eliminados (soft delete)
        return MedioDePago.objects.filter(deleted_at__isnull=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_eliminados'] = self.get_queryset().count()
        return context


class MedioDePagoRestoreView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Vista para restaurar un medio de pago eliminado"""
    permission_required = 'medios_pago.change_mediodepago'

    def post(self, request, pk):
        medio_de_pago = get_object_or_404(MedioDePago.objects.filter(deleted_at__isnull=False), pk=pk)
        
        try:
            medio_de_pago.restore()
            messages.success(request, f'Medio de pago "{medio_de_pago.nombre}" restaurado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al restaurar el medio de pago: {str(e)}')
        
        return redirect('medios_pago:papelera')


class MedioDePagoHardDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Vista para eliminación permanente (solo para casos extremos)"""
    permission_required = 'medios_pago.delete_mediodepago'

    def post(self, request, pk):
        medio_de_pago = get_object_or_404(MedioDePago.objects.filter(deleted_at__isnull=False), pk=pk)
        
        try:
            nombre = medio_de_pago.nombre
            medio_de_pago.delete()  # Eliminación real de la BD
            messages.warning(request, f'Medio de pago "{nombre}" eliminado permanentemente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar permanentemente: {str(e)}')
        
        return redirect('medios_pago:papelera')