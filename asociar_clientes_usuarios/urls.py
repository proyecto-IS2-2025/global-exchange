# asociar_clientes_usuarios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('admin/asociar/', views.asociar_admin_view, name='asociar_admin'),
]