# clientes/urls.py
from django.urls import path
from . import views
from .views import (
    ClienteCreateView,
    ClienteListView,
    ClienteUpdateView,
    ClienteDeleteView,
)

urlpatterns = [
    # URLs para la gestión de clientes
    path('clientes/', ClienteListView.as_view(), name='cliente_list'),
    path('clientes/add/', ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/edit/', ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/delete/', ClienteDeleteView.as_view(), name='cliente_delete'),
    # URLs asociar clientes-usuarios
    path('asociar_admin/', views.asociar_admin_view, name='asociar_admin'),
    path('listar_asociaciones/', views.listar_asociaciones, name='listar_asociaciones'),

]