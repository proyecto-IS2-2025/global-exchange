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