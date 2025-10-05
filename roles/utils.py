"""
Utilidades para gestión de permisos.
"""
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


def get_permissions_by_module(modulo):
    """
    Obtiene todos los permisos de un módulo específico.
    
    Args:
        modulo (str): Nombre del módulo (clientes, divisas, transacciones, etc.)
        
    Returns:
        QuerySet: Permisos del módulo ordenados por codename
        
    Ejemplo:
        >>> permisos_clientes = get_permissions_by_module('clientes')
        >>> for p in permisos_clientes:
        ...     print(f"{p.codename}: {p.name}")
    """
    return Permission.objects.filter(
        content_type__app_label=modulo
    ).select_related('content_type').order_by('codename')


def permission_exists(app_label, codename):
    """
    Verifica si un permiso existe en la base de datos.
    
    Args:
        app_label (str): App label del permiso (clientes, divisas, etc.)
        codename (str): Codename del permiso (view_cliente, manage_divisas, etc.)
        
    Returns:
        bool: True si existe, False si no
        
    Ejemplo:
        >>> if permission_exists('clientes', 'view_all_clientes'):
        ...     print("El permiso existe")
    """
    try:
        Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename
        )
        return True
    except Permission.DoesNotExist:
        return False


def get_user_permission_count(user):
    """
    Retorna la cantidad de permisos que tiene un usuario.
    Incluye permisos directos y heredados de grupos.
    
    Args:
        user: Instancia de Usuario
        
    Returns:
        int: Cantidad de permisos únicos
        
    Ejemplo:
        >>> count = get_user_permission_count(request.user)
        >>> print(f"Tienes {count} permisos")
    """
    if not user.is_authenticated:
        return 0
    
    if user.is_superuser:
        return Permission.objects.count()  # Superuser tiene todos
    
    # Permisos directos + permisos de grupos
    return user.user_permissions.count() + Permission.objects.filter(
        group__user=user
    ).distinct().count()


def es_staff(user):
    """
    Determina si un usuario tiene permisos de staff/empleado.
    Un usuario es staff si tiene al menos un permiso administrativo.
    
    Args:
        user: Instancia de Usuario
        
    Returns:
        bool: True si es staff, False si no
        
    Ejemplo:
        >>> if es_staff(request.user):
        ...     # Mostrar panel administrativo
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    # Lista de permisos que identifican a un usuario como staff
    # Si tiene AL MENOS UNO de estos, es considerado staff
    permisos_staff = [
        'clientes.view_cliente',
        'clientes.view_all_clientes',
        'auth.view_group',
        'divisas.view_divisas',
        'divisas.manage_divisas',
        'transacciones.view_transacciones_globales',
        'medios_pago.view_mediodepago',
        'users.manage_usuarios',
    ]
    
    return any(user.has_perm(perm) for perm in permisos_staff)


def obtener_tipo_usuario(user):
    """
    Retorna un string descriptivo del tipo de usuario.
    Útil para mostrar en la UI (navbar, perfil, etc.).
    
    Args:
        user: Instancia de Usuario
        
    Returns:
        str: Tipo de usuario ('Anónimo', 'Superadmin', 'Admin', 'Cliente', etc.)
        
    Ejemplo:
        >>> tipo = obtener_tipo_usuario(request.user)
        >>> # En template: "Bienvenido {{ tipo }}"
    """
    if not user.is_authenticated:
        return 'Anónimo'
    
    if user.is_superuser:
        return 'Superadmin'
    
    if es_staff(user):
        # Intentar obtener el nombre del primer grupo como "rol"
        primer_grupo = user.groups.first()
        if primer_grupo:
            # Capitalizar el nombre del grupo (admin → Admin, operador → Operador)
            return primer_grupo.name.capitalize()
        return 'Staff'
    
    # Usuario sin permisos administrativos
    return 'Cliente'


def get_modulos_con_permisos(user):
    """
    Retorna lista de módulos a los que el usuario tiene acceso.
    Útil para generar menús dinámicos.
    
    Args:
        user: Instancia de Usuario
        
    Returns:
        list: Lista de strings con nombres de módulos
        
    Ejemplo:
        >>> modulos = get_modulos_con_permisos(request.user)
        >>> # ['clientes', 'divisas', 'transacciones']
    """
    if not user.is_authenticated:
        return []
    
    if user.is_superuser:
        return ['clientes', 'divisas', 'transacciones', 'medios_pago', 'users', 'roles']
    
    # Obtener todos los permisos del usuario (directos + grupos)
    permisos_usuario = Permission.objects.filter(
        user=user
    ) | Permission.objects.filter(
        group__user=user
    )
    
    # Extraer módulos únicos
    modulos = permisos_usuario.values_list(
        'content_type__app_label',
        flat=True
    ).distinct()
    
    return list(modulos)


def tiene_permiso_en_modulo(user, modulo):
    """
    Verifica si el usuario tiene AL MENOS UN permiso en un módulo específico.
    
    Args:
        user: Instancia de Usuario
        modulo (str): Nombre del módulo (clientes, divisas, etc.)
        
    Returns:
        bool: True si tiene permisos, False si no
        
    Ejemplo:
        >>> if tiene_permiso_en_modulo(request.user, 'clientes'):
        ...     # Mostrar link a módulo clientes en el menú
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    # Verificar si tiene algún permiso del módulo
    permisos_modulo = Permission.objects.filter(
        content_type__app_label=modulo
    )
    
    for perm in permisos_modulo:
        if user.has_perm(f"{modulo}.{perm.codename}"):
            return True
    
    return False