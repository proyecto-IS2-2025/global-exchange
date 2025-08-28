# clientes/urls.py
from django.urls import path
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
]