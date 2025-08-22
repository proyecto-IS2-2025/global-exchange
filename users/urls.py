# users/urls.py
from django.urls import path
from .views import (
    CustomUserCreateView,
    CustomUserListView,
    CustomUserUpdateView,
    CustomUserDeleteView,
    ClienteCreateView,
    ClienteListView,
    ClienteUpdateView,
    ClienteDeleteView,
)

urlpatterns = [
    # URLs para la gestión de usuarios
    path('users/', CustomUserListView.as_view(), name='user_list'),
    path('users/add/', CustomUserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', CustomUserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', CustomUserDeleteView.as_view(), name='user_delete'),

    # URLs para la gestión de clientes
    path('clientes/', ClienteListView.as_view(), name='cliente_list'),
    path('clientes/add/', ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/edit/', ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/delete/', ClienteDeleteView.as_view(), name='cliente_delete'),
]