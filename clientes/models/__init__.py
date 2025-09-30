"""
Módulo de modelos para la gestión de clientes.
Exporta todos los modelos para mantener compatibilidad con imports existentes.
"""

from .cliente import Cliente, Segmento, AsignacionCliente
from .descuento import Descuento, HistorialDescuentos
from .medio_pago import ClienteMedioDePago, HistorialClienteMedioDePago
from .limite import LimiteDiario, LimiteMensual

__all__ = [
    # Cliente
    'Cliente',
    'Segmento',
    'AsignacionCliente',
    # Descuento
    'Descuento',
    'HistorialDescuentos',
    # Medio de Pago
    'ClienteMedioDePago',
    'HistorialClienteMedioDePago',
    # Límites
    'LimiteDiario',
    'LimiteMensual',
]