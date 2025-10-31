from django.urls import path
from . import views

app_name = 'tauser'

urlpatterns = [
    # ==================== PÁGINA PRINCIPAL EXTERNA ====================
    path(
        '',
        views.tauser_home,
        name='home'
    ),
    path(
        'terminal/<str:terminal_codigo>/cliente/',
        views.menu_cliente_tauser,
        name='menu_cliente'
    ),
    
    # ==================== ACCESO Y SESIÓN ====================
    path(
        'terminales-cliente/',
        views.lista_terminales,
        name='lista_terminales'
    ),
    path(
        'terminal/seleccionar/<str:terminal_codigo>/',
        views.seleccionar_terminal,
        name='seleccionar_terminal'
    ),
    path(
        'terminal/<str:terminal_codigo>/',
        views.inicio_tauser,
        name='inicio_tauser'
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
        'terminales/<int:pk>/',
        views.TerminalDetailView.as_view(),
        name='terminal_detail'
    ),
    path(
        'terminales/<int:pk>/editar/',
        views.TerminalUpdateView.as_view(),
        name='terminal_update'
    ),
    path(
        'terminales/<int:pk>/toggle/',
        views.toggle_terminal_activa,
        name='terminal_toggle'
    ),
    # ==================== GESTIÓN DE INVENTARIO POR DENOMINACIONES ====================
    path(
        'terminales/<int:terminal_pk>/inventario-denominaciones/',
        views.GestionInventarioDenominacionesView.as_view(),
        name='gestion_inventario_denominaciones'
    ),
    path(
        'terminales/<int:terminal_pk>/inventario-denominaciones/agregar/',
        views.AgregarDenominacionInventarioView.as_view(),
        name='agregar_denominacion_inventario'
    ),
    path(
        'terminales/<int:terminal_pk>/inventario-denominaciones/<int:inventario_pk>/ajustar/',
        views.AjustarInventarioDenominacionAdminView.as_view(),
        name='ajustar_inventario_denominacion_admin'
    ),
    path(
        'terminales/<int:terminal_pk>/inventario-denominaciones/<int:inventario_pk>/eliminar/',
        views.EliminarInventarioDenominacionView.as_view(),
        name='eliminar_inventario_denominacion'
    ),
    # Nuevas rutas para mejoras de UI
    path(
        'terminales/<int:terminal_pk>/dashboard-inventario/',
        views.DashboardInventarioView.as_view(),
        name='dashboard_inventario'
    ),
    path(
        'terminales/<int:terminal_pk>/recarga-masiva/',
        views.RecargaMasivaView.as_view(),
        name='recarga_masiva'
    ),
    path(
        'terminales/<int:terminal_pk>/historial-recargas/',
        views.HistorialRecargasView.as_view(),
        name='historial_recargas'
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