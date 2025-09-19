# views.py - Versión con filtros por estado en lugar de soft delete
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
from .forms import MedioDePagoForm, create_campo_formset


class MedioDePagoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista de listado para los Medios de Pago con filtros por estado.
    
    Requiere el permiso 'medios_pago.view_mediodepago'.
    Permite filtrar por: todos, activos, inactivos.
    """
    permission_required = 'medios_pago.view_mediodepago'
    model = MedioDePago
    template_name = 'medios_pago/lista.html'
    context_object_name = 'medios_pago'
    paginate_by = 20

    def get_queryset(self):
        """
        Devuelve el queryset filtrado según el parámetro 'estado'.
        """
        # Obtener todos los medios (sin soft delete)
        queryset = MedioDePago.objects.all()
        
        # Aplicar filtro según el parámetro GET
        estado_filtro = self.request.GET.get('estado', 'todos')
        
        if estado_filtro == 'activos':
            queryset = queryset.filter(is_active=True)
        elif estado_filtro == 'inactivos':
            queryset = queryset.filter(is_active=False)
        # 'todos' no aplica filtro adicional
        
        return queryset.order_by('nombre')

    def get_context_data(self, **kwargs):
        """
        Añade información del filtro actual al contexto.
        """
        context = super().get_context_data(**kwargs)
        
        # Estado del filtro actual
        estado_actual = self.request.GET.get('estado', 'todos')
        context['estado_filtro'] = estado_actual
        
        # Estadísticas para mostrar en la interfaz
        total_medios = MedioDePago.objects.count()
        medios_activos = MedioDePago.objects.filter(is_active=True).count()
        medios_inactivos = MedioDePago.objects.filter(is_active=False).count()
        
        context['stats'] = {
            'total': total_medios,
            'activos': medios_activos,
            'inactivos': medios_inactivos
        }
        
        # Opciones del filtro
        context['filtros_disponibles'] = [
            {'value': 'todos', 'label': f'Todos ({total_medios})', 'active': estado_actual == 'todos'},
            {'value': 'activos', 'label': f'Activos ({medios_activos})', 'active': estado_actual == 'activos'},
            {'value': 'inactivos', 'label': f'Inactivos ({medios_inactivos})', 'active': estado_actual == 'inactivos'},
        ]
        
        return context


class MedioDePagoCreateAdminView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para la creación de un nuevo Medio de Pago.
    
    Requiere el permiso 'medios_pago.add_mediodepago'.
    Permite la creación de campos dinámicos a través de un formset.
    """
    permission_required = 'medios_pago.add_mediodepago'
    model = MedioDePago
    form_class = MedioDePagoForm
    template_name = 'medios_pago/form.html'
    success_url = reverse_lazy('medios_pago:lista')

    def get_context_data(self, **kwargs):
        """
        Añade el formset de campos al contexto.
        """
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Crear'
        ctx['is_edit'] = False
        ctx['can_edit_freely'] = True  # En creación siempre se puede editar todo
        
        # Usar factory para formset de creación (con extra=1)
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
        
        # Usar factory para formset de creación
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
        """
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
    """
    Vista para la edición de un Medio de Pago existente.
    
    Requiere el permiso 'medios_pago.change_mediodepago'.
    Permite la edición de campos dinámicos.
    """
    permission_required = 'medios_pago.change_mediodepago'
    model = MedioDePago
    form_class = MedioDePagoForm
    template_name = 'medios_pago/form.html'
    success_url = reverse_lazy('medios_pago:lista')

    def get_context_data(self, **kwargs):
        """
        Añade el formset de campos al contexto en modo edición.
        """
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Editar'
        ctx['is_edit'] = True
        ctx['can_edit_freely'] = self.object.can_be_edited_freely
        
        # Usar factory para formset de edición (con extra=0)
        CampoFormSet = create_campo_formset(is_edit=True)
        
        if self.request.POST:
            # Incluir todos los campos en el formset
            campos_queryset = self.object.campos.all()
            ctx['campos_formset'] = CampoFormSet(
                self.request.POST,
                instance=self.object,
                queryset=campos_queryset
            )
        else:
            # Mostrar todos los campos activos
            campos_queryset = self.object.campos.all()
            ctx['campos_formset'] = CampoFormSet(
                instance=self.object,
                queryset=campos_queryset
            )
        return ctx
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        
        # Usar factory para formset de edición
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
        """
        Guarda los cambios en el medio de pago y sus campos asociados.
        """
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
        
        # Mantener el filtro actual al redirigir
        estado_filtro = request.GET.get('estado', 'todos')
        return redirect(f"{reverse_lazy('medios_pago:lista')}?estado={estado_filtro}")


class MedioDePagoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista para eliminación real (no soft delete) de un medio de pago.
    Solo disponible si no tiene dependencias.
    """
    permission_required = 'medios_pago.delete_mediodepago'

    def post(self, request, pk):
        medio_de_pago = get_object_or_404(MedioDePago, pk=pk)
        
        try:
            # Verificar si se puede eliminar (lógica de negocio)
            if hasattr(medio_de_pago, 'transacciones') and medio_de_pago.transacciones.exists():
                messages.error(request, f'No se puede eliminar "{medio_de_pago.nombre}" porque tiene transacciones asociadas.')
                return redirect('medios_pago:lista')
            
            nombre = medio_de_pago.nombre
            medio_de_pago.delete()
            messages.success(request, f'Medio de pago "{nombre}" eliminado exitosamente.')
            
        except Exception as e:
            messages.error(request, f'Error al eliminar el medio de pago: {str(e)}')
        
        return redirect('medios_pago:lista')