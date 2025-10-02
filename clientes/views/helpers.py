"""
Funciones auxiliares compartidas entre vistas.
"""
from clientes.models import Cliente


def get_cliente_activo(request):
    """Obtener el cliente activo de la sesión."""
    cliente_id = request.session.get('cliente_activo_id') or request.session.get('cliente_id')
    if not cliente_id:
        return None

    try:
        return Cliente.objects.get(
            id=cliente_id,
            asignacioncliente__usuario=request.user,
            esta_activo=True
        )
    except Cliente.DoesNotExist:
        request.session.pop('cliente_activo_id', None)
        request.session.pop('cliente_id', None)
        return None


def get_medio_acreditacion_seleccionado(request):
    """Obtener el medio de acreditación seleccionado."""
    return request.session.get("medio_seleccionado")


def get_medio_pago_seleccionado(request):
    """Obtener el medio de pago seleccionado."""
    return request.session.get("medio_pago_seleccionado")