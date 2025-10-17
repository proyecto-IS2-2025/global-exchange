# terminal/urls.py
from django.urls import path
from . import views

app_name = 'tauser'

urlpatterns = [
# CRUD Terminales
    path('terminales/', views.TerminalListView.as_view(), name='terminal_list'),
    path('terminales/nueva/', views.TerminalCreateView.as_view(), name='terminal_create'),
    path('terminales/<int:pk>/', views.TerminalDetailView.as_view(), name='terminal_detail'),
    path('terminales/<int:pk>/editar/', views.TerminalUpdateView.as_view(), name='terminal_update'),
    path('terminales/<int:pk>/eliminar/', views.TerminalDeleteView.as_view(), name='terminal_delete'),
    path('terminales/<int:pk>/toggle/', views.toggle_terminal_activa, name='toggle_terminal_activa'),

    # Gestión de Inventario
    path('terminales/<int:terminal_pk>/inventario/', views.InventarioTerminalView.as_view(), name='inventario_terminal'),

    # Generación de PINs
    path('clientes/<int:cliente_id>/generar-pin/', views.generar_pin_cliente, name='generar_pin_cliente'),

    # Terminal de autoservicio (acceso público)
    path('<str:terminal_codigo>/', views.TerminalInicioView.as_view(), name='inicio_tauser'),
    path('<str:terminal_codigo>/cliente/<int:cliente_id>/', views.TransaccionesClienteView.as_view(), name='transacciones_cliente'),
    path('<str:terminal_codigo>/operacion/<str:transaccion_id>/', views.EjecutarOperacionView.as_view(), name='ejecutar_operacion'),
    path('<str:terminal_codigo>/cerrar-sesion/', views.CerrarSesionTerminalView.as_view(), name='cerrar_sesion'),

    # Inicio de terminal
    path('<str:terminal_codigo>/', views.TerminalInicioView.as_view(), name='inicio_tauser'),
    
    # Transacciones del cliente
    path('<str:terminal_codigo>/cliente/<int:cliente_id>/', 
         views.TransaccionesClienteView.as_view(), 
         name='transacciones_cliente'),
    
    # Ejecutar operación
    path('<str:terminal_codigo>/operacion/<str:transaccion_id>/', 
         views.EjecutarOperacionView.as_view(), 
         name='ejecutar_operacion'),
    
    # Cerrar sesión
    path('<str:terminal_codigo>/cerrar-sesion/', 
         views.CerrarSesionTerminalView.as_view(), 
         name='cerrar_sesion'),

     # Lista de terminales disponibles
    path('terminales/', views.lista_terminales, name='lista_terminales'),

     # Seleccionar un terminal específico
    path('terminales/<str:terminal_codigo>/seleccionar/', 
         views.seleccionar_terminal, 
         name='seleccionar_terminal'),
      # Inicio del terminal (ingreso de PIN)
    path('terminal/<str:terminal_codigo>/', 
         views.inicio_tauser, 
         name='inicio_tauser'),
    
    # Menú principal después de validar PIN
    path('terminal/<str:terminal_codigo>/menu/', 
         views.menu_principal, 
         name='menu_principal'),
    
    # Cerrar sesión del TAUSER
    path('terminal/<str:terminal_codigo>/cerrar/', 
         views.cerrar_sesion_tauser, 
         name='cerrar_sesion_tauser'),
]