from django.urls import path
from . import views

app_name = 'ganancias'

urlpatterns = [
    path('tablero/', views.tablero_ganancias, name='tablero'),
    path('comparacion/', views.comparacion_periodos, name='comparacion'),
    path('api/evolucion/', views.api_ganancias_evolucion, name='api_evolucion'),
    path('api/por-divisa/', views.api_ganancias_por_divisa, name='api_por_divisa'),
    path('actualizar/', views.actualizar_ganancias, name='actualizar'),
    path('exportar-excel/', views.exportar_ganancias_excel, name='exportar_excel'),
]
