"""
Definiciones de permisos personalizados para la app 'medios_pago'.
"""

PERMISOS_MEDIOS_PAGO = [
    # ═══════════════════════════════════════════════════════════════════
    # CATÁLOGO DE MEDIOS DE PAGO (ADMINISTRACIÓN)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'medios_pago',
        'model': 'mediodepago',
        'codename': 'view_catalogo_medios_pago',
        'name': 'Puede ver el catálogo de medios de pago',
        'modulo': 'medios_pago',
        'descripcion': 'Permite consultar los medios de pago disponibles en el sistema (bancos, billeteras, etc).',
        'ejemplo': 'Un operador consulta qué bancos están habilitados para transferencias.',
        'nivel_riesgo': 'bajo',
        'orden': 10,
        'categoria': 'consulta_catalogo',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'medios_pago',
        'model': 'mediodepago',
        'codename': 'manage_catalogo_medios_pago',
        'name': 'Puede administrar el catálogo de medios de pago',
        'modulo': 'medios_pago',
        'descripcion': 'Permite agregar, modificar o deshabilitar medios de pago en el sistema.',
        'ejemplo': 'Un administrador agrega Banco Atlas con comisión del 2% para transferencias.',
        'nivel_riesgo': 'critico',
        'orden': 20,
        'categoria': 'administracion_catalogo',
        'requiere_auditoria': True,
    },
]