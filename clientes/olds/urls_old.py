
# clientes/urls.py
app_name = 'clientes'
from django.urls import path, include
from . import views
from .views_old import (
    # Vistas Basadas en Clase Genericas
    DescuentoListView, DescuentoUpdateView, HistorialDescuentoListView,
    ClienteListView, ClienteUpdateView,

    # CLASES DE EDICIÓN DE LÍMITES (Nombres corregidos para coincidir con views.py)
    LimiteDiarioUpdateView,    
    LimiteMensualUpdateView,   
    
    # Vistas de Medios de Pago
    ClienteMedioDePagoListView, ClienteMedioDePagoCreateView, ClienteMedioDePagoUpdateView,
    ClienteMedioDePagoToggleView, ClienteMedioDePagoDeleteView,
    SeleccionarMedioAcreditacionView,
    
    # Funciones de Vistas (FBV) para Medios de Pago y AJAX
    select_medio_pago_view, medio_pago_detail_ajax, dashboard_medios_pago,
    exportar_medios_pago, verificar_duplicados_ajax,
)

app_name = 'clientes'

urlpatterns = [
    # -----------------------------------------------------
    # 1. URLs para Clientes
    # -----------------------------------------------------
    path('clientes/crear/', views.crear_cliente_view, name='crear_cliente'),
    path("lista_clientes/", ClienteListView.as_view(), name="lista_clientes"),
    path("<int:pk>/editar/", ClienteUpdateView.as_view(), name="editar"),
    path("seleccionar/", views.seleccionar_cliente_view, name="seleccionar_cliente"),

    # -----------------------------------------------------
    # 2. URLs de Asociación Cliente-Usuario
    # -----------------------------------------------------
    path('asociar_clientes_usuarios/', views.asociar_clientes_usuarios_view, name='asociar_clientes_usuarios'),
    path('listar_asociaciones/', views.listar_asociaciones, name='listar_asociaciones'),
    
    # -----------------------------------------------------
    # 3. URLs para Descuentos
    # -----------------------------------------------------
    path('configuracion/descuentos/', DescuentoListView.as_view(), name='lista_descuentos'),
    path('configuracion/descuentos/<int:pk>/editar/', DescuentoUpdateView.as_view(), name='editar_descuento'),
    path('configuracion/descuentos/historial/', HistorialDescuentoListView.as_view(), name='historial_descuentos'),
    
    # -----------------------------------------------------
    # 4. URLs para Límites Diarios y Mensuales
    # -----------------------------------------------------
    # Limites Diarios
    path("limites-diarios/", views.lista_limites_diarios, name="lista_limites_diarios"),
    path("limites-diarios/nuevo/", views.crear_limite_diario, name="crear_limite_diario"),
    # RUTA FINAL CORREGIDA
    path("limites-diarios/<int:pk>/editar/", LimiteDiarioUpdateView.as_view(), name="editar_limite_diario"), 
    
    # Limites Mensuales
    path("limites-mensuales/", views.lista_limites_mensuales, name="lista_limites_mensuales"),
    path("limites-mensuales/nuevo/", views.crear_limite_mensual, name="crear_limite_mensual"),
    # RUTA FINAL CORREGIDA
    path("limites-mensuales/<int:pk>/editar/", LimiteMensualUpdateView.as_view(), name="editar_limite_mensual"), 

    # -----------------------------------------------------
    # 5. URLs para Medios de Pago
    # -----------------------------------------------------
    path('medios-pago/', ClienteMedioDePagoListView.as_view(), name='medios_pago_cliente'),
    path('medios-pago/dashboard/', dashboard_medios_pago, name='dashboard_medios_pago'),

    # Proceso de agregar medio de pago
    path('medios-pago/seleccionar/', select_medio_pago_view, name='seleccionar_medio_pago_crear'),
    path('medios-pago/agregar/<int:medio_id>/', ClienteMedioDePagoCreateView.as_view(), name='agregar_medio_pago'),

    # Gestión individual de medios de pago
    path('medios-pago/<int:pk>/editar/', ClienteMedioDePagoUpdateView.as_view(), name='editar_medio_pago'),
    path('medios-pago/<int:pk>/toggle/', ClienteMedioDePagoToggleView.as_view(), name='toggle_medio_pago'),
    path('medios-pago/<int:pk>/eliminar/', ClienteMedioDePagoDeleteView.as_view(), name='eliminar_medio_pago'),

    # Funcionalidades adicionales y AJAX
    path('medios-pago/exportar/', exportar_medios_pago, name='exportar_medios_pago'),
    path('medios-pago/<int:pk>/detalle/', medio_pago_detail_ajax, name='detalle_medio_pago_ajax'),
    path('medios-pago/verificar-duplicados/', verificar_duplicados_ajax, name='verificar_duplicados_ajax'),
    path('seleccionar-medio-acreditacion/', SeleccionarMedioAcreditacionView.as_view(), name='seleccionar_medio_acreditacion'),

    #Seleccionar medio de pago
    path('seleccionar-medio-pago/', views.SeleccionarMedioPagoView.as_view(), name='seleccionar_medio_pago'),


]
