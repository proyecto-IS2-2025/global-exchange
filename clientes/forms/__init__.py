"""
Módulo de formularios para la gestión de clientes.
Exporta todos los formularios para mantener compatibilidad con imports existentes.
"""

# Formularios de Cliente
from .cliente import ClienteForm, SeleccionClienteForm

# Formularios de Descuento
from .descuento import DescuentoForm

# Formularios de Límites
from .limite import LimiteDiarioForm, LimiteMensualForm

# Formularios de Medios de Pago
from .medio_pago import (
    SelectMedioDePagoForm,
    ClienteMedioDePagoCompleteForm,
    ClienteMedioDePagoBulkForm
)

__all__ = [
    # Cliente
    'ClienteForm',
    'SeleccionClienteForm',
    
    # Descuento
    'DescuentoForm',
    
    # Límites
    'LimiteDiarioForm',
    'LimiteMensualForm',
    
    # Medios de Pago
    'SelectMedioDePagoForm',
    'ClienteMedioDePagoCompleteForm',
    'ClienteMedioDePagoBulkForm',
]