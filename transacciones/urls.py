# transactions/urls.py
from django.urls import path
from . import views
from simulador import views as simulador_views

urlpatterns = [
    path('iniciar/', views.iniciar_transaccion, name='iniciar_transaccion'),
    path('previsualizar/', views.previsualizar_transaccion, name='previsualizar_transaccion'),
    path('confirmar/', views.confirmar_transaccion, name='confirmar_transaccion'),
    path('exitosa/', views.transaccion_exitosa, name='transaccion_exitosa'),
    path('simulador/', simulador_views.simulador_view, name='visualizador'),
    path('historial/', views.historial_transacciones, name='historial'),
]