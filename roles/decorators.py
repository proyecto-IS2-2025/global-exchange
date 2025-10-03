"""
Decoradores reutilizables para proteger Function-Based Views.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

def permission_required_custom(*perms, raise_exception=True, redirect_url='inicio'):
    """
    Decorador mejorado que verifica permisos y muestra mensajes amigables.
    
    Uso:
        @permission_required_custom('clientes.view_cliente', 'clientes.add_cliente')
        def mi_vista(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Superusuarios siempre pasan
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar si tiene TODOS los permisos requeridos
            if request.user.has_perms(perms):
                return view_func(request, *args, **kwargs)
            
            # Usuario sin permisos
            messages.error(
                request, 
                'No tienes los permisos necesarios para acceder a esta sección.'
            )
            
            if raise_exception:
                raise PermissionDenied
            
            return redirect(redirect_url)
        
        return wrapper
    return decorator


def any_permission_required(*perms, raise_exception=True, redirect_url='inicio'):
    """
    Decorador que requiere AL MENOS UNO de los permisos especificados.
    
    Uso:
        @any_permission_required('clientes.view_cliente', 'clientes.add_cliente')
        def mi_vista(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar si tiene AL MENOS UN permiso
            if any(request.user.has_perm(perm) for perm in perms):
                return view_func(request, *args, **kwargs)
            
            messages.error(
                request,
                'No tienes permisos suficientes para acceder a esta sección.'
            )
            
            if raise_exception:
                raise PermissionDenied
            
            return redirect(redirect_url)
        
        return wrapper
    return decorator


def staff_required(view_func):
    """
    Decorador simple que requiere que el usuario tenga algún permiso administrativo.
    
    TODO: Cuando migremos completamente a permisos, cambiar esta lógica.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Por ahora, verificar si está en grupos admin u operador
        if request.user.is_superuser or request.user.groups.filter(name__in=['admin', 'operador']).exists():
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Esta sección es solo para personal autorizado.')
        return redirect('inicio')
    
    return wrapper