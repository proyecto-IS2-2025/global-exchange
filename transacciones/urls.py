# transacciones/urls.py
from django.urls import path
from . import views

app_name = 'transacciones'

urlpatterns = [
    # Crear transacción
    path('crear-desde-venta/', views.crear_transaccion_desde_venta, name='crear_desde_venta'),
    
    # Confirmación
    path('confirmacion/<str:numero_transaccion>/', views.confirmacion_operacion, name='confirmacion_operacion'),
    
    # Historial cliente
    path('historial/', views.HistorialTransaccionesClienteView.as_view(), name='historial_cliente'),
    
    # Historial administrativo
    path('admin/historial/', views.historial_admin, name='historial_admin'),
    
    # Detalle de transacción
    path('detalle/<str:numero_transaccion>/', views.DetalleTransaccionView.as_view(), name='detalle'),
    
    # Gestión de estados (admin)
    path('cambiar-estado/<str:numero_transaccion>/', views.cambiar_estado_transaccion, name='cambiar_estado'),
    
    # Cancelar transacción (cliente)
    path('cancelar/<str:numero_transaccion>/', views.cancelar_transaccion, name='cancelar'),

    #Crear transacción
    path('crear-desde-compra/', views.crear_transaccion_desde_compra, name='crear_desde_compra'),

]