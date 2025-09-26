# divisas/urls.py
from django.urls import path
from . import views
from .views import (
    DivisaListView, DivisaCreateView, DivisaUpdateView, DivisaToggleActivaView,
    TasaCambioListView, TasaCambioCreateView, TasaCambioAllListView,
    VentaDivisaView, VentaConfirmacionView, VentaMediosView
)

app_name = 'divisas'
urlpatterns = [
    path('', DivisaListView.as_view(), name='lista'),
    path('nueva/', DivisaCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', DivisaUpdateView.as_view(), name='editar'),
    path('<int:pk>/toggle/', DivisaToggleActivaView.as_view(), name='toggle'),

    # Tasas por divisa
    path('<int:divisa_id>/tasas/', TasaCambioListView.as_view(), name='tasas'),
    path('<int:divisa_id>/tasas/nueva/', TasaCambioCreateView.as_view(), name='tasa_nueva'),

    # Tabla histórica global (filtros por divisa y fechas)
    path('tasas/', TasaCambioAllListView.as_view(), name='tasas_global'),

    #Visualizador tasas
    path("tasas/actuales", views.visualizador_tasas, name="visualizador_tasas"),
    # Visualizador tasas - Administradores (todos los segmentos)
    path("tasas/admin/", views.visualizador_tasas_admin, name="visualizador_tasas_admin"),

    #Compra de divisas
    path("venta/", VentaDivisaView.as_view(), name="venta"),
    path("venta/confirmacion/", VentaConfirmacionView.as_view(), name="venta_confirmacion"),
    path("venta/medios/", VentaMediosView.as_view(), name="venta_medios"),

    # urls.py (app operaciones)
    path("venta/sumario/", views.SumarioOperacionView.as_view(), name="venta_sumario"),
    #Venta de divisas
    path('compra/', views.CompraDivisaView.as_view(), name='compra'),
    path('compra/confirmacion/', views.CompraConfirmacionView.as_view(), name='compra_confirmacion'),
    path('compra/sumario/', views.SumarioCompraView.as_view(), name='compra_sumario'),

    #Seleccionar operación
    path("operacion/", views.seleccionar_operacion_view, name="seleccionar_operacion"),    
]
