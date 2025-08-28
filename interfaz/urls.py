# interfaz/urls.py

from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import crear_cliente_admin
from autenticacion.views import registro_usuario
from autenticacion.views import verificar_correo
from autenticacion.views import login_view

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("registro/", registro_usuario, name="registro"),
    path("contacto/", views.contacto, name="contacto"),
    path('verificar/<str:token>/', verificar_correo, name='verificar_correo'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='inicio'), name='logout'),
    path('panel_admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # Rutas para los dashboards
    path('cliente/dashboard/', views.cliente_dashboard, name='cliente_dashboard'),
    #path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('panel_admin/', views.dashboard, name='admin_dashboard'),
    path("dashboard/", views.dashboard, name="dashboard_admin"),
    path('cambista/dashboard/', views.cambista_dashboard, name='cambista_dashboard'),

    #Opciones de administrador
    path('admin/crear-cliente/', crear_cliente_admin, name='crear_cliente_admin'),
]