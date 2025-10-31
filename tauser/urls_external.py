"""
URLs externas para acceso público al sistema TAUSER.
Este módulo está separado para diferenciar el acceso externo (público)
del acceso administrativo interno (casa de cambios).
"""
from django.urls import path
from . import views_external

app_name = 'tauser_external'

urlpatterns = [
    # ==================== PANTALLA PRINCIPAL TAUSER ====================
    path(
        '',
        views_external.tauser_home,
        name='home'
    ),
    
    # ==================== SELECCIÓN DE TERMINAL ====================
    path(
        'seleccionar/',
        views_external.seleccionar_terminal_externo,
        name='seleccionar_terminal'
    ),
    
    # ==================== ACCESO CON PIN ====================
    path(
        'terminal/<str:terminal_codigo>/acceso/',
        views_external.acceso_terminal,
        name='acceso_terminal'
    ),
    
    # ==================== MENÚ PRINCIPAL ====================
    path(
        'terminal/<str:terminal_codigo>/menu/',
        views_external.menu_tauser,
        name='menu_tauser'
    ),
    
    # ==================== VERIFICAR CÓDIGO TAUSER ====================
    path(
        'terminal/<str:terminal_codigo>/verificar-codigo/',
        views_external.verificar_codigo_tauser,
        name='verificar_codigo'
    ),
    
    # ==================== MFA PARA ACCESO A TRANSACCIÓN ====================
    path(
        'terminal/<str:terminal_codigo>/mfa/',
        views_external.mfa_transaccion,
        name='mfa_transaccion'
    ),
    path(
        'terminal/<str:terminal_codigo>/mfa/reenviar/',
        views_external.reenviar_mfa,
        name='reenviar_mfa'
    ),
    
    # ==================== VISTAS DE DETALLE ====================
    path(
        'terminal/<str:terminal_codigo>/detalle/retiro/',
        views_external.mostrar_detalle_retiro,
        name='mostrar_detalle_retiro'
    ),
    path(
        'terminal/<str:terminal_codigo>/detalle/deposito/',
        views_external.mostrar_detalle_deposito,
        name='mostrar_detalle_deposito'
    ),
    
    # ==================== TRANSACCIONES ====================
    path(
        'terminal/<str:terminal_codigo>/transacciones/',
        views_external.ver_transacciones,
        name='ver_transacciones'
    ),
    
    # ==================== OPERACIONES (RETIRO/PAGO) ====================
    path(
        'terminal/<str:terminal_codigo>/retiro/<int:transaccion_id>/',
        views_external.procesar_retiro,
        name='procesar_retiro'
    ),
    path(
        'terminal/<str:terminal_codigo>/pago/<int:transaccion_id>/',
        views_external.procesar_pago,
        name='procesar_pago'
    ),
    
    # ==================== PANTALLA DE ÉXITO ====================
    path(
        'terminal/<str:terminal_codigo>/retiro-exitoso/',
        views_external.retiro_exitoso,
        name='retiro_exitoso'
    ),
    
    # ==================== REPOSICIÓN (NUEVO) ====================
    path(
        'terminal/<str:terminal_codigo>/reposicion/',
        views_external.menu_reposicion,
        name='menu_reposicion'
    ),
    path(
        'terminal/<str:terminal_codigo>/reposicion/ejecutar/',
        views_external.ejecutar_reposicion,
        name='ejecutar_reposicion'
    ),
    
    # ==================== GESTIÓN DE INVENTARIO POR DENOMINACIONES ====================
    path(
        'terminales/<int:terminal_pk>/inventario-denominaciones/',
        views_external.gestion_inventario_denominaciones,
        name='gestion_inventario_denominaciones'
    ),
    
    # ==================== REABASTECIMIENTO (SISTEMA PÚBLICO) ====================
    path(
        'terminal/<str:terminal_codigo>/dashboard-inventario/',
        views_external.dashboard_inventario_externo,
        name='dashboard_inventario'
    ),
    path(
        'terminal/<str:terminal_codigo>/recarga-masiva/',
        views_external.recarga_masiva_externo,
        name='recarga_masiva'
    ),
    path(
        'terminal/<str:terminal_codigo>/historial-recargas/',
        views_external.historial_recargas_externo,
        name='historial_recargas'
    ),
    
    # ==================== CERRAR SESIÓN ====================
    path(
        'terminal/<str:terminal_codigo>/cerrar/',
        views_external.cerrar_sesion_external,
        name='cerrar_sesion'
    ),
]
