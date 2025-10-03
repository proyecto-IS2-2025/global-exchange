"""
Utilidades para determinar roles y permisos de usuarios de forma dinámica.
"""

def es_staff(user):
    """
    Determina si un usuario tiene permisos de staff/empleado.
    NO verifica nombres de grupos, solo permisos.
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    # Lista de permisos que identifican a un usuario como staff
    # Cualquier usuario con AL MENOS UNO de estos permisos es staff
    permisos_staff = [
        'clientes.view_cliente',
        'auth.view_group',
        'divisas.view_divisa',
        'transacciones.view_transaccion',
        'medios_pago.view_mediodepago',
    ]
    
    return any(user.has_perm(perm) for perm in permisos_staff)


def obtener_tipo_usuario(user):
    """
    Retorna un string que identifica el tipo de usuario.
    Útil para mostrar en UI.
    """
    if not user.is_authenticated:
        return 'anonimo'
    
    if user.is_superuser:
        return 'superadmin'
    
    if es_staff(user):
        # Obtener el primer grupo como "rol"
        primer_grupo = user.groups.first()
        if primer_grupo:
            return primer_grupo.name.title()
        return 'Staff'
    
    return 'Cliente'