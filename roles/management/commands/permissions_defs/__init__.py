# roles/management/commands/permissions_defs/__init__.py

from .clientes import PERMISOS_CLIENTES
from .divisas import PERMISOS_DIVISAS
from .medios_pago import PERMISOS_MEDIOS_PAGO
from .transacciones import PERMISOS_TRANSACCIONES
from .usuarios import PERMISOS_USUARIOS

# Consolidar todos los permisos
TODOS_LOS_PERMISOS = (
    PERMISOS_CLIENTES +
    PERMISOS_DIVISAS +
    PERMISOS_MEDIOS_PAGO +
    PERMISOS_TRANSACCIONES +
    PERMISOS_USUARIOS
)

__all__ = [
    'TODOS_LOS_PERMISOS',
    'PERMISOS_CLIENTES',
    'PERMISOS_DIVISAS',
    'PERMISOS_MEDIOS_PAGO',
    'PERMISOS_TRANSACCIONES',
    'PERMISOS_USUARIOS',
]