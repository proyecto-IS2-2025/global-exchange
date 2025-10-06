# notificaciones/urls.py

from django.urls import path
from . import views

# Define el nombre de la aplicación para usarlo en reversos de URL (ej: notificaciones:gestion_notificaciones)
app_name = 'notificaciones'

urlpatterns = [
    # GESTIÓN DE NOTIFICACIONES DE TASAS

    # La vista principal (Listado y Formularios de Configuración)
    path('', views.GestionNotificacionesView.as_view(), name='gestion_notificaciones'),

    # Acciones individuales
    path('toggle/<int:pk>/', views.toggle_notificacion, name='toggle_notificacion'),
    path('eliminar/<int:pk>/', views.eliminar_notificacion, name='eliminar_notificacion'),
    path('marcar-leida/<int:pk>/', views.marcar_leida, name='marcar_leida'),

]