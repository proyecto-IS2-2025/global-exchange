from django import template
from django.contrib.auth.models import Permission

register = template.Library()


@register.simple_tag(takes_context=True)
def has_perm(context, permission_codename):
    """
    Verifica si el usuario actual tiene un permiso específico.
    
    Uso en template:
        {% load permissions_tags %}
        {% has_perm 'clientes.view_medios_pago' as puede_ver %}
        {% if puede_ver %}
            <a href="...">Ver medios de pago</a>
        {% endif %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    return request.user.has_perm(permission_codename)


@register.filter
def has_permission(user, permission_codename):
    """
    Filtro para verificar permisos.
    
    Uso en template:
        {% load permissions_tags %}
        {% if user|has_permission:'clientes.view_medios_pago' %}
            <a href="...">Ver medios de pago</a>
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    
    return user.has_perm(permission_codename)


@register.simple_tag(takes_context=True)
def has_any_perm(context, *permissions):
    """
    Verifica si el usuario tiene AL MENOS UNO de los permisos.
    
    Uso en template:
        {% load permissions_tags %}
        {% has_any_perm 'clientes.view_all_clientes' 'clientes.view_assigned_clientes' as puede_ver_clientes %}
        {% if puede_ver_clientes %}
            <a href="...">Ver clientes</a>
        {% endif %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    return any(request.user.has_perm(perm) for perm in permissions)


@register.simple_tag(takes_context=True)
def has_all_perms(context, *permissions):
    """
    Verifica si el usuario tiene TODOS los permisos.
    
    Uso en template:
        {% load permissions_tags %}
        {% has_all_perms 'clientes.view_medios_pago' 'clientes.manage_medios_pago' as puede_gestionar %}
        {% if puede_gestionar %}
            <a href="...">Gestionar medios de pago</a>
        {% endif %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    return all(request.user.has_perm(perm) for perm in permissions)


@register.inclusion_tag('partials/permission_required_msg.html', takes_context=True)
def show_permission_required(context, permission_codename, message=None):
    """
    Muestra mensaje de permiso requerido si el usuario NO tiene acceso.
    
    Uso en template:
        {% load permissions_tags %}
        {% show_permission_required 'clientes.manage_medios_pago' 'gestionar medios de pago' %}
    """
    request = context.get('request')
    tiene_permiso = False
    
    if request and request.user.is_authenticated:
        tiene_permiso = request.user.has_perm(permission_codename)
    
    return {
        'tiene_permiso': tiene_permiso,
        'permission_codename': permission_codename,
        'message': message or 'acceder a esta funcionalidad',
    }