"""
Definiciones de permisos personalizados para la app 'users' (gestión de usuarios).
"""

PERMISOS_USUARIOS = [
    # ═══════════════════════════════════════════════════════════════════
    # GESTIÓN DE USUARIOS
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'users',
        'model': 'customuser',
        'codename': 'manage_usuarios',
        'name': 'Puede gestionar usuarios del sistema',
        'modulo': 'usuarios',
        'descripcion': 'Permite crear, editar y eliminar cuentas de usuarios del sistema.',
        'ejemplo': 'Un administrador crea una cuenta para un nuevo operador.',
        'nivel_riesgo': 'critico',
        'orden': 10,
        'categoria': 'gestion_usuarios',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'users',
        'model': 'customuser',
        'codename': 'view_all_usuarios',
        'name': 'Puede ver todos los usuarios',
        'modulo': 'usuarios',
        'descripcion': 'Permite listar y consultar información de todos los usuarios.',
        'ejemplo': 'Un administrador revisa el listado de operadores activos.',
        'nivel_riesgo': 'medio',
        'orden': 20,
        'categoria': 'visualizacion_usuarios',
        'requiere_auditoria': False,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # ROLES Y PERMISOS
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'users',
        'model': 'customuser',
        'codename': 'manage_usuario_roles',
        'name': 'Puede asignar roles a usuarios',
        'modulo': 'usuarios',
        'descripcion': 'Permite agregar o quitar roles (grupos) a usuarios del sistema.',
        'ejemplo': 'Un administrador asigna el rol "Operador" a un usuario nuevo.',
        'nivel_riesgo': 'critico',
        'orden': 30,
        'categoria': 'gestion_roles',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # ACTIVACIÓN Y SEGURIDAD
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'users',
        'model': 'customuser',
        'codename': 'activate_deactivate_usuarios',
        'name': 'Puede activar/desactivar usuarios',
        'modulo': 'usuarios',
        'descripcion': 'Permite habilitar o deshabilitar cuentas de usuario (sin eliminarlas).',
        'ejemplo': 'Un administrador desactiva temporalmente un operador que está de vacaciones.',
        'nivel_riesgo': 'alto',
        'orden': 40,
        'categoria': 'gestion_estado',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'users',
        'model': 'customuser',
        'codename': 'reset_usuario_password',
        'name': 'Puede resetear contraseñas de usuarios',
        'modulo': 'usuarios',
        'descripcion': 'Permite forzar el cambio de contraseña de otro usuario.',
        'ejemplo': 'Un administrador resetea la contraseña de un operador que la olvidó.',
        'nivel_riesgo': 'alto',
        'orden': 50,
        'categoria': 'seguridad',
        'requiere_auditoria': True,
    },
]