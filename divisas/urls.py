# divisas/urls.py
from django.urls import path
from . import views
from .views import (
    DivisaListView, DivisaCreateView, DivisaUpdateView, DivisaToggleActivaView,
    TasaCambioListView, TasaCambioCreateView, TasaCambioAllListView,
)

app_name = 'divisas'
urlpatterns = [
    path('', DivisaListView.as_view(), name='lista'),
    path('nueva/', DivisaCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', DivisaUpdateView.as_view(), name='editar'),
    path('<int:pk>/toggle/', DivisaToggleActivaView.as_view(), name='toggle'),

    # Tasas por divisa
    path('<int:divisa_id>/tasas/', TasaCambioListView.as_view(), name='tasas'),
    path('<int:divisa_id>/tasas/nueva/', TasaCambioCreateView.as_view(), name='tasa_nueva'),

    # Tabla histórica global (filtros por divisa y fechas)
    path('tasas/', TasaCambioAllListView.as_view(), name='tasas_global'),

    #Visualizador tasas
    path("tasas/actuales", views.visualizador_tasas, name="visualizador_tasas"),
    # Visualizador tasas - Administradores (todos los segmentos)
    path("tasas/admin/", views.visualizador_tasas_admin, name="visualizador_tasas_admin"),
    
    # Denominaciones
    #path('denominaciones/', views.DenominacionListView.as_view(), name='denominacion_list'),
    #path('denominaciones/nueva/', views.DenominacionCreateView.as_view(), name='denominacion_create'),
    #path('denominaciones/rapida/', views.DenominacionQuickCreateView.as_view(), name='denominacion_quick_create'),
    #path('denominaciones/<int:pk>/editar/', views.DenominacionUpdateView.as_view(), name='denominacion_form'),
    #path('denominaciones/<int:pk>/toggle/', views.DenominacionDeleteView.as_view(), name='denominacion_toggle'),
    #path('denominaciones/divisa/<int:divisa_id>/', views.DenominacionesDivisaView.as_view(), name='denominaciones_divisa'),
    #path('denominaciones/disponibles/<int:divisa_id>/json/', views.denominaciones_disponibles_json, name='denominaciones_json'),
    
    path('denominaciones/', views.DenominacionListView.as_view(), name='denominacion_list'),
    path('denominaciones/<int:divisa_id>/', views.DenominacionesDivisaView.as_view(), name='denominaciones_divisa'),
    path('denominaciones/nueva/', views.DenominacionCreateView.as_view(), name='denominacion_create'),
    path('denominaciones/rapida/', views.DenominacionQuickCreateView.as_view(), name='denominacion_quick_create'),
    path('denominaciones/editar/<int:pk>/', views.DenominacionUpdateView.as_view(), name='denominacion_form'),
    path('denominaciones/<int:pk>/toggle/', views.DenominacionDeleteView.as_view(), name='denominacion_toggle'),

    # Calculadora
    path('calculadora-denominaciones/', views.CalculadoraDenominacionesView.as_view(), name='calculadora_denominaciones'),
    
]
