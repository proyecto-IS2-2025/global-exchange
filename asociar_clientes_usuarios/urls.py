# asociar_clientes_usuarios/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('asociar_admin/', views.asociar_admin_view, name='asociar_admin'),
    path('listar_asociaciones/', views.listar_asociaciones, name='listar_asociaciones'),
]