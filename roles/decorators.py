"""
Decoradores para proteger vistas con permisos personalizados.
CENTRALIZADOS PARA TODO EL SISTEMA.

Este módulo contiene decoradores reutilizables para Function-Based Views (FBV)
y Class-Based Views (CBV) que permiten verificar permisos personalizados
y validar acceso a clientes específicos.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def require_permission(permission_codename, check_client_assignment=None):
    """
    Decorador que verifica permisos del usuario.
    
    ⚠️ DEPRECATED: check_client_assignment ya no se usa
    
    Args:
        permission_codename (str): Permiso requerido (ej: 'clientes.view_medios_pago')
        check_client_assignment (bool|None): [IGNORADO] Mantener para retrocompatibilidad
    """
    # ⚠️ Advertir si se usa check_client_assignment
    if check_client_assignment is not None:
        import warnings
        warnings.warn(
            f"check_client_assignment está deprecado y será ignorado. "
            f"Valida cliente activo en la vista usando request.session['cliente_id']",
            DeprecationWarning,
            stacklevel=2
        )
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # ✅ SOLO verificar permiso
            if not request.user.has_perm(permission_codename):
                raise PermissionDenied(
                    f"No tienes permiso para realizar esta acción. "
                    f"Permiso requerido: {permission_codename}"
                )
            
            # ✅ NO validar cliente activo aquí
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator


def require_client_selection(view_func):
    """
    Decorador separado para validar cliente activo.
    
    Uso:
        @require_permission('clientes.view_medios_pago')
        @require_client_selection  # ✅ Decorador específico
        def mi_vista(request):
            cliente_id = request.session['cliente_id']  # Garantizado
            ...
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        from roles.utils import es_staff
        
        # Staff NO necesita cliente seleccionado
        if es_staff(request.user):
            return view_func(request, *args, **kwargs)
        
        # Validar cliente activo para operadores de cuenta
        cliente_id = request.session.get('cliente_id')
        
        if not cliente_id:
            raise PermissionDenied(
                "No hay un cliente activo seleccionado. "
                "Por favor, selecciona un cliente antes de continuar."
            )
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view