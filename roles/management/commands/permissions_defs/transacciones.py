"""
Definiciones de permisos personalizados para la app 'transacciones'.
"""

PERMISOS_TRANSACCIONES = [
    # ═══════════════════════════════════════════════════════════════════
    # VISUALIZACIÓN DE TRANSACCIONES
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'transacciones',
        'model': 'transaccion',
        'codename': 'view_transacciones_asignadas',
        'name': 'Puede ver transacciones de clientes asignados',
        'modulo': 'transacciones',
        'descripcion': 'Permite visualizar transacciones únicamente de los clientes asignados al usuario.',
        'ejemplo': 'Un operador revisa el historial de operaciones de sus 10 clientes asignados.',
        'nivel_riesgo': 'bajo',
        'orden': 10,
        'categoria': 'visualizacion_transacciones',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'transacciones',
        'model': 'transaccion',
        'codename': 'view_transacciones_globales',
        'name': 'Puede ver TODAS las transacciones del sistema',
        'modulo': 'transacciones',
        'descripcion': 'Permite acceder al historial completo de transacciones sin restricciones.',
        'ejemplo': 'Un administrador audita todas las operaciones del último trimestre.',
        'nivel_riesgo': 'medio',
        'orden': 20,
        'categoria': 'visualizacion_global',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # GESTIÓN DE ESTADOS
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'transacciones',
        'model': 'transaccion',
        'codename': 'manage_estados_transacciones',
        'name': 'Puede cambiar estados de transacciones',
        'modulo': 'transacciones',
        'descripcion': 'Permite modificar el estado de una transacción (pendiente → pagada → completada).',
        'ejemplo': 'Un operador marca como "pagada" una transacción tras confirmar el depósito.',
        'nivel_riesgo': 'alto',
        'orden': 30,
        'categoria': 'gestion_estados',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'transacciones',
        'model': 'transaccion',
        'codename': 'manage_reversiones_transacciones',
        'name': 'Puede revertir/anular transacciones',
        'modulo': 'transacciones',
        'descripcion': 'Permite anular transacciones completadas (reversión de operación).',
        'ejemplo': 'Un supervisor anula una transacción por error en el monto acreditado.',
        'nivel_riesgo': 'critico',
        'orden': 40,
        'categoria': 'reversiones',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'transacciones',
        'model': 'transaccion',
        'codename': 'cancel_propias_transacciones',
        'name': 'Puede cancelar sus propias transacciones pendientes',
        'modulo': 'transacciones',
        'descripcion': 'Permite al cliente cancelar transacciones en estado "pendiente".',
        'ejemplo': 'Un cliente cancela su compra de USD 500 porque cambió de opinión.',
        'nivel_riesgo': 'bajo',
        'orden': 50,
        'categoria': 'cancelacion_propia',
        'requiere_auditoria': False,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # AUDITORÍA Y REPORTES
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'transacciones',
        'model': 'historialtransaccion',
        'codename': 'view_historial_transacciones',
        'name': 'Puede ver historial de cambios de transacciones',
        'modulo': 'transacciones',
        'descripcion': 'Permite consultar el log de modificaciones y cambios de estado.',
        'ejemplo': 'Un auditor revisa quién cambió el estado de una transacción y cuándo.',
        'nivel_riesgo': 'bajo',
        'orden': 60,
        'categoria': 'auditoria',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'transacciones',
        'model': 'transaccion',
        'codename': 'export_transacciones',
        'name': 'Puede exportar transacciones a CSV/Excel',
        'modulo': 'transacciones',
        'descripcion': 'Permite descargar reportes de transacciones en formatos estructurados.',
        'ejemplo': 'Un administrador exporta el reporte mensual de transacciones para contabilidad.',
        'nivel_riesgo': 'medio',
        'orden': 70,
        'categoria': 'reportes',
        'requiere_auditoria': True,
    },
]