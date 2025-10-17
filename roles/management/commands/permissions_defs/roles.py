"""
Definiciones de permisos personalizados para la app 'roles'.

ARQUITECTURA DE PERMISOS:
- Nivel 1 (Bajo riesgo): Solo visualización
- Nivel 2 (Medio riesgo): Gestión de usuarios en grupos
- Nivel 3 (Alto riesgo): Gestión de permisos
- Nivel 4 (Crítico): Administración completa de roles
"""

PERMISOS_ROLES = [
    # ═══════════════════════════════════════════════════════════════════
    # NIVEL 1: VISUALIZACIÓN (BAJO RIESGO)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'roles',
        'model': 'rolestatus',
        'codename': 'view_roles_list',
        'name': 'Puede ver el listado de roles',
        'modulo': 'roles',
        'descripcion': 'Permite visualizar el listado de grupos/roles del sistema sin poder modificarlos.',
        'ejemplo': 'Un auditor consulta qué roles existen en el sistema (Admin, Operador, Cliente).',
        'nivel_riesgo': 'bajo',
        'orden': 10,
        'categoria': 'visualizacion',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'roles',
        'model': 'rolestatus',
        'codename': 'view_role_details',
        'name': 'Puede ver detalles de un rol específico',
        'modulo': 'roles',
        'descripcion': 'Permite acceder a la información detallada de un rol (usuarios, permisos asignados).',
        'ejemplo': 'Un supervisor revisa qué permisos tiene asignado el rol "Operador".',
        'nivel_riesgo': 'bajo',
        'orden': 20,
        'categoria': 'visualizacion',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'roles',
        'model': 'rolestatus',
        'codename': 'view_permission_matrix',
        'name': 'Puede ver la matriz de permisos',
        'modulo': 'roles',
        'descripcion': 'Permite acceder a la vista comparativa de permisos entre todos los roles.',
        'ejemplo': 'Un gerente de RRHH consulta la matriz para entender diferencias entre roles.',
        'nivel_riesgo': 'medio',
        'orden': 30,
        'categoria': 'visualizacion_avanzada',
        'requiere_auditoria': False,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # NIVEL 2: GESTIÓN DE USUARIOS EN GRUPOS (MEDIO RIESGO)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'roles',
        'model': 'rolestatus',
        'codename': 'view_group_users',
        'name': 'Puede ver usuarios asignados a roles',
        'modulo': 'roles',
        'descripcion': 'Permite consultar qué usuarios pertenecen a cada grupo sin poder modificar asignaciones.',
        'ejemplo': 'Un supervisor verifica qué operadores están en el grupo "Operador de Cuenta".',
        'nivel_riesgo': 'bajo',
        'orden': 40,
        'categoria': 'consulta_usuarios',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'roles',
        'model': 'rolestatus',
        'codename': 'manage_group_users',
        'name': 'Puede asignar/remover usuarios de roles',
        'modulo': 'roles',
        'descripcion': 'Permite agregar o quitar usuarios de grupos existentes (onboarding/offboarding).',
        'ejemplo': 'Un gerente de RRHH asigna 3 nuevos empleados al grupo "Operador".',
        'nivel_riesgo': 'alto',
        'orden': 50,
        'categoria': 'gestion_usuarios',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # NIVEL 3: GESTIÓN DE PERMISOS (ALTO RIESGO)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'roles',
        'model': 'rolestatus',
        'codename': 'view_group_permissions',
        'name': 'Puede ver permisos de roles',
        'modulo': 'roles',
        'descripcion': 'Permite consultar qué permisos tiene asignado cada rol sin poder modificarlos.',
        'ejemplo': 'Un auditor revisa qué permisos tiene el rol "Administrador".',
        'nivel_riesgo': 'medio',
        'orden': 60,
        'categoria': 'consulta_permisos',
        'requiere_auditoria': False,
    },
    {
        'app_label': 'roles',
        'model': 'rolestatus',
        'codename': 'manage_group_permissions',
        'name': 'Puede modificar permisos de roles existentes',
        'modulo': 'roles',
        'descripcion': 'Permite agregar o quitar permisos de grupos ya creados (sin poder crear/eliminar roles).',
        'ejemplo': 'Un administrador agrega el permiso "view_reportes" al grupo "Operador".',
        'nivel_riesgo': 'critico',
        'orden': 70,
        'categoria': 'gestion_permisos',
        'requiere_auditoria': True,
    },
    
    # ═══════════════════════════════════════════════════════════════════
    # NIVEL 4: ADMINISTRACIÓN COMPLETA (CRÍTICO)
    # ═══════════════════════════════════════════════════════════════════
    {
        'app_label': 'roles',
        'model': 'rolestatus',
        'codename': 'manage_roles',
        'name': 'Puede administrar roles completamente (CRUD)',
        'modulo': 'roles',
        'descripcion': 'Permite crear, editar, eliminar roles y gestionar todos sus aspectos (permisos + usuarios).',
        'ejemplo': 'Un super administrador crea un nuevo rol "Auditor" con permisos específicos.',
        'nivel_riesgo': 'critico',
        'orden': 80,
        'categoria': 'administracion_completa',
        'requiere_auditoria': True,
    },
    {
        'app_label': 'roles',
        'model': 'rolestatus',
        'codename': 'manage_role_status',
        'name': 'Puede activar/desactivar roles',
        'modulo': 'roles',
        'descripcion': 'Permite habilitar o deshabilitar roles temporalmente sin eliminarlos.',
        'ejemplo': 'Un administrador desactiva el rol "Operador Temporal" al finalizar la temporada alta.',
        'nivel_riesgo': 'alto',
        'orden': 90,
        'categoria': 'gestion_estado',
        'requiere_auditoria': True,
    },
]