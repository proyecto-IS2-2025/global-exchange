"""
URLs para el módulo de Facturación Electrónica
"""
from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    # Listados
    path('', views.lista_facturas, name='lista'),
    path('mis-facturas/', views.mis_facturas, name='mis_facturas'),
    
    # Detalle
    path('<int:factura_id>/', views.detalle_factura, name='detalle_factura'),
    
    # Generación
    path('generar/<int:transaccion_id>/', views.generar_factura, name='generar'),
    
    # Descargas
    path('<int:factura_id>/pdf/', views.descargar_pdf, name='descargar_pdf'),
    path('<int:factura_id>/xml/', views.descargar_xml, name='descargar_xml'),
    
    # Sincronización
    path('<int:factura_id>/actualizar-estado/', views.actualizar_estado, name='actualizar_estado'),
    
    # Anulación
    path('<int:factura_id>/cancelar/', views.cancelar_factura, name='cancelar'),
    
    # Reportes
    path('reporte/', views.reporte_facturacion, name='reporte'),
]
