"""
Vistas para la gestión de roles, grupos y permisos del sistema.
REFACTORIZADO: Usa permisos personalizados en lugar de RoleRequiredMixin hardcoded.
"""
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied

from roles.decorators import require_permission
from .forms import GroupForm
from .management.commands.permissions_defs import TODOS_LOS_PERMISOS
from .models import RoleStatus

User = get_user_model()

# ═══════════════════════════════════════════════════════════════════
# GRUPOS PROTEGIDOS - NO SE PUEDEN MODIFICAR/ELIMINAR
# ═══════════════════════════════════════════════════════════════════
PROTECTED_GROUPS = ['administrador', 'dev', 'superuser']

# ═══════════════════════════════════════════════════════════════════
# VISTAS DE GRUPOS
# ═══════════════════════════════════════════════════════════════════

@method_decorator(
    require_permission("roles.view_roles_list", check_client_assignment=False),
    name="dispatch"
)
class GroupListView(LoginRequiredMixin, ListView):
    """
    🔒 PROTEGIDA: roles.view_roles_list
    
    Lista todos los grupos/roles del sistema con información de permisos y usuarios.
    """
    model = Group
    template_name = 'groups/group_list.html'
    context_object_name = 'groups'
    
    def get_queryset(self):
        """Obtiene grupos con contadores de permisos y usuarios"""
        return Group.objects.annotate(
            num_permissions=Count('permissions', distinct=True),
            num_users=Count('user', distinct=True)
        ).order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_groups'] = self.get_queryset().count()
        
        # Indicar si el usuario puede gestionar roles
        context['can_manage_roles'] = self.request.user.has_perm('roles.manage_roles')
        
        return context


@method_decorator(
    require_permission("roles.view_role_details", check_client_assignment=False),
    name="dispatch"
)
class GroupDetailView(LoginRequiredMixin, DetailView):
    """
    🔒 PROTEGIDA: roles.view_role_details
    
    Muestra los detalles de un grupo/rol específico.
    """
    model = Group
    template_name = 'groups/group_detail.html'
    context_object_name = 'group'
    
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
        
        # Permisos del usuario actual
        context['can_edit_role'] = self.request.user.has_perm('roles.manage_roles')
        context['can_manage_permissions'] = self.request.user.has_perm('roles.manage_group_permissions')
        context['can_manage_users'] = self.request.user.has_perm('roles.manage_group_users')
        
        return context


@method_decorator(
    require_permission("roles.manage_roles", check_client_assignment=False),
    name="dispatch"
)
class GroupCreateView(LoginRequiredMixin, CreateView):
    """
    🔒 PROTEGIDA: roles.manage_roles
    
    Crea un nuevo grupo/rol en el sistema.
    """
    model = Group
    form_class = GroupForm
    template_name = 'groups/group_form.html'
    success_url = reverse_lazy('group_list')
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'✅ Rol "{form.instance.name}" creado exitosamente.'
        )
        return super().form_valid(form)


@method_decorator(
    require_permission("roles.manage_roles", check_client_assignment=False),
    name="dispatch"
)
class GroupUpdateView(LoginRequiredMixin, UpdateView):
    """
    🔒 PROTEGIDA: roles.manage_roles
    
    Actualiza la información básica de un grupo/rol.
    """
    model = Group
    form_class = GroupForm
    template_name = 'groups/group_form.html'
    success_url = reverse_lazy('group_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Validar que el grupo no esté protegido"""
        self.object = self.get_object()
        
        if self.object.name in PROTECTED_GROUPS:
            messages.error(
                request,
                f'❌ El rol "{self.object.name}" está protegido y no se puede modificar.'
            )
            return redirect('group_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'✅ Rol "{form.instance.name}" actualizado exitosamente.'
        )
        return super().form_valid(form)


@method_decorator(
    require_permission("roles.manage_roles", check_client_assignment=False),
    name="dispatch"
)
class GroupDeleteView(LoginRequiredMixin, DeleteView):
    """
    🔒 PROTEGIDA: roles.manage_roles
    
    Elimina un grupo/rol del sistema (con confirmación).
    """
    model = Group
    template_name = 'groups/group_confirm_delete.html'
    success_url = reverse_lazy('group_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Validar que el grupo no esté protegido"""
        self.object = self.get_object()
        
        if self.object.name in PROTECTED_GROUPS:
            messages.error(
                request,
                f'❌ El rol "{self.object.name}" está protegido y no se puede eliminar.'
            )
            return redirect('group_list')
        
        return super().dispatch(request, *args, **kwargs)
    
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
            f'✅ Rol "{group_name}" eliminado exitosamente.'
        )
        return super().delete(request, *args, **kwargs)


# ═══════════════════════════════════════════════════════════════════
# GESTIÓN DE PERMISOS
# ═══════════════════════════════════════════════════════════════════

@method_decorator(
    require_permission("roles.manage_group_permissions", check_client_assignment=False),
    name="dispatch"
)
class GroupDetailPermissionsView(LoginRequiredMixin, UpdateView):
    """
    🔒 PROTEGIDA: roles.manage_group_permissions
    
    Vista para gestionar permisos de un grupo con metadata enriquecida.
    """
    model = Group
    template_name = 'groups/group_detail_permissions.html'
    fields = []
    
    def get_success_url(self):
        return reverse_lazy('group_detail_permissions', kwargs={'pk': self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        """Validar que el usuario no modifique permisos de sus propios grupos"""
        self.object = self.get_object()
        
        # SEGURIDAD: Evitar escalación de privilegios
        if request.user.groups.filter(pk=self.object.pk).exists():
            messages.error(
                request,
                '❌ No puedes modificar los permisos de un grupo al que perteneces. '
                'Solicita a otro administrador que lo haga.'
            )
            return redirect('group_list')
        
        # SEGURIDAD: Proteger grupos críticos
        if self.object.name in PROTECTED_GROUPS and not request.user.is_superuser:
            messages.error(
                request,
                f'❌ El rol "{self.object.name}" está protegido. '
                'Solo superusuarios pueden modificar sus permisos.'
            )
            return redirect('group_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        
        # ═══════════════════════════════════════════════════════════════
        # 1. PERMISOS ACTUALES CON METADATA
        # ═══════════════════════════════════════════════════════════════
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
        
        # ═══════════════════════════════════════════════════════════════
        # 2. PERMISOS AGRUPADOS POR MÓDULO
        # ═══════════════════════════════════════════════════════════════
        permisos_por_modulo = self._agrupar_permisos_por_modulo()
        context['permisos_por_modulo'] = permisos_por_modulo
        
        # ═══════════════════════════════════════════════════════════════
        # 3. ESTADÍSTICAS
        # ═══════════════════════════════════════════════════════════════
        context['total_permisos_disponibles'] = sum(
            len(info['permisos']) for info in permisos_por_modulo.values()
        )
        context['total_permisos_asignados'] = len(current_permissions)
        
        # Indicar si el grupo está protegido
        context['is_protected_group'] = group.name in PROTECTED_GROUPS
        
        return context
    
    def _get_permission_metadata(self, codename):
        """Obtiene metadata enriquecida de un permiso personalizado"""
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
        Agrupa SOLO permisos personalizados por módulo con metadata.
        Los permisos nativos de Django son ignorados.
        """
        modulos = {}
        
        # Crear set de codenames custom para filtrado rápido
        codenames_custom = {perm_def['codename'] for perm_def in TODOS_LOS_PERMISOS}
        
        # Obtener todos los permisos del sistema
        all_permissions = Permission.objects.select_related('content_type').all()
        
        for perm in all_permissions:
            app_label = perm.content_type.app_label
            
            # FILTRO 1: Solo apps relevantes (incluyendo 'roles' ahora)
            if app_label not in ['clientes', 'divisas', 'transacciones', 'medios_pago', 'users', 'mfa', 'roles']:
                continue
            
            # FILTRO 2: Solo permisos custom (ignorar nativos)
            if perm.codename not in codenames_custom:
                continue
            
            # Obtener metadata
            metadata = self._get_permission_metadata(perm.codename)
            
            # Usar módulo de metadata en lugar de app_label
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
                'descripcion': metadata['descripcion_detallada'],
                'ejemplo': metadata['ejemplo_uso'],
                'nivel_riesgo_display': metadata['nivel_riesgo_display'],
                'nivel_riesgo_badge': metadata['nivel_riesgo_badge'],
                'app_label': app_label,
                'es_personalizado': True,
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
            'mfa': 'Autenticación MFA',
            'roles': 'Roles y Permisos',  # ← NUEVO
            'usuarios': 'Usuarios',
            'configuracion': 'Configuración',
            'auth': 'Autenticación',
        }
        return nombres.get(modulo, modulo.capitalize())
    
    def post(self, request, *args, **kwargs):
        """Procesa la actualización de permisos del grupo"""
        self.object = self.get_object()
        
        # Validar que no se modifiquen los propios grupos (seguridad redundante)
        if request.user.groups.filter(pk=self.object.pk).exists():
            messages.error(request, '❌ No puedes modificar permisos de tus propios grupos.')
            return redirect(self.get_success_url())
        
        # Obtener IDs de permisos seleccionados
        permission_ids = request.POST.getlist('permissions')
        
        # Validar que sean IDs válidos
        try:
            permission_ids = [int(pid) for pid in permission_ids]
        except ValueError:
            messages.error(request, '❌ IDs de permisos inválidos.')
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


@method_decorator(
    require_permission("roles.view_group_permissions", check_client_assignment=False),
    name="dispatch"
)
class SearchPermissionsView(LoginRequiredMixin, View):
    """
    🔒 PROTEGIDA: roles.view_group_permissions
    
    API para buscar permisos con metadata enriquecida.
    """
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse([], safe=False)
        
        # Crear set de codenames custom
        codenames_custom = {perm_def['codename'] for perm_def in TODOS_LOS_PERMISOS}
        
        # Buscar permisos que coincidan
        permissions = Permission.objects.filter(
            Q(name__icontains=query) |
            Q(codename__icontains=query) |
            Q(content_type__app_label__icontains=query)
        ).select_related('content_type')[:50]
        
        results = []
        for perm in permissions:
            # FILTRO: Solo permisos custom
            if perm.codename not in codenames_custom:
                continue
            
            # Obtener metadata
            metadata = self._get_permission_metadata(perm.codename)
            
            results.append({
                'id': perm.id,
                'name': perm.name,
                'codename': perm.codename,
                'app_label': perm.content_type.app_label,
                'descripcion': metadata['descripcion_detallada'],
                'ejemplo': metadata['ejemplo_uso'],
                'modulo': metadata['modulo'],
                'nivel_riesgo_display': metadata['nivel_riesgo_display'],
                'nivel_riesgo_badge': metadata['nivel_riesgo_badge'],
            })
        
        return JsonResponse(results[:20], safe=False)
    
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


# ═══════════════════════════════════════════════════════════════════
# GESTIÓN DE USUARIOS EN GRUPOS
# ═══════════════════════════════════════════════════════════════════

@method_decorator(
    require_permission("roles.manage_group_users", check_client_assignment=False),
    name="dispatch"
)
class GroupDetailUsersView(LoginRequiredMixin, DetailView):
    """
    🔒 PROTEGIDA: roles.manage_group_users
    
    Vista para gestionar usuarios asignados a un grupo.
    """
    model = Group
    template_name = 'groups/group_detail_users.html'
    context_object_name = 'group'
    
    def dispatch(self, request, *args, **kwargs):
        """Validar que no se modifiquen los propios grupos"""
        self.object = self.get_object()
        
        # SEGURIDAD: Evitar que un usuario se remueva a sí mismo de grupos críticos
        if request.method == 'POST':
            action = request.POST.get('action')
            user_ids = request.POST.getlist('users')
            
            if action == 'remove' and str(request.user.id) in user_ids:
                if self.object.name in PROTECTED_GROUPS or request.user.groups.filter(pk=self.object.pk).exists():
                    messages.error(
                        request,
                        '❌ No puedes removerte a ti mismo de este grupo.'
                    )
                    return redirect('group_detail_users', pk=self.object.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        
        # Usuarios actuales del grupo
        context['current_users'] = group.user_set.all().order_by('username')
        
        # Usuarios disponibles para agregar (que NO están en el grupo)
        context['available_users'] = User.objects.exclude(
            groups=group
        ).order_by('username')
        
        # Indicar si puede solo ver o también gestionar
        context['can_view_only'] = self.request.user.has_perm('roles.view_group_users')
        context['can_manage'] = self.request.user.has_perm('roles.manage_group_users')
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Procesa la adición/eliminación de usuarios del grupo"""
        self.object = self.get_object()
        action = request.POST.get('action')
        
        if action == 'add':
            user_ids = request.POST.getlist('users')
            users = User.objects.filter(id__in=user_ids)
            self.object.user_set.add(*users)
            messages.success(
                request,
                f'✅ {users.count()} usuario(s) agregado(s) al rol "{self.object.name}".'
            )
        
        elif action == 'remove':
            user_ids = request.POST.getlist('users')
            users = User.objects.filter(id__in=user_ids)
            self.object.user_set.remove(*users)
            messages.success(
                request,
                f'✅ {users.count()} usuario(s) eliminado(s) del rol "{self.object.name}".'
            )
        
        return redirect('group_detail_users', pk=self.object.pk)


# ═══════════════════════════════════════════════════════════════════
# MATRIZ DE PERMISOS
# ═══════════════════════════════════════════════════════════════════

@method_decorator(
    require_permission("roles.view_permission_matrix", check_client_assignment=False),
    name="dispatch"
)
class PermissionMatrixView(LoginRequiredMixin, ListView):
    """
    🔒 PROTEGIDA: roles.view_permission_matrix
    
    Muestra una matriz comparativa de permisos entre todos los roles.
    """
    model = Group
    template_name = 'permissions/permission_matrix.html'
    context_object_name = 'groups'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener todos los grupos
        groups = self.get_queryset()
        
        # Filtrar solo permisos custom
        codenames_custom = {perm_def['codename'] for perm_def in TODOS_LOS_PERMISOS}
        
        # Obtener todos los permisos relevantes (incluyendo 'roles' ahora)
        all_permissions = Permission.objects.filter(
            codename__in=codenames_custom,
            content_type__app_label__in=[
                'clientes', 'divisas', 'transacciones', 'medios_pago', 'users', 'mfa', 'roles'
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


@method_decorator(
    require_permission("roles.manage_role_status", check_client_assignment=False),
    name="dispatch"
)
class GroupToggleStatusView(LoginRequiredMixin, View):
    """
    🔒 PROTEGIDA: roles.manage_role_status
    
    Activa/desactiva un rol.
    """
    
    def post(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        
        # SEGURIDAD: No permitir desactivar grupos protegidos
        if group.name in PROTECTED_GROUPS:
            messages.error(
                request,
                f'❌ El rol "{group.name}" está protegido y no se puede desactivar.'
            )
            return redirect('group_list')
        
        status, _ = RoleStatus.objects.get_or_create(group=group)
        status.is_active = not status.is_active
        status.save()

        estado = "activado" if status.is_active else "desactivado"
        messages.success(request, f'✅ Rol "{group.name}" {estado} correctamente.')
        return redirect('group_list')


# ═══════════════════════════════════════════════════════════════════
# VISTAS DE ERROR PERSONALIZADAS
# ═══════════════════════════════════════════════════════════════════

def permission_denied_view(request, exception=None):
    """
    Vista personalizada para error 403 (Permission Denied).
    Redirige según el tipo de usuario.
    """
    if not request.user.is_authenticated:
        # Usuario no autenticado → login
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.path)
    
    user = request.user
    grupos = list(user.groups.values_list('name', flat=True))
    
    # Determinar mensaje y URL de redirección
    if user.is_superuser or 'admin' in grupos or 'Administrador' in grupos:
        mensaje = 'No tienes permisos para acceder a esta sección como Administrador.'
        url_redireccion = '/admin/dashboard/' if hasattr(request, 'resolver_match') else '/'
        mostrar_menu_staff = True
    elif 'operador' in grupos or 'Operador' in grupos:
        mensaje = 'No tienes permisos para acceder a esta sección como Operador.'
        url_redireccion = '/'
        mostrar_menu_staff = True
    elif 'cliente' in grupos or 'Cliente' in grupos:
        mensaje = 'No tienes permisos para acceder a esta sección como Operador de Cuenta.'
        url_redireccion = '/'
        mostrar_menu_staff = False
    else:
        mensaje = 'Tu cuenta está pendiente de aprobación por un administrador.'
        url_redireccion = '/'
        mostrar_menu_staff = False
    
    context = {
        'titulo': 'Acceso Denegado',
        'mensaje': mensaje,
        'permiso_requerido': getattr(exception, 'args', [''])[0] if exception else None,
        'usuario': user,
        'usuario_autenticado': True,
        'es_superusuario': user.is_superuser,
        'url_redireccion': url_redireccion,
        'mostrar_menu_staff': mostrar_menu_staff,
        'tipo_usuario': grupos[0] if grupos else 'Usuario',
    }
    
    return render(request, '403.html', context, status=403)


def page_not_found_view(request, exception=None):
    """
    Vista personalizada para error 404 (Not Found).
    Redirige al dashboard según el tipo de usuario.
    """
    if not request.user.is_authenticated:
        url_redireccion = '/'
        mostrar_menu_staff = False
        tipo_usuario = 'Invitado'
    else:
        user = request.user
        grupos = list(user.groups.values_list('name', flat=True))
        
        if user.is_superuser or 'admin' in grupos or 'Administrador' in grupos:
            url_redireccion = '/admin/dashboard/'
            mostrar_menu_staff = True
            tipo_usuario = 'Administrador'
        elif 'operador' in grupos or 'Operador' in grupos:
            url_redireccion = '/'
            mostrar_menu_staff = True
            tipo_usuario = 'Operador'
        elif 'cliente' in grupos or 'Cliente' in grupos:
            url_redireccion = '/'
            mostrar_menu_staff = False
            tipo_usuario = 'Operador de Cuenta'
        else:
            url_redireccion = '/'
            mostrar_menu_staff = False
            tipo_usuario = 'Usuario'
    
    context = {
        'titulo': 'Página no encontrada',
        'mensaje': 'La página que buscas no existe o fue movida.',
        'url_redireccion': url_redireccion,
        'mostrar_menu_staff': mostrar_menu_staff,
        'tipo_usuario': tipo_usuario,
        'usuario_autenticado': request.user.is_authenticated,
    }
    
    return render(request, '404.html', context, status=404)


def server_error_view(request):
    """
    Vista personalizada para error 500 (Server Error).
    Siempre redirige al inicio para evitar loops.
    """
    context = {
        'titulo': 'Error del servidor',
        'mensaje': 'Ocurrió un error en el servidor. Nuestro equipo ha sido notificado.',
        'url_redireccion': '/',
        'mostrar_boton_reportar': True,
        'usuario_autenticado': request.user.is_authenticated if hasattr(request, 'user') else False,
    }
    
    return render(request, '500.html', context, status=500)


def bad_request_view(request, exception=None):
    """
    Vista personalizada para error 400 (Bad Request).
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        url_redireccion = '/'
    else:
        user = request.user
        grupos = list(user.groups.values_list('name', flat=True))
        
        if user.is_superuser or 'admin' in grupos or 'operador' in grupos:
            url_redireccion = '/'
        else:
            url_redireccion = '/'
    
    context = {
        'titulo': 'Solicitud incorrecta',
        'mensaje': 'La solicitud enviada no es válida.',
        'url_redireccion': url_redireccion,
        'usuario_autenticado': hasattr(request, 'user') and request.user.is_authenticated,
    }
    
    return render(request, '400.html', context, status=400)


@method_decorator(
    require_permission("roles.view_group_users", check_client_assignment=False),
    name="dispatch"
)
def search_users(request):
    """
    🔒 PROTEGIDA: roles.view_group_users
    
    Vista para buscar usuarios por nombre de usuario o email.
    Devuelve una lista de usuarios en formato JSON.
    Esta vista es utilizada por las llamadas AJAX.
    """
    query = request.GET.get('q', '')
    if query:
        # Busca usuarios que coincidan con la consulta en el email
        users = User.objects.filter(email__icontains=query).distinct()
        data = [{'id': u.id, 'email': u.email, 'username': u.username} for u in users]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)