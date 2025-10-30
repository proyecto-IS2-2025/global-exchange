"""
Mixins reutilizables para proteger Class-Based Views.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


class PermissionRequiredMessageMixin(PermissionRequiredMixin):
    """
    Mixin mejorado que muestra mensajes cuando falla la verificación de permisos.
    
    Uso:
        class MiVista(PermissionRequiredMessageMixin, ListView):
            permission_required = 'clientes.view_cliente'
    """
    raise_exception = False
    redirect_url = 'inicio'
    
    def handle_no_permission(self):
        messages.error(
            self.request,
            'No tienes los permisos necesarios para acceder a esta sección.'
        )
        return redirect(self.redirect_url)


class AnyPermissionRequiredMixin(LoginRequiredMixin):
    """
    Mixin que requiere AL MENOS UNO de los permisos especificados.
    
    Uso:
        class MiVista(AnyPermissionRequiredMixin, ListView):
            required_permissions = ['clientes.view_cliente', 'clientes.add_cliente']
    """
    required_permissions = []
    redirect_url = 'inicio'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        # Verificar si tiene al menos un permiso
        if any(request.user.has_perm(perm) for perm in self.required_permissions):
            return super().dispatch(request, *args, **kwargs)
        
        messages.error(
            request,
            'No tienes permisos suficientes para acceder a esta sección.'
        )
        return redirect(self.redirect_url)


class StaffRequiredMixin(LoginRequiredMixin):
    """
    Mixin simple que requiere que el usuario sea staff.
    
    TODO: Cuando migremos a permisos, cambiar esta lógica.
    """
    redirect_url = 'inicio'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Por ahora, verificar grupos
        if request.user.is_superuser or request.user.groups.filter(name__in=['admin', 'operador']).exists():
            return super().dispatch(request, *args, **kwargs)
        
        messages.error(request, 'Esta sección es solo para personal autorizado.')
        return redirect(self.redirect_url)


# ═══════════════════════════════════════════════════════════════════════════
# NUEVO: MIXIN PARA VERIFICAR ROL POR GRUPO
# ═══════════════════════════════════════════════════════════════════════════

class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin que requiere que el usuario pertenezca a un rol/grupo específico.
    
    Uso:
        class MiVista(RoleRequiredMixin, ListView):
            required_role = 'admin'  # O lista: ['admin', 'operador']
    
    Atributos:
        required_role (str o list): Nombre(s) del/los grupo(s) requerido(s)
        redirect_url (str): URL de redirección si no tiene el rol
        allow_superuser (bool): Si True, permite superusuarios sin verificar rol
    """
    required_role = None  # 'admin', 'operador', 'cliente', etc.
    redirect_url = 'inicio'
    allow_superuser = True
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar autenticación
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Permitir superusuarios sin verificar rol
        if self.allow_superuser and request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        # Verificar rol/grupo requerido
        if not self.has_required_role(request.user):
            messages.error(
                request,
                f'Esta sección requiere el rol "{self.get_required_role_display()}". '
                'Contacta al administrador si necesitas acceso.'
            )
            return redirect(self.redirect_url)
        
        return super().dispatch(request, *args, **kwargs)
    
    def has_required_role(self, user):
        """Verifica si el usuario tiene el rol requerido"""
        if self.required_role is None:
            return True
        
        # Soportar múltiples roles
        if isinstance(self.required_role, (list, tuple)):
            return user.groups.filter(name__in=self.required_role).exists()
        
        # Un solo rol
        return user.groups.filter(name=self.required_role).exists()
    
    def get_required_role_display(self):
        """Obtiene nombre legible del rol requerido"""
        if isinstance(self.required_role, (list, tuple)):
            return ', '.join(self.required_role)
        return self.required_role or 'desconocido'


class MultipleRolesRequiredMixin(LoginRequiredMixin):
    """
    Mixin que requiere que el usuario tenga TODOS los roles especificados.
    
    Uso:
        class MiVista(MultipleRolesRequiredMixin, ListView):
            required_roles = ['admin', 'operador']  # Debe tener AMBOS
    """
    required_roles = []
    redirect_url = 'inicio'
    allow_superuser = True
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if self.allow_superuser and request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        # Verificar que tiene TODOS los roles
        user_groups = set(request.user.groups.values_list('name', flat=True))
        required_set = set(self.required_roles)
        
        if not required_set.issubset(user_groups):
            missing_roles = required_set - user_groups
            messages.error(
                request,
                f'Te faltan los siguientes roles: {", ".join(missing_roles)}'
            )
            return redirect(self.redirect_url)
        
        return super().dispatch(request, *args, **kwargs)


class RoleOrPermissionRequiredMixin(LoginRequiredMixin):
    """
    Mixin híbrido: verifica ROL O PERMISO (lo que sea más conveniente).
    
    Uso:
        class MiVista(RoleOrPermissionRequiredMixin, ListView):
            required_role = 'admin'
            required_permission = 'clientes.view_all_clientes'
    """
    required_role = None
    required_permission = None
    redirect_url = 'inicio'
    allow_superuser = True
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if self.allow_superuser and request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        # Verificar rol
        has_role = False
        if self.required_role:
            if isinstance(self.required_role, (list, tuple)):
                has_role = request.user.groups.filter(name__in=self.required_role).exists()
            else:
                has_role = request.user.groups.filter(name=self.required_role).exists()
        
        # Verificar permiso
        has_permission = False
        if self.required_permission:
            has_permission = request.user.has_perm(self.required_permission)
        
        # Si tiene rol O permiso, permitir
        if has_role or has_permission:
            return super().dispatch(request, *args, **kwargs)
        
        messages.error(
            request,
            'No tienes acceso a esta sección. Contacta al administrador.'
        )
        return redirect(self.redirect_url)