# clientes/urls.py
app_name = 'clientes'
from django.urls import path
from . import views
from .views import (
    # Vistas existentes
    DescuentoListView, DescuentoUpdateView, HistorialDescuentoListView,
    ClienteListView, ClienteUpdateView,

    # Vistas de medios de pago mejoradas
    ClienteMedioDePagoListView, ClienteMedioDePagoCreateView, ClienteMedioDePagoUpdateView,
    ClienteMedioDePagoToggleView, ClienteMedioDePagoDeleteView,
    select_medio_pago_view, medio_pago_detail_ajax, dashboard_medios_pago,
    exportar_medios_pago, verificar_duplicados_ajax, SeleccionarMedioAcreditacionView,
)

app_name = 'clientes'

urlpatterns = [
    # URLs para la gestión de clientes
    path('clientes/crear/', views.crear_cliente_view, name='crear_cliente'),
    path("lista_clientes/", ClienteListView.as_view(), name="lista_clientes"),
    path("<int:pk>/editar/", ClienteUpdateView.as_view(), name="editar"),

    # URLs asociar clientes-usuarios
    path('asociar_clientes_usuarios/', views.asociar_clientes_usuarios_view, name='asociar_clientes_usuarios'),
    path('listar_asociaciones/', views.listar_asociaciones, name='listar_asociaciones'),
    
    # URLs para la gestión de descuentos
    path('configuracion/descuentos/', DescuentoListView.as_view(), name='lista_descuentos'),
    path('configuracion/descuentos/<int:pk>/editar/', DescuentoUpdateView.as_view(), name='editar_descuento'),
    path('configuracion/descuentos/historial/', HistorialDescuentoListView.as_view(), name='historial_descuentos'),
    #Seleccionar cliente
    path("seleccionar/", views.seleccionar_cliente_view, name="seleccionar_cliente"),
    path("limites-diarios/", views.lista_limites_diarios, name="lista_limites_diarios"),
    path("limites-mensuales/", views.lista_limites_mensuales, name="lista_limites_mensuales"),
    path("limites-mensuales/nuevo/", views.crear_limite_mensual, name="crear_limite_mensual"),
    path("limites-diarios/nuevo/", views.crear_limite_diario, name="crear_limite_diario"),
    # URLs principales para medios de pago del cliente
    path('medios-pago/', ClienteMedioDePagoListView.as_view(), name='medios_pago_cliente'),
    path('medios-pago/dashboard/', dashboard_medios_pago, name='dashboard_medios_pago'),

    # Proceso de agregar medio de pago (2 pasos)
    path('medios-pago/seleccionar/', select_medio_pago_view, name='seleccionar_medio_pago'),
    path('medios-pago/agregar/<int:medio_id>/', ClienteMedioDePagoCreateView.as_view(), name='agregar_medio_pago'),

    # Gestión individual de medios de pago
    path('medios-pago/<int:pk>/editar/', ClienteMedioDePagoUpdateView.as_view(), name='editar_medio_pago'),
    path('medios-pago/<int:pk>/toggle/', ClienteMedioDePagoToggleView.as_view(), name='toggle_medio_pago'),
    path('medios-pago/<int:pk>/eliminar/', ClienteMedioDePagoDeleteView.as_view(), name='eliminar_medio_pago'),

    # Funcionalidades adicionales
    path('medios-pago/exportar/', exportar_medios_pago, name='exportar_medios_pago'),

    # APIs AJAX
    path('medios-pago/<int:pk>/detalle/', medio_pago_detail_ajax, name='detalle_medio_pago_ajax'),

    # AJAX para verificación de duplicados
    path('medios-pago/verificar-duplicados/', verificar_duplicados_ajax, name='verificar_duplicados_ajax'),

    # Agrega esta URL a tu urlpatterns
    path('seleccionar-medio-acreditacion/', SeleccionarMedioAcreditacionView.as_view(), name='seleccionar_medio_acreditacion'),

]