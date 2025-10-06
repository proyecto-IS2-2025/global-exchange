# transacciones/urls.py
from django.urls import path
from . import views

app_name = 'transacciones'

urlpatterns = [
    # ═══════════════════════════════════════════════════════════════
    # CREACIÓN DE TRANSACCIONES
    # ═══════════════════════════════════════════════════════════════
    path('realizar-compra/', views.realizar_compra, name='realizar_compra'),
    path('realizar-venta/', views.realizar_venta, name='realizar_venta'),
    
    # ═══════════════════════════════════════════════════════════════
    # CONFIRMACIÓN
    # ═══════════════════════════════════════════════════════════════
    path('confirmacion/<str:numero_transaccion>/', views.confirmacion_operacion, name='confirmacion_operacion'),
    
    # ═══════════════════════════════════════════════════════════════
    # HISTORIAL Y DETALLE
    # ═══════════════════════════════════════════════════════════════
    path('historial/', views.HistorialTransaccionesClienteView.as_view(), name='historial_cliente'),
    path('historial/admin/', views.historial_admin, name='historial_admin'),
    path('detalle/<str:numero_transaccion>/', views.DetalleTransaccionView.as_view(), name='detalle'),
    
    # ═══════════════════════════════════════════════════════════════
    # EXPORTACIÓN
    # ═══════════════════════════════════════════════════════════════
    path('exportar/', views.ExportarTransaccionesView.as_view(), name='exportar'),
    
    # ═══════════════════════════════════════════════════════════════
    # GESTIÓN (CAMBIO DE ESTADO, CANCELACIÓN)
    # ═══════════════════════════════════════════════════════════════
    path('cambiar-estado/<str:numero_transaccion>/', views.cambiar_estado_transaccion, name='cambiar_estado'),
    path('cancelar/<str:numero_transaccion>/', views.cancelar_transaccion, name='cancelar'),
    
    # ═══════════════════════════════════════════════════════════════
    # ALIAS (compatibilidad con código antiguo)
    # ═══════════════════════════════════════════════════════════════
    path('crear-desde-compra/', views.realizar_compra, name='crear_desde_compra'),  # Alias
    path('crear-desde-venta/', views.realizar_venta, name='crear_desde_venta'),  # Alias
]