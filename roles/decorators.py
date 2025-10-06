"""
Decoradores para proteger vistas con permisos personalizados.
CENTRALIZADOS PARA TODO EL SISTEMA.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.conf import settings


def require_permission(permission_codename, check_client_assignment=None):
    """
    Decorador que verifica permisos del usuario.
    
    Args:
        permission_codename (str|list|tuple): Permiso(s) requerido(s)
            - Si es string: debe tener ese permiso exacto
            - Si es lista/tupla: debe tener AL MENOS UNO de los permisos
        check_client_assignment (bool|None): [DEPRECADO] Ignorado
    
    Examples:
        @require_permission('clientes.view_all_clientes')
        
        @require_permission([
            'clientes.view_all_clientes',
            'clientes.view_assigned_clientes'
        ])
    
    ⚠️ DEPRECATED: check_client_assignment ya no se usa
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
            # ✅ BYPASS PARA DESARROLLO
            if settings.DEBUG and request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # ✅ Soportar tanto string como lista/tupla
            if isinstance(permission_codename, (list, tuple)):
                # Lista: debe tener AL MENOS UNO
                tiene_permiso = any(
                    request.user.has_perm(perm) 
                    for perm in permission_codename
                )
                permisos_str = ' o '.join(permission_codename)
            else:
                # String: debe tener ese permiso
                tiene_permiso = request.user.has_perm(permission_codename)
                permisos_str = permission_codename
            
            if not tiene_permiso:
                raise PermissionDenied(
                    f"No tienes permiso para realizar esta acción. "
                    f"Permiso requerido: {permisos_str}"
                )
            
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