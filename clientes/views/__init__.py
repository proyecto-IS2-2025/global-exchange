"""
Módulo de vistas para la gestión de clientes.
Exporta todas las vistas para mantener compatibilidad.
"""

from .helpers import get_cliente_activo, get_medio_acreditacion_seleccionado, get_medio_pago_seleccionado
from .cliente import (
    crear_cliente_view,
    seleccionar_cliente_view,
    ClienteListView,
    ClienteUpdateView,
)
from .asociacion import (
    asociar_clientes_usuarios_view,
    listar_asociaciones,
)
from .descuento import (
    DescuentoListView,
    DescuentoUpdateView,
    HistorialDescuentoListView,
)
from .limite import (
    panel_limites,
    lista_limites_diarios,
    crear_limite_diario,
    LimiteDiarioUpdateView,
    lista_limites_mensuales,
    crear_limite_mensual,
    LimiteMensualUpdateView,
)
from .medio_pago import (
    ClienteMedioDePagoListView,
    ClienteMedioDePagoCreateView,
    ClienteMedioDePagoUpdateView,
    ClienteMedioDePagoToggleView,
    ClienteMedioDePagoDeleteView,
    SeleccionarMedioAcreditacionView,
    SeleccionarMedioPagoView,
    select_medio_pago_view,
    medio_pago_detail_ajax,
    dashboard_medios_pago,
    exportar_medios_pago,
    verificar_duplicados_ajax,
)

# Exportar todo
__all__ = [
    # Clientes
    'crear_cliente_view',
    'seleccionar_cliente_view',
    'ClienteListView',
    'ClienteUpdateView',
    
    # Asociaciones
    'asociar_clientes_usuarios_view',
    'listar_asociaciones',
    
    # Descuentos
    'DescuentoListView',
    'DescuentoUpdateView',
    'HistorialDescuentoListView',
    
    # Límites
    'panel_limites',
    'lista_limites_diarios',
    'crear_limite_diario',
    'LimiteDiarioUpdateView',
    'lista_limites_mensuales',
    'crear_limite_mensual',
    'LimiteMensualUpdateView',
    
    # Medios de Pago
    'ClienteMedioDePagoListView',
    'ClienteMedioDePagoCreateView',
    'ClienteMedioDePagoUpdateView',
    'ClienteMedioDePagoToggleView',
    'ClienteMedioDePagoDeleteView',
    'SeleccionarMedioAcreditacionView',
    'SeleccionarMedioPagoView',
    'select_medio_pago_view',
    'medio_pago_detail_ajax',
    'dashboard_medios_pago',
    'exportar_medios_pago',
    'verificar_duplicados_ajax',
]