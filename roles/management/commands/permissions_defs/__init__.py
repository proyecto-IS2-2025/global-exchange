# roles/management/commands/permissions_defs/__init__.py

from .clientes import PERMISOS_CLIENTES

# Consolidar todos los permisos
TODOS_LOS_PERMISOS = (
    PERMISOS_CLIENTES
    # + PERMISOS_DIVISAS (agregaremos después)
    # + PERMISOS_TRANSACCIONES (agregaremos después)
)

__all__ = [
    'TODOS_LOS_PERMISOS',
    'PERMISOS_CLIENTES',
]