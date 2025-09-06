# clientes/urls.py
app_name = 'clientes'
from django.urls import path
from . import views
from .views import DescuentoListView, DescuentoUpdateView, HistorialDescuentoListView
from .views import ClienteListView, ClienteUpdateView

"""
from .views import (
    ,
)
"""

urlpatterns = [
    # URLs para la gestión de clientes
    path('clientes/crear/', views.crear_cliente_view, name='crear_cliente'),
    
    # URLs asociar clientes-usuarios
    path('asociar_clientes_usuarios/', views.asociar_clientes_usuarios_view, name='asociar_clientes_usuarios'),
    path('listar_asociaciones/', views.listar_asociaciones, name='listar_asociaciones'),
    path("lista_clientes/", ClienteListView.as_view(), name="lista_clientes"),
    path("<int:pk>/editar/", ClienteUpdateView.as_view(), name="editar"),
    
    # URLs para la gestión de descuentos
    path('configuracion/descuentos/', DescuentoListView.as_view(), name='lista_descuentos'),
    path('configuracion/descuentos/<int:pk>/editar/', DescuentoUpdateView.as_view(), name='editar_descuento'),
    path('configuracion/descuentos/historial/', HistorialDescuentoListView.as_view(), name='historial_descuentos'),

]

"""
    path('lista_clientes/', views.lista_clientes, name='lista_clientes')
    path('clientes/', ClienteListView.as_view(), name='cliente_list'),
    path('clientes/add/', ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/edit/', ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/delete/', ClienteDeleteView.as_view(), name='cliente_delete'),
"""

