"""
Vistas para la gestión de roles, grupos y permisos del sistema.
"""
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from .mixins import RoleRequiredMixin
from .forms import GroupForm
from .management.commands.permissions_defs import TODOS_LOS_PERMISOS
from .models import RoleStatus

User = get_user_model()


# ═══════════════════════════════════════════════════════════════════════════
# VISTAS DE GRUPOS
# ═══════════════════════════════════════════════════════════════════════════

class GroupListView(RoleRequiredMixin, ListView):
    """
    Lista todos los grupos/roles del sistema con información de permisos y usuarios.
    """
    model = Group
    template_name = 'groups/group_list.html'
    context_object_name = 'groups'
    required_role = 'admin'
    
    def get_queryset(self):
        """Obtiene grupos con contadores de permisos y usuarios"""
        return Group.objects.annotate(
            num_permissions=Count('permissions', distinct=True),
            num_users=Count('user', distinct=True)
        ).order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_groups'] = self.get_queryset().count()
        return context


class GroupDetailView(RoleRequiredMixin, DetailView):
    """
    Muestra los detalles de un grupo/rol específico.
    """
    model = Group
    template_name = 'groups/group_detail.html'
    context_object_name = 'group'
    required_role = 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        
        # Obtener usuarios del grupo
        context['users'] = group.user_set.all()
        
        # Obtener permisos agrupados por app
        permissions = group.permissions.select_related('content_type').all()
        permissions_by_app = {}
        
        for perm in permissions:
            app_label = perm.content_type.app_label
            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = []
            permissions_by_app[app_label].append(perm)
        
        context['permissions_by_app'] = dict(sorted(permissions_by_app.items()))
        context['total_permissions'] = permissions.count()
        context['total_users'] = context['users'].count()
        
        return context


class GroupCreateView(RoleRequiredMixin, CreateView):
    """
    Crea un nuevo grupo/rol en el sistema.
    """
    model = Group
    form_class = GroupForm
    template_name = 'groups/group_form.html'
    success_url = reverse_lazy('group_list')
    required_role = 'admin'
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Rol "{form.instance.name}" creado exitosamente.'
        )
        return super().form_valid(form)


class GroupUpdateView(RoleRequiredMixin, UpdateView):
    """
    Actualiza la información básica de un grupo/rol.
    """
    model = Group
    form_class = GroupForm
    template_name = 'groups/group_form.html'
    success_url = reverse_lazy('group_list')
    required_role = 'admin'
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Rol "{form.instance.name}" actualizado exitosamente.'
        )
        return super().form_valid(form)


class GroupDeleteView(RoleRequiredMixin, DeleteView):
    """
    Elimina un grupo/rol del sistema (con confirmación).
    """
    model = Group
    template_name = 'groups/group_confirm_delete.html'
    success_url = reverse_lazy('group_list')
    required_role = 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        context['users_count'] = group.user_set.count()
        context['permissions_count'] = group.permissions.count()
        return context
    
    def delete(self, request, *args, **kwargs):
        group_name = self.get_object().name
        messages.success(
            request,
            f'Rol "{group_name}" eliminado exitosamente.'
        )
        return super().delete(request, *args, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# GESTIÓN DE PERMISOS
# ═══════════════════════════════════════════════════════════════════════════

class GroupDetailPermissionsView(RoleRequiredMixin, UpdateView):
    """
    Vista para gestionar permisos de un grupo con metadata enriquecida.
    """
    model = Group
    template_name = 'groups/group_detail_permissions.html'
    fields = []
    required_role = 'admin'
    
    def get_success_url(self):
        return reverse_lazy('group_detail_permissions', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        
        # ═══════════════════════════════════════════════════════
        # 1. PERMISOS ACTUALES CON METADATA
        # ═══════════════════════════════════════════════════════
        current_permissions = []
        for perm in group.permissions.select_related('content_type').all():
            metadata = self._get_permission_metadata(perm.codename)
            perm_data = {
                'id': perm.id,
                'name': perm.name,
                'codename': perm.codename,
                'content_type': perm.content_type,
                'app_label': perm.content_type.app_label,
                'metadata': metadata
            }
            current_permissions.append(perm_data)
        
        context['current_permissions'] = sorted(
            current_permissions,
            key=lambda x: (x['app_label'], x['name'])
        )
        
        # ═══════════════════════════════════════════════════════
        # 2. PERMISOS AGRUPADOS POR MÓDULO
        # ═══════════════════════════════════════════════════════
        permisos_por_modulo = self._agrupar_permisos_por_modulo()
        context['permisos_por_modulo'] = permisos_por_modulo
        
        # ═══════════════════════════════════════════════════════
        # 3. ESTADÍSTICAS
        # ═══════════════════════════════════════════════════════
        context['total_permisos_disponibles'] = sum(
            len(info['permisos']) for info in permisos_por_modulo.values()
        )
        context['total_permisos_asignados'] = len(current_permissions)
        
        return context
    
    def _get_permission_metadata(self, codename):
        """
        Obtiene metadata enriquecida de un permiso personalizado.
        """
        for perm_def in TODOS_LOS_PERMISOS:
            if perm_def['codename'] == codename:
                return {
                    'descripcion_detallada': perm_def.get('descripcion', ''),
                    'ejemplo_uso': perm_def.get('ejemplo', ''),
                    'nivel_riesgo': perm_def.get('nivel_riesgo', 'medio'),
                    'nivel_riesgo_display': self._get_nivel_riesgo_display(
                        perm_def.get('nivel_riesgo', 'medio')
                    ),
                    'nivel_riesgo_badge': self._get_nivel_riesgo_badge(
                        perm_def.get('nivel_riesgo', 'medio')
                    ),
                    'modulo': perm_def.get('modulo', ''),
                    'categoria': perm_def.get('categoria', ''),
                }
        return None
    
    def _get_nivel_riesgo_display(self, nivel):
        """Convierte nivel de riesgo a texto legible"""
        niveles = {
            'bajo': 'Bajo',
            'medio': 'Medio',
            'alto': 'Alto',
            'critico': 'Crítico',
        }
        return niveles.get(nivel, 'Medio')
    
    def _get_nivel_riesgo_badge(self, nivel):
        """Obtiene clase CSS para badge de nivel de riesgo"""
        badges = {
            'bajo': 'success',
            'medio': 'info',
            'alto': 'warning',
            'critico': 'danger',
        }
        return badges.get(nivel, 'info')
    
    def _agrupar_permisos_por_modulo(self):
        """
        Agrupa todos los permisos disponibles por módulo con metadata.
        """
        modulos = {}
        
        # Obtener todos los permisos del sistema
        all_permissions = Permission.objects.select_related('content_type').all()
        
        for perm in all_permissions:
            app_label = perm.content_type.app_label
            
            # Filtrar solo apps relevantes
            if app_label not in ['clientes', 'divisas', 'transacciones', 'medios_pago', 'users', 'auth']:
                continue
            
            # Obtener metadata
            metadata = self._get_permission_metadata(perm.codename)
            modulo_nombre = metadata['modulo'] if metadata else app_label
            
            # Inicializar módulo si no existe
            if modulo_nombre not in modulos:
                modulos[modulo_nombre] = {
                    'nombre': self._get_modulo_display_name(modulo_nombre),
                    'permisos': []
                }
            
            # Agregar permiso al módulo
            perm_data = {
                'id': perm.id,
                'nombre': perm.name,
                'codename': perm.codename,
                'descripcion': metadata['descripcion_detallada'] if metadata else '',
                'ejemplo': metadata['ejemplo_uso'] if metadata else '',
                'nivel_riesgo_display': metadata['nivel_riesgo_display'] if metadata else 'Medio',
                'nivel_riesgo_badge': metadata['nivel_riesgo_badge'] if metadata else 'info',
                'app_label': app_label,
                'es_personalizado': bool(metadata),
            }
            
            modulos[modulo_nombre]['permisos'].append(perm_data)
        
        # Ordenar permisos dentro de cada módulo
        for modulo in modulos.values():
            modulo['permisos'].sort(key=lambda x: x['nombre'])
        
        return dict(sorted(modulos.items()))
    
    def _get_modulo_display_name(self, modulo):
        """Obtiene el nombre legible del módulo"""
        nombres = {
            'clientes': 'Clientes',
            'divisas': 'Divisas',
            'transacciones': 'Transacciones',
            'medios_pago': 'Medios de Pago',
            'users': 'Usuarios',
            'usuarios': 'Usuarios',
            'configuracion': 'Configuración',
            'auth': 'Autenticación',
        }
        return nombres.get(modulo, modulo.capitalize())
    
    def post(self, request, *args, **kwargs):
        """
        Procesa la actualización de permisos del grupo.
        """
        self.object = self.get_object()
        
        # Obtener IDs de permisos seleccionados
        permission_ids = request.POST.getlist('permissions')
        
        # Validar que sean IDs válidos
        try:
            permission_ids = [int(pid) for pid in permission_ids]
        except ValueError:
            messages.error(request, 'IDs de permisos inválidos.')
            return redirect(self.get_success_url())
        
        # Actualizar permisos del grupo
        permissions = Permission.objects.filter(id__in=permission_ids)
        self.object.permissions.set(permissions)
        
        messages.success(
            request,
            f'✅ Permisos del rol "{self.object.name}" actualizados correctamente. '
            f'Total de permisos asignados: {permissions.count()}'
        )
        
        return redirect(self.get_success_url())


class SearchPermissionsView(LoginRequiredMixin, View):
    """
    API para buscar permisos con metadata enriquecida.
    """
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse([], safe=False)
        
        # Buscar permisos que coincidan
        permissions = Permission.objects.filter(
            Q(name__icontains=query) |
            Q(codename__icontains=query) |
            Q(content_type__app_label__icontains=query)
        ).select_related('content_type')[:20]
        
        results = []
        for perm in permissions:
            # Obtener metadata
            metadata = self._get_permission_metadata(perm.codename)
            
            results.append({
                'id': perm.id,
                'name': perm.name,
                'codename': perm.codename,
                'app_label': perm.content_type.app_label,
                'descripcion': metadata['descripcion_detallada'] if metadata else '',
                'ejemplo': metadata['ejemplo_uso'] if metadata else '',
                'modulo': metadata['modulo'] if metadata else perm.content_type.app_label,
                'nivel_riesgo_display': metadata['nivel_riesgo_display'] if metadata else 'Medio',
                'nivel_riesgo_badge': metadata['nivel_riesgo_badge'] if metadata else 'info',
            })
        
        return JsonResponse(results, safe=False)
    
    def _get_permission_metadata(self, codename):
        """Obtiene metadata de un permiso personalizado"""
        for perm_def in TODOS_LOS_PERMISOS:
            if perm_def['codename'] == codename:
                return {
                    'descripcion_detallada': perm_def.get('descripcion', ''),
                    'ejemplo_uso': perm_def.get('ejemplo', ''),
                    'nivel_riesgo': perm_def.get('nivel_riesgo', 'medio'),
                    'nivel_riesgo_display': self._get_nivel_riesgo_display(
                        perm_def.get('nivel_riesgo', 'medio')
                    ),
                    'nivel_riesgo_badge': self._get_nivel_riesgo_badge(
                        perm_def.get('nivel_riesgo', 'medio')
                    ),
                    'modulo': perm_def.get('modulo', ''),
                    'categoria': perm_def.get('categoria', ''),
                }
        return None
    
    def _get_nivel_riesgo_display(self, nivel):
        """Convierte nivel de riesgo a texto legible"""
        niveles = {
            'bajo': 'Bajo',
            'medio': 'Medio',
            'alto': 'Alto',
            'critico': 'Crítico',
        }
        return niveles.get(nivel, 'Medio')
    
    def _get_nivel_riesgo_badge(self, nivel):
        """Obtiene clase CSS para badge de nivel de riesgo"""
        badges = {
            'bajo': 'success',
            'medio': 'info',
            'alto': 'warning',
            'critico': 'danger',
        }
        return badges.get(nivel, 'info')


# ═══════════════════════════════════════════════════════════════════════════
# GESTIÓN DE USUARIOS EN GRUPOS
# ═══════════════════════════════════════════════════════════════════════════

class GroupDetailUsersView(RoleRequiredMixin, DetailView):
    """
    Vista para gestionar usuarios asignados a un grupo.
    """
    model = Group
    template_name = 'groups/group_detail_users.html'
    context_object_name = 'group'
    required_role = 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        
        # Usuarios actuales del grupo
        context['current_users'] = group.user_set.all().order_by('username')
        
        # Usuarios disponibles para agregar (que NO están en el grupo)
        context['available_users'] = User.objects.exclude(
            groups=group
        ).order_by('username')
        
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Procesa la adición/eliminación de usuarios del grupo.
        """
        self.object = self.get_object()
        action = request.POST.get('action')
        
        if action == 'add':
            user_ids = request.POST.getlist('users')
            users = User.objects.filter(id__in=user_ids)
            self.object.user_set.add(*users)
            messages.success(
                request,
                f'{users.count()} usuario(s) agregado(s) al rol "{self.object.name}".'
            )
        
        elif action == 'remove':
            user_ids = request.POST.getlist('users')
            users = User.objects.filter(id__in=user_ids)
            self.object.user_set.remove(*users)
            messages.success(
                request,
                f'{users.count()} usuario(s) eliminado(s) del rol "{self.object.name}".'
            )
        
        return redirect('group_detail_users', pk=self.object.pk)


# ═══════════════════════════════════════════════════════════════════════════
# MATRIZ DE PERMISOS
# ═══════════════════════════════════════════════════════════════════════════

class PermissionMatrixView(RoleRequiredMixin, ListView):
    """
    Muestra una matriz comparativa de permisos entre todos los roles.
    """
    model = Group
    template_name = 'permissions/permission_matrix.html'
    context_object_name = 'groups'
    required_role = 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener todos los grupos
        groups = self.get_queryset()
        
        # Obtener todos los permisos relevantes
        all_permissions = Permission.objects.filter(
            content_type__app_label__in=[
                'clientes', 'divisas', 'transacciones', 'medios_pago', 'users', 'auth'
            ]
        ).select_related('content_type').order_by(
            'content_type__app_label', 'name'
        )
        
        # Crear matriz de permisos
        permission_matrix = []
        for perm in all_permissions:
            row = {
                'permission': perm,
                'app_label': perm.content_type.app_label,
                'groups': {}
            }
            for group in groups:
                row['groups'][group.id] = group.permissions.filter(id=perm.id).exists()
            permission_matrix.append(row)
        
        context['permission_matrix'] = permission_matrix
        context['apps'] = list(set(
            perm.content_type.app_label for perm in all_permissions
        ))
        
        return context


class GroupToggleStatusView(RoleRequiredMixin, View):
    """Activa/desactiva un rol."""
    required_role = 'admin'

    def post(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        status, _ = RoleStatus.objects.get_or_create(group=group)
        status.is_active = not status.is_active
        status.save()

        estado = "activado" if status.is_active else "desactivado"
        messages.success(request, f'Rol "{group.name}" {estado} correctamente.')
        return redirect('group_list')