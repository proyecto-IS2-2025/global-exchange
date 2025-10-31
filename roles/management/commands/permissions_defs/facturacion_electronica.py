"""
Definiciones de permisos personalizados para la app 'facturacion_electronica'.
"""

PERMISOS_FACTURACION = [
    # ═══════════════════════════════════════════════════════════════════
    # VISUALIZACIÓN DE FACTURAS
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'view_facturas_propias',
        'name': 'Puede ver sus propias facturas electrónicas',
        'modulo': 'facturacion',
        'descripcion': 'Permite al cliente ver únicamente las facturas electrónicas de sus propias transacciones.',
        'ejemplo': 'Un cliente descarga el PDF de la factura de su compra de USD.',
        'nivel_riesgo': 'bajo',
        'orden': 10,
        'categoria': 'visualizacion_facturas',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'view_facturas_asignadas',
        'name': 'Puede ver facturas de clientes asignados',
        'modulo': 'facturacion',
        'descripcion': 'Permite visualizar facturas de los clientes asignados al operador.',
        'ejemplo': 'Un operador revisa las facturas emitidas a sus clientes asignados.',
        'nivel_riesgo': 'bajo',
        'orden': 20,
        'categoria': 'visualizacion_facturas',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'view_todas_facturas',
        'name': 'Puede ver TODAS las facturas del sistema',
        'modulo': 'facturacion',
        'descripcion': 'Permite acceder al registro completo de facturas electrónicas del sistema.',
        'ejemplo': 'Un supervisor audita todas las facturas emitidas en el mes.',
        'nivel_riesgo': 'medio',
        'orden': 30,
        'categoria': 'visualizacion_global',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # GENERACIÓN DE FACTURAS
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'generar_factura',
        'name': 'Puede generar facturas electrónicas',
        'modulo': 'facturacion',
        'descripcion': 'Permite emitir facturas electrónicas para transacciones completadas.',
        'ejemplo': 'Un operador genera la factura para una transacción de cambio de EUR.',
        'nivel_riesgo': 'alto',
        'orden': 40,
        'categoria': 'emision_facturas',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'generar_factura_manual',
        'name': 'Puede generar facturas manualmente',
        'modulo': 'facturacion',
        'descripcion': 'Permite crear facturas electrónicas de forma manual (sin transacción asociada).',
        'ejemplo': 'Un administrador emite una factura por un servicio especial.',
        'nivel_riesgo': 'critico',
        'orden': 50,
        'categoria': 'emision_manual',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # ANULACIÓN Y CORRECCIÓN
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'cancelar_factura',
        'name': 'Puede cancelar/anular facturas electrónicas',
        'modulo': 'facturacion',
        'descripcion': 'Permite anular facturas electrónicas ya emitidas ante SIFEN.',
        'ejemplo': 'Un supervisor anula una factura por error en los datos del cliente.',
        'nivel_riesgo': 'critico',
        'orden': 60,
        'categoria': 'cancelacion',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'inutilizar_numero',
        'name': 'Puede inutilizar números de factura',
        'modulo': 'facturacion',
        'descripcion': 'Permite inutilizar números de factura no utilizados en el timbrado.',
        'ejemplo': 'Un administrador inutiliza números salteados por error en la secuencia.',
        'nivel_riesgo': 'critico',
        'orden': 70,
        'categoria': 'inutilizacion',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # DESCARGA DE DOCUMENTOS
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'download_kude_pdf',
        'name': 'Puede descargar facturas en PDF (KuDE)',
        'modulo': 'facturacion',
        'descripcion': 'Permite descargar el documento electrónico KuDE en formato PDF.',
        'ejemplo': 'Un cliente descarga el PDF de su factura electrónica.',
        'nivel_riesgo': 'bajo',
        'orden': 80,
        'categoria': 'descarga_documentos',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'download_kude_xml',
        'name': 'Puede descargar facturas en XML (KuDE)',
        'modulo': 'facturacion',
        'descripcion': 'Permite descargar el documento electrónico KuDE en formato XML.',
        'ejemplo': 'Un contador descarga el XML para importar en su sistema contable.',
        'nivel_riesgo': 'medio',
        'orden': 90,
        'categoria': 'descarga_documentos',
        'requiere_auditoria': False,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # REPORTES Y AUDITORÍA
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'view_reporte_facturacion',
        'name': 'Puede ver reportes de facturación',
        'modulo': 'facturacion',
        'descripcion': 'Permite acceder a reportes consolidados de facturación electrónica.',
        'ejemplo': 'Un gerente revisa el reporte mensual de facturas emitidas.',
        'nivel_riesgo': 'medio',
        'orden': 100,
        'categoria': 'reportes',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'export_reporte_facturacion',
        'name': 'Puede exportar reportes de facturación',
        'modulo': 'facturacion',
        'descripcion': 'Permite exportar reportes de facturación a Excel/PDF.',
        'ejemplo': 'Un contador exporta el libro de ventas mensual para contabilidad.',
        'nivel_riesgo': 'medio',
        'orden': 110,
        'categoria': 'exportacion',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # CONFIGURACIÓN (SOLO ADMINISTRADORES)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'manage_config_facturacion',
        'name': 'Puede administrar configuración de facturación',
        'modulo': 'facturacion',
        'descripcion': 'Permite modificar la configuración del sistema de facturación (ESI, timbrado, etc.).',
        'ejemplo': 'Un administrador actualiza el timbrado al renovarse.',
        'nivel_riesgo': 'critico',
        'orden': 120,
        'categoria': 'configuracion',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'facturacion_electronica',
        'model': 'facturaelectronica',
        'codename': 'sync_sifen',
        'name': 'Puede sincronizar con SIFEN',
        'modulo': 'facturacion',
        'descripcion': 'Permite forzar sincronización de estados con SIFEN.',
        'ejemplo': 'Un técnico sincroniza el estado de facturas pendientes con SIFEN.',
        'nivel_riesgo': 'alto',
        'orden': 130,
        'categoria': 'sincronizacion',
        'requiere_auditoria': True,
    },
]
