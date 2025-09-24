# views.py - Versión con templates dinámicos
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json

from .models import MedioDePago, CampoMedioDePago, PaymentTemplate
from .forms import MedioDePagoForm, create_campo_formset


class MedioDePagoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista de listado para los Medios de Pago con filtros por estado.
    """
    permission_required = 'medios_pago.view_mediodepago'
    model = MedioDePago
    template_name = 'medios_pago/lista.html'
    context_object_name = 'medios_pago'
    paginate_by = 20

    def get_queryset(self):
        queryset = MedioDePago.objects.all()
        estado_filtro = self.request.GET.get('estado', 'todos')
        
        if estado_filtro == 'activos':
            queryset = queryset.filter(is_active=True)
        elif estado_filtro == 'inactivos':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        estado_actual = self.request.GET.get('estado', 'todos')
        context['estado_filtro'] = estado_actual
        
        total_medios = MedioDePago.objects.count()
        medios_activos = MedioDePago.objects.filter(is_active=True).count()
        medios_inactivos = MedioDePago.objects.filter(is_active=False).count()
        
        context['stats'] = {
            'total': total_medios,
            'activos': medios_activos,
            'inactivos': medios_inactivos
        }
        
        context['filtros_disponibles'] = [
            {'value': 'todos', 'label': f'Todos ({total_medios})', 'active': estado_actual == 'todos'},
            {'value': 'activos', 'label': f'Activos ({medios_activos})', 'active': estado_actual == 'activos'},
            {'value': 'inactivos', 'label': f'Inactivos ({medios_inactivos})', 'active': estado_actual == 'inactivos'},
        ]
        
        return context


class MedioDePagoCreateAdminView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para la creación de un nuevo Medio de Pago con templates dinámicos.
    """
    permission_required = 'medios_pago.add_mediodepago'
    model = MedioDePago
    form_class = MedioDePagoForm
    template_name = 'medios_pago/form.html'
    success_url = reverse_lazy('medios_pago:lista')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Crear'
        ctx['is_edit'] = False
        ctx['can_edit_freely'] = True
        
        CampoFormSet = create_campo_formset(is_edit=False)
        
        if self.request.POST:
            ctx['campos_formset'] = CampoFormSet(
                self.request.POST,
                instance=None
            )
        else:
            ctx['campos_formset'] = CampoFormSet(
                instance=None
            )
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        
        CampoFormSet = create_campo_formset(is_edit=False)
        campos_formset = CampoFormSet(
            request.POST,
            instance=None
        )
        
        if form.is_valid() and campos_formset.is_valid():
            return self.form_valid(form, campos_formset)
        else:
            return self.form_invalid(form, campos_formset)

    def form_valid(self, form, campos_formset):
        """
        Guarda el medio de pago y sus campos asociados.
        También maneja la creación de templates personalizados.
        """
        try:
            with transaction.atomic():
                self.object = form.save()
                
                # Aplicar template si fue seleccionado (solo en creación)
                template_key = form.cleaned_data.get('aplicar_template')
                if template_key:
                    self.object.aplicar_template(template_key)
                    messages.info(self.request, f'Template aplicado automáticamente.')
                else:
                    # Si no hay template, guardar los campos del formset
                    campos_formset.instance = self.object
                    campos_formset.save()
                
                # Crear template personalizado si fue solicitado
                nuevo_template_nombre = form.cleaned_data.get('crear_template')
                if nuevo_template_nombre and nuevo_template_nombre.strip():
                    try:
                        template = self.object.create_template_from_current_fields(
                            nuevo_template_nombre.strip(),
                            created_by=self.request.user
                        )
                        messages.success(
                            self.request, 
                            f'Template "{template.name}" creado exitosamente y estará disponible para futuros medios de pago.'
                        )
                    except Exception as e:
                        messages.warning(
                            self.request,
                            f'El medio de pago se creó correctamente, pero hubo un error al crear el template: {str(e)}'
                        )
                
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
    """
    Vista para la edición de un Medio de Pago existente.
    """
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
        
        CampoFormSet = create_campo_formset(is_edit=True)
        
        if self.request.POST:
            campos_queryset = self.object.campos.all()
            ctx['campos_formset'] = CampoFormSet(
                self.request.POST,
                instance=self.object,
                queryset=campos_queryset
            )
        else:
            campos_queryset = self.object.campos.all()
            ctx['campos_formset'] = CampoFormSet(
                instance=self.object,
                queryset=campos_queryset
            )
        return ctx
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        
        CampoFormSet = create_campo_formset(is_edit=True)
        campos_formset = CampoFormSet(
            request.POST,
            instance=self.object,
            queryset=self.object.campos.all()
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
    """
    Vista para activar o desactivar un medio de pago.
    """
    permission_required = 'medios_pago.change_mediodepago'

    def post(self, request, pk):
        medio_de_pago = get_object_or_404(MedioDePago, pk=pk)
        estado_anterior = medio_de_pago.is_active
        medio_de_pago.toggle_active()
        
        estado = 'activado' if medio_de_pago.is_active else 'desactivado'
        messages.success(request, f'Medio de pago "{medio_de_pago.nombre}" {estado} exitosamente.')
        
        estado_filtro = request.GET.get('estado', 'todos')
        return redirect(f"{reverse_lazy('medios_pago:lista')}?estado={estado_filtro}")


class MedioDePagoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista para eliminación real (no soft delete) de un medio de pago.
    """
    permission_required = 'medios_pago.delete_mediodepago'

    def post(self, request, pk):
        medio_de_pago = get_object_or_404(MedioDePago, pk=pk)
        
        try:
            if hasattr(medio_de_pago, 'transacciones') and medio_de_pago.transacciones.exists():
                messages.error(request, f'No se puede eliminar "{medio_de_pago.nombre}" porque tiene transacciones asociadas.')
                return redirect('medios_pago:lista')
            
            nombre = medio_de_pago.nombre
            medio_de_pago.delete()
            messages.success(request, f'Medio de pago "{nombre}" eliminado exitosamente.')
            
        except Exception as e:
            messages.error(request, f'Error al eliminar el medio de pago: {str(e)}')
        
        return redirect('medios_pago:lista')


class TemplateDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista AJAX para obtener datos de un template específico.
    """
    permission_required = 'medios_pago.view_mediodepago'

    def get(self, request, template_key):
        try:
            all_templates = PaymentTemplate.get_all_templates()
            
            if template_key not in all_templates:
                return JsonResponse({'error': 'Template no encontrado'}, status=404)
            
            template_data = all_templates[template_key]
            
            return JsonResponse({
                'success': True,
                'name': template_data['name'],
                'fields': template_data['fields'],
                'is_custom': template_data.get('is_custom', False)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class DeleteTemplateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista AJAX para eliminar un template personalizado.
    """
    permission_required = 'medios_pago.delete_mediodepago'  # Usar el mismo permiso

    def post(self, request, template_key):
        try:
            # Verificar que sea un template personalizado
            if not template_key.startswith('custom_'):
                return JsonResponse({
                    'success': False,
                    'message': 'Solo se pueden eliminar templates personalizados'
                }, status=400)
            
            # Extraer el ID del template
            template_id = template_key.replace('custom_', '')
            
            try:
                template_id = int(template_id)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de template inválido'
                }, status=400)
            
            # Buscar y eliminar el template
            template = get_object_or_404(PaymentTemplate, pk=template_id)
            
            # Verificar que el usuario tenga permisos para eliminar este template
            # (opcional: solo el creador o superusuarios pueden eliminar)
            if not request.user.is_superuser and template.created_by != request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'No tienes permisos para eliminar este template'
                }, status=403)
            
            template_name = template.name
            template.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Template "{template_name}" eliminado exitosamente'
            })
            
        except PaymentTemplate.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Template no encontrado'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar el template: {str(e)}'
            }, status=500)


class TemplateListView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista AJAX para obtener la lista actualizada de templates.
    Útil para refrescar el selector después de crear/eliminar templates.
    """
    permission_required = 'medios_pago.view_mediodepago'

    def get(self, request):
        try:
            all_templates = PaymentTemplate.get_all_templates()
            
            templates_list = []
            for key, template in all_templates.items():
                templates_list.append({
                    'key': key,
                    'name': template['name'],
                    'is_custom': template.get('is_custom', False),
                    'field_count': len(template['fields'])
                })
            
            return JsonResponse({
                'success': True,
                'templates': templates_list
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)