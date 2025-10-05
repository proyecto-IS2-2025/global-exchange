# roles/management/commands/permissions_defs/divisas.py

"""
Definiciones de permisos personalizados para la app 'divisas'.
"""

PERMISOS_DIVISAS = [
    # ═══════════════════════════════════════════════════════════════════
    # COTIZACIONES Y VISUALIZACIÓN
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
    # OPERACIONES DE COMPRA/VENTA
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
    #     'orden': 40,
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
    #     'orden': 50,
    #     'categoria': 'reportes',
    #     'requiere_auditoria': False,
    # },
]