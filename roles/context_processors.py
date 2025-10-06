"""
Context processor que inyecta información del usuario y permisos.
"""


def user_permissions(request):
    """
    Inyecta permisos del usuario en todos los templates.
    
    Variables disponibles:
    - user_perms: Lista de permisos del usuario
    - user_groups: Lista de grupos del usuario
    - is_admin: ¿Es administrador?
    - is_operador: ¿Es operador?
    - is_cliente: ¿Es cliente?
    - can_view_all_clients: ¿Puede ver todos los clientes?
    - can_view_assigned_clients: ¿Puede ver clientes asignados?
    - can_manage_medios_pago: ¿Puede gestionar medios de pago?
    - can_realizar_operacion: ¿Puede realizar operaciones?
    """
    context = {
        'user_perms': [],
        'user_groups': [],
        'is_admin': False,
        'is_operador': False,
        'is_cliente': False,
        
        # Permisos específicos comunes
        'can_view_all_clients': False,
        'can_view_assigned_clients': False,
        'can_manage_medios_pago': False,
        'can_realizar_operacion': False,
        'can_view_transacciones_globales': False,
        'can_view_transacciones_asignadas': False,
        'can_manage_divisas': False,
        'can_manage_tasas_cambio': False,
    }
    
    if not request.user.is_authenticated:
        return context
    
    user = request.user
    
    # Obtener permisos del usuario
    context['user_perms'] = list(user.get_all_permissions())
    
    # Obtener grupos
    context['user_groups'] = list(user.groups.values_list('name', flat=True))
    
    # Identificar rol principal
    context['is_admin'] = user.is_superuser or 'admin' in context['user_groups']
    context['is_operador'] = 'operador' in context['user_groups']
    context['is_cliente'] = 'cliente' in context['user_groups']
    
    # Verificar permisos específicos comunes
    context['can_view_all_clients'] = user.has_perm('clientes.view_all_clientes')
    context['can_view_assigned_clients'] = user.has_perm('clientes.view_assigned_clientes')
    context['can_manage_medios_pago'] = user.has_perm('clientes.manage_medios_pago')
    context['can_realizar_operacion'] = user.has_perm('divisas.realizar_operacion')
    context['can_view_transacciones_globales'] = user.has_perm('transacciones.view_transacciones_globales')
    context['can_view_transacciones_asignadas'] = user.has_perm('transacciones.view_transacciones_asignadas')
    context['can_manage_divisas'] = user.has_perm('divisas.manage_divisas')
    context['can_manage_tasas_cambio'] = user.has_perm('divisas.manage_tasas_cambio')
    
    return context


def grupo_usuario(request):
    """
    ✅ FUNCIÓN PRINCIPAL (compatible con templates existentes)
    
    Inyecta TODAS las variables necesarias para base.html e inicio.html.
    """
    # Obtener contexto base de user_permissions
    context = user_permissions(request)
    
    if not request.user.is_authenticated:
        # ✅ Variables para usuarios NO autenticados
        context.update({
            'grupo_usuario': None,
            'tipo_usuario': None,
            'usuario_es_staff': False,
            'usuario_es_cliente': False,
            'usuario_es_registrado': False,
        })
        return context
    
    user = request.user
    grupos = list(user.groups.values_list('name', flat=True))
    
    # ═══════════════════════════════════════════════════════════════
    # ✅ VARIABLES NECESARIAS PARA BASE.HTML E INICIO.HTML
    # ═══════════════════════════════════════════════════════════════
    
    # 1. grupo_usuario: nombre del primer grupo o None
    context['grupo_usuario'] = grupos[0] if grupos else None
    
    # 2. tipo_usuario: admin/operador/cliente (para mostrar en navbar)
    if user.is_superuser:
        context['tipo_usuario'] = 'Superusuario'
    elif 'admin' in grupos:
        context['tipo_usuario'] = 'Administrador'
    elif 'operador' in grupos:
        context['tipo_usuario'] = 'Operador'
    elif 'cliente' in grupos:
        context['tipo_usuario'] = 'Operador de Cuenta'
    else:
        context['tipo_usuario'] = 'Usuario'
    
    # 3. usuario_es_staff: ¿Es admin u operador? (para mostrar menú staff)
    context['usuario_es_staff'] = (
        user.is_superuser or 
        'admin' in grupos or 
        'operador' in grupos
    )
    
    # 4. usuario_es_cliente: ¿Tiene grupo cliente Y clientes asignados?
    if 'cliente' in grupos:
        # Verificar si tiene clientes asignados
        try:
            from clientes.models import Cliente
            tiene_clientes = Cliente.objects.filter(usuario_asignado=user).exists()
            context['usuario_es_cliente'] = tiene_clientes
        except:
            context['usuario_es_cliente'] = True  # Fallback
    else:
        context['usuario_es_cliente'] = False
    
    # 5. usuario_es_registrado: ¿Usuario sin grupos o sin clientes?
    context['usuario_es_registrado'] = (
        not context['usuario_es_staff'] and 
        not context['usuario_es_cliente']
    )
    
    return context