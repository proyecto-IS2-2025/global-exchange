# clientes/urls.py
app_name = 'clientes'
from django.urls import path
from . import views
from .views import ComisionListView, ComisionUpdateView, HistorialComisionListView

urlpatterns = [
    # URLs para la gestión de clientes
    path('clientes/crear/', views.crear_cliente_view, name='crear_cliente'),
    
    # URLs asociar clientes-usuarios
    path('asociar_clientes_usuarios/', views.asociar_clientes_usuarios_view, name='asociar_clientes_usuarios'),
    path('listar_asociaciones/', views.listar_asociaciones, name='listar_asociaciones'),
    path('lista_clientes/', views.lista_clientes, name='lista_clientes'),
    
    # URLs para la nueva gestión de comisiones
    path('configuracion/comisiones/', ComisionListView.as_view(), name='lista_comisiones'),
    path('configuracion/comisiones/<int:pk>/editar/', ComisionUpdateView.as_view(), name='editar_comision'),
    # Nueva URL para el historial
    path('configuracion/comisiones/historial/', HistorialComisionListView.as_view(), name='historial_comisiones'),
]