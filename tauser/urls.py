from django.urls import path
from . import views

app_name = 'tauser'

urlpatterns = [
    # ==================== ACCESO Y SESIÓN ====================
    path(
        'terminal/<str:terminal_codigo>/',
        views.inicio_tauser,
        name='inicio_tauser'
    ),
    path(
        'terminal/<str:terminal_codigo>/validar-pin/',
        views.validar_pin,
        name='validar_pin'
    ),
    path(
        'terminal/<str:terminal_codigo>/menu/',
        views.menu_principal,
        name='menu_principal'
    ),
    path(
        'terminal/<str:terminal_codigo>/cerrar-sesion/',
        views.cerrar_sesion_tauser,
        name='cerrar_sesion_tauser'
    ),
    
    # ==================== TRANSACCIONES ====================
    path(
        'terminal/<str:terminal_codigo>/cliente/<int:cliente_id>/transacciones/',
        views.TransaccionesClienteView.as_view(),
        name='transacciones_cliente'
    ),
    path(
        'terminal/<str:terminal_codigo>/transaccion/<int:transaccion_id>/ejecutar/',
        views.EjecutarOperacionView.as_view(),
        name='ejecutar_operacion'
    ),
    
    # ==================== DENOMINACIONES - RETIRO ====================
    path(
        'terminal/<str:terminal_codigo>/transaccion/<int:transaccion_id>/denominaciones-retiro/',
        views.seleccionar_denominaciones_retiro,
        name='seleccionar_denominaciones_retiro'
    ),
    
    # ==================== DENOMINACIONES - VENTA ====================
    path(
        'terminal/<str:terminal_codigo>/transaccion/<int:transaccion_id>/denominaciones-venta/',
        views.seleccionar_denominaciones_venta,
        name='seleccionar_denominaciones_venta'
    ),
    path(
        'terminal/<str:terminal_codigo>/transaccion/<int:transaccion_id>/confirmar-venta/',
        views.confirmar_denominaciones_venta,
        name='confirmar_denominaciones_venta'
    ),
    
    # ==================== GESTIÓN DE INVENTARIO (STAFF) ====================
    path(
        'terminales/',
        views.TerminalListView.as_view(),
        name='terminal_list'
    ),
    path(
        'terminales/crear/',
        views.TerminalCreateView.as_view(),
        name='terminal_create'
    ),
    path(
        'terminales/<int:pk>/editar/',
        views.TerminalUpdateView.as_view(),
        name='terminal_update'
    ),
    
    # ==================== INVENTARIO DE DENOMINACIONES ====================
    path(
        'terminal/<str:terminal_codigo>/inventario/denominaciones/',
        views.InventarioDenominacionesView.as_view(),
        name='inventario_denominaciones'
    ),
    path(
        'terminal/<str:terminal_codigo>/inventario/denominaciones/reponer/',
        views.ReponerDenominacionesView.as_view(),
        name='reponer_denominaciones'
    ),
    path(
        'terminal/<str:terminal_codigo>/inventario/denominaciones/ajustar/',
        views.AjustarInventarioDenominacionView.as_view(),
        name='ajustar_inventario_denominacion'
    ),
    path(
        'terminal/<str:terminal_codigo>/inventario/denominaciones/historial/',
        views.HistorialDenominacionesView.as_view(),
        name='historial_denominaciones'
    ),
    
    # ==================== REPORTES ====================
    path(
        'terminal/<str:terminal_codigo>/reportes/operaciones/',
        views.ReporteOperacionesView.as_view(),
        name='reporte_operaciones'
    ),
    path(
        'terminal/<str:terminal_codigo>/reportes/denominaciones/',
        views.ReporteDenominacionesView.as_view(),
        name='reporte_denominaciones'
    ),
    
    # ==================== API/AJAX ====================
    path(
        'terminal/<str:terminal_codigo>/api/inventario-denominaciones/',
        views.api_inventario_denominaciones,
        name='api_inventario_denominaciones'
    ),
]