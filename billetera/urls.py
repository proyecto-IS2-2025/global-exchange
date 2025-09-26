# billetera/urls.py
from django.urls import path
from . import views

app_name = 'billetera'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('crear-billetera/', views.crear_billetera, name='crear_billetera'),
    path('recargar/', views.recargar, name='recargar'),
    path('transferir/', views.transferir, name='transferir'),
    path('historial/', views.historial, name='historial'),
    path('api/comprobante/', views.comprobante_ajax, name='comprobante_ajax'),
]