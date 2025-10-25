"""
Context processor que inyecta información del usuario y permisos de forma dinámica.
Maneja múltiples roles de staff y determina automáticamente el tipo de menú a mostrar.
"""

from clientes.models import AsignacionCliente, Cliente


def grupo_usuario(request):
    """
    ✅ Context processor principal que determina el tipo de usuario y sus permisos.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # USUARIOS NO AUTENTICADOS
    # ═══════════════════════════════════════════════════════════════
    if not request.user.is_authenticated:
        return {
            'tipo_usuario': None,
            'usuario_es_staff': False,
            'usuario_es_cliente': False,
            'usuario_es_registrado': False,
            'grupo_admin': False,
            'grupo_operador': False,
            'grupos_usuario': [],
            'permisos_clave': {},
            'cliente_activo': None,
        }
    
    user = request.user
    
    # ═══════════════════════════════════════════════════════════════
    # OBTENER GRUPOS DEL USUARIO
    # ═══════════════════════════════════════════════════════════════
    grupos = list(user.groups.values_list('name', flat=True))
    
    # ═══════════════════════════════════════════════════════════════
    # DEFINIR ROLES DE STAFF (DINÁMICO)
    # ═══════════════════════════════════════════════════════════════
    ROLES_STAFF = {
        'dev': {
            'prioridad': 1,
            'display_name': 'Developer',
            'es_admin': True,
        },
        'administrador': {
            'prioridad': 2,
            'display_name': 'Administrador',
            'es_admin': True,
        },
        'operador': {
            'prioridad': 3,
            'display_name': 'Operador',
            'es_admin': False,
        },
        'observador': {
            'prioridad': 4,
            'display_name': 'Observador',
            'es_admin': False,
        },
    }
    
    # ═══════════════════════════════════════════════════════════════
    # DETERMINAR ROL PRINCIPAL (POR PRIORIDAD)
    # ═══════════════════════════════════════════════════════════════
    rol_actual = None
    es_staff = False
    es_admin = False
    es_operador = False
    
    # Superusuario tiene máxima prioridad
    if user.is_superuser:
        rol_actual = {
            'nombre': 'superusuario',
            'display_name': 'Superusuario',
            'es_admin': True,
        }
        es_staff = True
        es_admin = True
    else:
        # Buscar el rol de staff con mayor prioridad
        for grupo in grupos:
            if grupo in ROLES_STAFF:
                if rol_actual is None or ROLES_STAFF[grupo]['prioridad'] < rol_actual.get('prioridad', 999):
                    rol_actual = {
                        'nombre': grupo,
                        'display_name': ROLES_STAFF[grupo]['display_name'],
                        'es_admin': ROLES_STAFF[grupo]['es_admin'],
                        'prioridad': ROLES_STAFF[grupo]['prioridad'],
                    }
                    es_staff = True
                    es_admin = ROLES_STAFF[grupo]['es_admin']
                    es_operador = (grupo == 'operador')
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICAR ASIGNACIÓN DE CLIENTES Y CLIENTE ACTIVO
    # ═══════════════════════════════════════════════════════════════
    tiene_clientes = False
    cliente_activo = None
    
    if not es_staff:  # Solo verificar si NO es staff
        tiene_clientes = AsignacionCliente.objects.filter(
            usuario=user
        ).exists()
        
        # Obtener cliente_id de la sesión
        cliente_id = request.session.get('cliente_id')
        
        if cliente_id:
            try:
                cliente_activo = Cliente.objects.select_related('segmento').get(
                    id=cliente_id,
                    esta_activo=True
                )
            except Cliente.DoesNotExist:
                # Si el cliente no existe o no está activo, limpiar sesión
                request.session.pop('cliente_id', None)
                cliente_activo = None
        else:
            # Último intento: Auto-asignar primer cliente disponible
            if tiene_clientes:
                asignacion = AsignacionCliente.objects.filter(
                    usuario=user,
                    cliente__esta_activo=True
                ).first()
                
                if asignacion:
                    cliente_activo = asignacion.cliente
                    request.session['cliente_id'] = cliente_activo.id
    
    # ═══════════════════════════════════════════════════════════════
    # DETERMINAR TIPO DE USUARIO FINAL
    # ═══════════════════════════════════════════════════════════════
    if es_staff:
        tipo_usuario = rol_actual['display_name']
        es_cliente = False
        es_registrado = False
    elif tiene_clientes:
        tipo_usuario = 'Operador de Cuenta'
        es_cliente = True
        es_registrado = False
    else:
        tipo_usuario = 'Usuario Registrado'
        es_cliente = False
        es_registrado = True
    
    # ═══════════════════════════════════════════════════════════════
    # PERMISOS CLAVE (PARA VERIFICACIÓN RÁPIDA EN TEMPLATES)
    # ═══════════════════════════════════════════════════════════════
    permisos_clave = {
        # Clientes
        'puede_ver_todos_clientes': user.has_perm('clientes.view_all_clientes'),
        'puede_ver_clientes_asignados': user.has_perm('clientes.view_assigned_clientes'),
        'puede_asignar_clientes': user.has_perm('clientes.manage_cliente_assignment'),
        'puede_gestionar_clientes': user.has_perm('clientes.manage_all_clientes'),
        
        # Divisas
        'puede_ver_divisas': user.has_perm('divisas.view_divisas'),
        'puede_gestionar_divisas': user.has_perm('divisas.manage_divisas'),
        'puede_gestionar_cotizaciones': user.has_perm('divisas.manage_cotizaciones_segmento'),
        
        # Medios de Pago
        'puede_ver_medios_pago': user.has_perm('medios_pago.view_catalogo_medios_pago'),
        'puede_gestionar_medios_pago': user.has_perm('medios_pago.manage_catalogo_medios_pago'),
        
        # Transacciones
        'puede_ver_transacciones_globales': user.has_perm('transacciones.view_transacciones_globales'),
        'puede_ver_transacciones_asignadas': user.has_perm('transacciones.view_transacciones_asignadas'),
        'puede_crear_transaccion': user.has_perm('transacciones.create_transaccion'),
        
        # Descuentos
        'puede_ver_descuentos': user.has_perm('clientes.view_descuentos_segmento'),
        'puede_gestionar_descuentos': user.has_perm('clientes.manage_descuentos_segmento'),
        
        # Límites
        'puede_ver_limites': user.has_perm('clientes.view_limites_operacion'),
        'puede_gestionar_limites': user.has_perm('clientes.manage_limites_operacion'),
        
        # MFA
        'puede_ver_config_mfa': user.has_perm('mfa.view_mfa_config'),
        'puede_gestionar_config_mfa': user.has_perm('mfa.manage_mfa_config'),
        
        # Usuarios
        'puede_gestionar_usuarios': user.has_perm('users.manage_usuarios'),
        'puede_ver_usuarios': user.has_perm('users.view_all_usuarios'),
    }
    
    # ═══════════════════════════════════════════════════════════════
    # RETORNAR CONTEXTO COMPLETO
    # ═══════════════════════════════════════════════════════════════
    return {
        # Variables principales
        'tipo_usuario': tipo_usuario,
        'usuario_es_staff': es_staff,
        'usuario_es_cliente': es_cliente,
        'usuario_es_registrado': es_registrado,
        
        # Variables legacy (para compatibilidad con templates antiguos)
        'grupo_admin': es_admin,
        'grupo_operador': es_operador,
        'grupo_usuario': grupos[0] if grupos else None,
        
        # Información adicional
        'grupos_usuario': grupos,
        'rol_actual': rol_actual,
        'permisos_clave': permisos_clave,
        
        # Flags útiles
        'es_superusuario': user.is_superuser,
        'tiene_clientes_asignados': tiene_clientes,
        'cliente_activo': cliente_activo,
    }


def user_permissions(request):
    """
    ✅ Context processor alternativo con estructura diferente.
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
    context['is_admin'] = user.is_superuser or 'administrador' in context['user_groups']
    context['is_operador'] = 'operador' in context['user_groups']
    context['is_cliente'] = 'cliente' in context['user_groups']
    
    # Verificar permisos específicos comunes
    context['can_view_all_clients'] = user.has_perm('clientes.view_all_clientes')
    context['can_view_assigned_clients'] = user.has_perm('clientes.view_assigned_clientes')
    context['can_manage_medios_pago'] = user.has_perm('medios_pago.manage_catalogo_medios_pago')
    context['can_realizar_operacion'] = user.has_perm('divisas.realizar_operacion')
    context['can_view_transacciones_globales'] = user.has_perm('transacciones.view_transacciones_globales')
    context['can_view_transacciones_asignadas'] = user.has_perm('transacciones.view_transacciones_asignadas')
    context['can_manage_divisas'] = user.has_perm('divisas.manage_divisas')
    context['can_manage_tasas_cambio'] = user.has_perm('divisas.manage_cotizaciones_segmento')
    
    return context