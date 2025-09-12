# simulador/urls.py
from django.urls import path
from . import views

app_name = 'simulador'  # Esto es opcional, pero buena práctica
urlpatterns = [
    path('', views.simulador_view, name='simulador'),
    # Nueva URL para la API
    path('calcular/', views.calcular_simulacion_api, name='calcular_simulacion_api'),
]