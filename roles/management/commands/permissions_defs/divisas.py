# roles/management/commands/permissions_defs/divisas.py

"""
Definiciones de permisos personalizados para la app 'divisas'.
"""

PERMISOS_DIVISAS = [
    # ═══════════════════════════════════════════════════════════════════
    # COTIZACIONES Y VISUALIZACIÓN (CLIENTES)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'divisas',
        'model': 'cotizacionsegmento',
        'codename': 'view_cotizaciones_segmento',
        'name': 'Puede ver cotizaciones del segmento',
        'modulo': 'divisas',
        'descripcion': 'Permite consultar las cotizaciones disponibles para los segmentos asignados.',
        'ejemplo': 'Ver tasas preferenciales del segmento corporativo en el visualizador público.',
        'nivel_riesgo': 'bajo',
        'orden': 10,
        'categoria': 'consulta_cotizaciones',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'divisas',
        'model': 'cotizacionsegmento',
        'codename': 'manage_cotizaciones_segmento',
        'name': 'Puede gestionar cotizaciones por segmento',
        'modulo': 'divisas',
        'descripcion': 'Autoriza la visualización administrativa y gestión de cotizaciones de todos los segmentos.',
        'ejemplo': 'Acceder al panel administrativo de tasas y actualizar spreads por segmento.',
        'nivel_riesgo': 'alto',
        'orden': 20,
        'categoria': 'gestion_cotizaciones',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # OPERACIONES DE COMPRA/VENTA (CLIENTES)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'divisas',
        'model': 'divisa',
        'codename': 'realizar_operacion',
        'name': 'Puede realizar operaciones de compra/venta',
        'modulo': 'divisas',
        'descripcion': 'Permite ejecutar transacciones de cambio de divisas (compra/venta).',
        'ejemplo': 'Cliente compra USD 100 a la tasa del día para su segmento.',
        'nivel_riesgo': 'alto',
        'orden': 30,
        'categoria': 'operaciones',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # GESTIÓN ADMINISTRATIVA DE DIVISAS (ABM)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'divisas',
        'model': 'divisa',
        'codename': 'manage_divisas',
        'name': 'Puede gestionar divisas del sistema',
        'modulo': 'divisas',
        'descripcion': 'Permite crear, editar, activar y desactivar divisas disponibles para operaciones.',
        'ejemplo': 'Un administrador activa la divisa "EUR" después de configurar sus tasas base.',
        'nivel_riesgo': 'alto',
        'orden': 40,
        'categoria': 'administracion',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'divisas',
        'model': 'divisa',
        'codename': 'view_divisas',
        'name': 'Puede visualizar divisas del sistema',
        'modulo': 'divisas',
        'descripcion': 'Permite ver el listado de divisas configuradas sin poder modificarlas.',
        'ejemplo': 'Un observador consulta las divisas activas e inactivas del sistema.',
        'nivel_riesgo': 'bajo',
        'orden': 50,
        'categoria': 'visualizacion',
        'requiere_auditoria': False,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # GESTIÓN DE TASAS DE CAMBIO
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'divisas',
        'model': 'tasacambio',
        'codename': 'manage_tasas_cambio',
        'name': 'Puede gestionar tasas de cambio',
        'modulo': 'divisas',
        'descripcion': 'Permite registrar nuevas tasas de cambio para divisas (precio base, comisiones).',
        'ejemplo': 'Un operador registra la tasa del dólar del día: 7.200 PYG con 2% de comisión.',
        'nivel_riesgo': 'critico',
        'orden': 60,
        'categoria': 'gestion_tasas',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'divisas',
        'model': 'tasacambio',
        'codename': 'view_tasas_cambio',
        'name': 'Puede ver historial de tasas de cambio',
        'modulo': 'divisas',
        'descripcion': 'Permite consultar el historial de tasas registradas sin poder modificar.',
        'ejemplo': 'Un observador consulta la evolución del tipo de cambio USD/PYG del último mes.',
        'nivel_riesgo': 'bajo',
        'orden': 70,
        'categoria': 'consulta_tasas',
        'requiere_auditoria': False,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # PERMISOS COMENTADOS - FUNCIONALIDAD NO IMPLEMENTADA AÚN
    # ═══════════════════════════════════════════════════════════════════
    
    # TODO: Implementar vista de aprobación de operaciones de alto monto
    # {
    #     'app_label': 'divisas',
    #     'model': 'divisa',
    #     'codename': 'approve_operaciones_divisas',
    #     'name': 'Puede aprobar operaciones de divisas',
    #     'modulo': 'divisas',
    #     'descripcion': 'Habilita la aprobación de operaciones superiores al límite estándar.',
    #     'ejemplo': 'Aprobar la compra de USD 50.000 para el cliente ACME (requiere doble autorización).',
    #     'nivel_riesgo': 'critico',
    #     'orden': 80,
    #     'categoria': 'aprobaciones',
    #     'requiere_auditoria': True,
    # },
    
    # TODO: Implementar dashboard de reportes consolidados
    # {
    #     'app_label': 'divisas',
    #     'model': 'divisa',
    #     'codename': 'view_reportes_divisas',
    #     'name': 'Puede ver reportes consolidados de divisas',
    #     'modulo': 'divisas',
    #     'descripcion': 'Permite acceder a tableros y reportes de operaciones y posiciones.',
    #     'ejemplo': 'Descargar el reporte semanal de operaciones de divisas en formato Excel.',
    #     'nivel_riesgo': 'medio',
    #     'orden': 90,
    #     'categoria': 'reportes',
    #     'requiere_auditoria': False,
    # },
]