# asociar_clientes_usuarios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('seleccionar_cliente/', views.seleccion_cliente_view, name='seleccionar_cliente'),
    path('admin/asociar/', views.asociar_admin_view, name='asociar_admin'),
    path('seleccionar_cliente/<int:cliente_id>/', views.guardar_seleccion_cliente, name='guardar_seleccion_cliente'),
    path('', views.home_view, name='home'),
]