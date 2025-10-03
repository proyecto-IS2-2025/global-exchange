from functools import wraps

from django.core.exceptions import PermissionDenied

from clientes.models import AsignacionCliente, Cliente


def _get_cliente_activo(request):
    cliente_id = request.session.get("cliente_activo_id")
    if not cliente_id:
        return None
    return Cliente.objects.filter(id=cliente_id).first()


def _tiene_acceso_a_cliente(user, cliente):
    if not cliente:
        return False
    if user.is_superuser or user.has_perm("clientes.view_all_clientes"):
        return True
    return AsignacionCliente.objects.filter(usuario=user, cliente=cliente).exists()


def require_permission(permission_codename, check_client_assignment=True):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(permission_codename):
                raise PermissionDenied

            if check_client_assignment:
                cliente = _get_cliente_activo(request)
                if not _tiene_acceso_a_cliente(request.user, cliente):
                    raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator