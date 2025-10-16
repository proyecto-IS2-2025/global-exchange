"""
Importación centralizada de todas las definiciones de permisos personalizados.
"""

from .clientes import PERMISOS_CLIENTES
from .divisas import PERMISOS_DIVISAS
from .medios_pago import PERMISOS_MEDIOS_PAGO
from .transacciones import PERMISOS_TRANSACCIONES
from .usuarios import PERMISOS_USUARIOS
from .mfa import PERMISOS_MFA  
# Consolidar todos los permisos personalizados del sistema
TODOS_LOS_PERMISOS = (
    PERMISOS_CLIENTES +
    PERMISOS_DIVISAS +
    PERMISOS_MEDIOS_PAGO +
    PERMISOS_TRANSACCIONES +
    PERMISOS_USUARIOS +
    PERMISOS_MFA  
)

__all__ = [
    'TODOS_LOS_PERMISOS',
    'PERMISOS_CLIENTES',
    'PERMISOS_DIVISAS',
    'PERMISOS_MEDIOS_PAGO',
    'PERMISOS_TRANSACCIONES',
    'PERMISOS_USUARIOS',
    'PERMISOS_MFA',
]