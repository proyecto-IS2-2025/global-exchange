# operaciones_divisas/urls.py
from django.urls import path
from . import views
from .views import (
    VentaDivisaView, VentaConfirmacionView
)

app_name = 'operacion_divisas'
urlpatterns = [
    #Compra de divisas
    path("venta/", VentaDivisaView.as_view(), name="venta"),
    path("venta/confirmacion/", VentaConfirmacionView.as_view(), name="venta_confirmacion"),

    # urls.py (app operaciones)
    path("venta/sumario/", views.SumarioVentaView.as_view(), name="venta_sumario"),
    #Venta de divisas
    path('compra/', views.CompraDivisaView.as_view(), name='compra'),
    path('compra/confirmacion/', views.CompraConfirmacionView.as_view(), name='compra_confirmacion'),
    path('compra/sumario/', views.SumarioCompraView.as_view(), name='compra_sumario'),

    #Seleccionar operación
    path("operacion/", views.seleccionar_operacion_view, name="seleccionar_operacion"),    
]
