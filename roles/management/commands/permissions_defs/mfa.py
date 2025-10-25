"""
Definiciones de permisos personalizados para la app 'mfa'.
"""

PERMISOS_MFA = [
    {
        'app_label': 'mfa',
        'model': 'mfaconfig',
        'codename': 'view_mfa_config',
        'name': 'Puede ver la configuración de MFA',
        'modulo': 'mfa',
        'descripcion': 'Permite visualizar la configuración actual de MFA.',
        'ejemplo': 'Un administrador revisa la configuración de MFA para asegurarse de que esté habilitada.',
        'nivel_riesgo': 'bajo',
        'orden': 10,
        'categoria': 'visualizacion',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'mfa',
        'model': 'mfaconfig',
        'codename': 'manage_mfa_config',
        'name': 'Puede gestionar la configuración de MFA',
        'modulo': 'mfa',
        'descripcion': 'Permite activar o desactivar MFA para login y compras.',
        'ejemplo': 'Un administrador habilita MFA para todos los usuarios en la plataforma.',
        'nivel_riesgo': 'alto',
        'orden': 20,
        'categoria': 'gestion',
        'requiere_auditoria': True,
    },
]