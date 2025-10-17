"""
Utilidades para gestión de permisos.
"""
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

User = get_user_model()


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
    Verifica si el usuario es staff (admin o operador).
    
    Args:
        user: Instancia de CustomUser
        
    Returns:
        bool: True si es admin o operador, False en caso contrario
    """
    if not user.is_authenticated:
        return False
    
    # Superusuario siempre es staff
    if user.is_superuser:
        return True
    
    # Verificar grupos de staff
    grupos_staff = ['admin', 'operador']
    return user.groups.filter(name__in=grupos_staff).exists()


def obtener_tipo_usuario(user):
    """
    Obtiene el tipo de usuario basado en sus grupos.
    
    Args:
        user: Instancia de CustomUser
        
    Returns:
        str: 'admin', 'operador', 'cliente', 'usuario_registrado' o 'anonimo'
    """
    if not user.is_authenticated:
        return 'anonimo'
    
    # Superusuario es admin
    if user.is_superuser:
        return 'admin'
    
    # Obtener grupos del usuario
    grupos = list(user.groups.values_list('name', flat=True))
    
    # Orden de prioridad
    if 'admin' in grupos:
        return 'admin'
    elif 'operador' in grupos:
        return 'operador'
    elif 'cliente' in grupos:
        return 'cliente'
    elif 'usuario_registrado' in grupos:
        return 'usuario_registrado'
    
    return 'anonimo'


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


def tiene_clientes_asignados(user):
    """
    Verifica si el usuario tiene clientes asignados.
    
    Args:
        user: Instancia de CustomUser
        
    Returns:
        bool: True si tiene clientes asignados, False en caso contrario
    """
    if not user.is_authenticated:
        return False
    
    from clientes.models import AsignacionCliente
    return AsignacionCliente.objects.filter(usuario=user).exists()