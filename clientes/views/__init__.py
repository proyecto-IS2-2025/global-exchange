"""
Módulo de vistas para la gestión de clientes.
Exporta todas las vistas para mantener compatibilidad.
"""

from .helpers import get_cliente_activo, get_medio_acreditacion_seleccionado, get_medio_pago_seleccionado
from .cliente import (
    ClienteListView, ClienteUpdateView, crear_cliente_view, 
    seleccionar_cliente_view
)
from .asociacion import asociar_clientes_usuarios_view, listar_asociaciones
from .descuento import DescuentoListView, DescuentoUpdateView, HistorialDescuentoListView
from .limite import (
    lista_limites_diarios, lista_limites_mensuales,
    crear_limite_diario, crear_limite_mensual,
    LimiteDiarioUpdateView, LimiteMensualUpdateView
)
from .medio_pago import (
    ClienteMedioDePagoListView, ClienteMedioDePagoCreateView, 
    ClienteMedioDePagoUpdateView, ClienteMedioDePagoToggleView,
    ClienteMedioDePagoDeleteView, select_medio_pago_view,
    medio_pago_detail_ajax, dashboard_medios_pago,
    exportar_medios_pago, verificar_duplicados_ajax,
    SeleccionarMedioAcreditacionView, SeleccionarMedioPagoView
)

__all__ = [
    # Helpers
    'get_cliente_activo',
    'get_medio_acreditacion_seleccionado',
    'get_medio_pago_seleccionado',
    # Cliente
    'ClienteListView',
    'ClienteUpdateView',
    'crear_cliente_view',
    'seleccionar_cliente_view',
    # Asociación
    'asociar_clientes_usuarios_view',
    'listar_asociaciones',
    # Descuento
    'DescuentoListView',
    'DescuentoUpdateView',
    'HistorialDescuentoListView',
    # Límite
    'lista_limites_diarios',
    'lista_limites_mensuales',
    'crear_limite_diario',
    'crear_limite_mensual',
    'LimiteDiarioUpdateView',
    'LimiteMensualUpdateView',
    # Medio de Pago
    'ClienteMedioDePagoListView',
    'ClienteMedioDePagoCreateView',
    'ClienteMedioDePagoUpdateView',
    'ClienteMedioDePagoToggleView',
    'ClienteMedioDePagoDeleteView',
    'select_medio_pago_view',
    'medio_pago_detail_ajax',
    'dashboard_medios_pago',
    'exportar_medios_pago',
    'verificar_duplicados_ajax',
    'SeleccionarMedioAcreditacionView',
    'SeleccionarMedioPagoView',
]