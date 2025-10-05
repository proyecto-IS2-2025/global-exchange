# roles/management/commands/permissions_defs/clientes.py
"""
Definiciones de permisos personalizados para la app 'clientes'.
"""

PERMISOS_CLIENTES = [
    # ═══════════════════════════════════════════════════════════════════
    # VISUALIZACIÓN Y ASIGNACIÓN DE CLIENTES
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'clientes',
        'model': 'cliente',
        'codename': 'view_assigned_clientes',
        'name': 'Puede ver clientes asignados',
        'modulo': 'clientes',
        'descripcion': 'Permite ver únicamente los clientes asignados al usuario actual.',
        'ejemplo': 'Un operador puede listar y gestionar solo los clientes que le fueron asignados.',
        'nivel_riesgo': 'bajo',
        'orden': 10,
        'categoria': 'visualizacion',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'clientes',
        'model': 'cliente',
        'codename': 'view_all_clientes',
        'name': 'Puede ver todos los clientes',
        'modulo': 'clientes',
        'descripcion': 'Permite visualizar el listado completo de clientes sin restricciones.',
        'ejemplo': 'Un administrador puede acceder al directorio completo de clientes del sistema.',
        'nivel_riesgo': 'medio',
        'orden': 20,
        'categoria': 'visualizacion',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'clientes',
        'model': 'asignacioncliente',
        'codename': 'manage_cliente_assignment',
        'name': 'Puede asignar clientes a operadores',
        'modulo': 'clientes',
        'descripcion': 'Permite crear, modificar y eliminar asignaciones de clientes a operadores.',
        'ejemplo': 'Un administrador asigna 5 clientes nuevos al operador Juan Pérez.',
        'nivel_riesgo': 'alto',
        'orden': 30,
        'categoria': 'gestion_asignaciones',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # LÍMITES DE OPERACIÓN
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'clientes',
        'model': 'limitediario',  # ← CORREGIDO
        'codename': 'manage_limites_operacion',
        'name': 'Puede modificar límites diarios y mensuales',
        'modulo': 'clientes',
        'descripcion': 'Permite ajustar los límites de transacciones diarias y mensuales de un cliente.',
        'ejemplo': 'Un administrador aumenta el límite mensual de USD 5,000 a USD 10,000 para un cliente VIP.',
        'nivel_riesgo': 'critico',
        'orden': 40,
        'categoria': 'gestion_limites',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'clientes',
        'model': 'limitediario',  # ← CORREGIDO
        'codename': 'view_limites_operacion',
        'name': 'Puede ver límites diarios y mensuales',
        'modulo': 'clientes',
        'descripcion': 'Permite consultar los límites de transacciones sin modificarlos.',
        'ejemplo': 'Un operador verifica si su cliente puede realizar una operación de USD 3,000.',
        'nivel_riesgo': 'bajo',
        'orden': 50,
        'categoria': 'consulta_limites',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'clientes',
        'model': 'limitemensual',  # ← CORREGIDO (usar modelo diferente para admin)
        'codename': 'admin_manage_limites',
        'name': 'Puede administrar límites diarios y mensuales',
        'modulo': 'clientes',
        'descripcion': 'Permiso administrativo completo para gestionar límites del sistema.',
        'ejemplo': 'Un administrador puede resetear límites de todos los clientes al inicio del mes.',
        'nivel_riesgo': 'critico',
        'orden': 60,
        'categoria': 'administracion_limites',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # MEDIOS DE PAGO DEL CLIENTE
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'clientes',
        'model': 'clientemediodepago',
        'codename': 'manage_medios_pago',
        'name': 'Puede gestionar medios de pago del cliente',
        'modulo': 'clientes',
        'descripcion': 'Permite agregar, editar o eliminar medios de pago asociados a un cliente.',
        'ejemplo': 'Un operador registra la cuenta bancaria del Banco Itaú para su cliente.',
        'nivel_riesgo': 'alto',
        'orden': 70,
        'categoria': 'gestion_medios_pago',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'clientes',
        'model': 'clientemediodepago',
        'codename': 'view_medios_pago',
        'name': 'Puede ver medios de pago del cliente',
        'modulo': 'clientes',
        'descripcion': 'Permite consultar los medios de pago registrados sin modificarlos.',
        'ejemplo': 'Un operador verifica qué cuentas tiene registradas un cliente para acreditar fondos.',
        'nivel_riesgo': 'medio',
        'orden': 80,
        'categoria': 'consulta_medios_pago',
        'requiere_auditoria': False,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # EXPORTACIÓN Y REPORTES
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'clientes',
        'model': 'cliente',
        'codename': 'export_clientes',
        'name': 'Puede exportar datos de clientes',
        'modulo': 'clientes',
        'descripcion': 'Permite descargar listados de clientes en formatos CSV, Excel o PDF.',
        'ejemplo': 'Un administrador exporta el reporte de clientes activos del mes para análisis.',
        'nivel_riesgo': 'medio',
        'orden': 90,
        'categoria': 'reportes',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # DESCUENTOS POR SEGMENTO
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'clientes',
        'model': 'descuento',  # ← CORREGIDO
        'codename': 'view_descuentos_segmento',
        'name': 'Puede ver descuentos por segmento',
        'modulo': 'clientes',
        'descripcion': 'Permite consultar los descuentos y tarifas preferenciales por segmento.',
        'ejemplo': 'Un operador verifica el descuento aplicable para clientes del segmento VIP.',
        'nivel_riesgo': 'bajo',
        'orden': 100,
        'categoria': 'consulta_descuentos',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'clientes',
        'model': 'descuento',  # ← CORREGIDO
        'codename': 'manage_descuentos_segmento',
        'name': 'Puede administrar descuentos por segmento',
        'modulo': 'clientes',
        'descripcion': 'Permite crear, modificar y eliminar configuraciones de descuentos por segmento.',
        'ejemplo': 'Un administrador crea un descuento del 15% para el segmento corporativo.',
        'nivel_riesgo': 'critico',
        'orden': 110,
        'categoria': 'administracion_descuentos',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'clientes',
        'model': 'historialdescuentos',  # ← CORREGIDO
        'codename': 'view_historial_descuentos',
        'name': 'Puede ver el historial de descuentos',
        'modulo': 'clientes',
        'descripcion': 'Permite consultar el registro histórico de cambios en descuentos.',
        'ejemplo': 'Un supervisor revisa cuándo se modificó el descuento del segmento premium.',
        'nivel_riesgo': 'bajo',
        'orden': 120,
        'categoria': 'auditoria_descuentos',
        'requiere_auditoria': False,
    },
]