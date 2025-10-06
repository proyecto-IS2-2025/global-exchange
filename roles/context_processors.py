"""
Context processor que inyecta información del usuario y permisos.
"""
from .utils import es_staff, obtener_tipo_usuario


def grupo_usuario(request):
    """
    Context processor que inyecta información dinámica del usuario.
    
    Variables disponibles en templates:
        - usuario_es_staff: bool (admin o operador de staff)
        - usuario_es_cliente: bool (operador de cuenta CON clientes asignados)
        - usuario_es_registrado: bool (usuario registrado SIN clientes asignados)
        - tipo_usuario: str ('admin'|'operador'|'cliente'|'usuario_registrado'|'anonimo')
        - grupos_usuario: list
        - permisos_comunes: dict
    
    ⚠️ ACLARACIÓN DE ROLES:
       - usuario_es_cliente: Usuario CON clientes asignados (puede operar)
       - usuario_es_registrado: Usuario SIN clientes asignados (espera asignación)
       - Cliente (modelo): Entidad de negocio (NO se loggea)
    """
    if not request.user.is_authenticated:
        return {
            'usuario_es_staff': False,
            'usuario_es_cliente': False,
            'usuario_es_registrado': False,
            'tipo_usuario': 'anonimo',
            'grupos_usuario': [],
            'permisos_comunes': {},
            
            # Variables obsoletas (mantener temporalmente)
            'grupo_admin': False,
            'grupo_operador': False,
            'grupo_cliente': False,
        }
    
    # Información del usuario
    usuario_es_staff = es_staff(request.user)
    grupos = list(request.user.groups.values_list('name', flat=True))
    
    # ✅ Identificar tipo de usuario
    usuario_es_cliente = 'cliente' in grupos and not usuario_es_staff
    usuario_es_registrado = 'usuario_registrado' in grupos and not usuario_es_staff
    
    # ✅ Helper de permisos comunes para templates
    permisos_comunes = {
        # Clientes (entidades de negocio)
        'puede_ver_clientes': request.user.has_perm('clientes.view_all_clientes'),
        'puede_gestionar_clientes': request.user.has_perm('clientes.manage_usuarios'),
        
        # Divisas
        'puede_ver_divisas': request.user.has_perm('divisas.view_divisas'),
        'puede_gestionar_divisas': request.user.has_perm('divisas.manage_divisas'),
        'puede_gestionar_tasas': request.user.has_perm('divisas.manage_tasas_cambio'),
        
        # Transacciones
        'puede_ver_transacciones_globales': request.user.has_perm('transacciones.view_transacciones_globales'),
        'puede_gestionar_transacciones': request.user.has_perm('transacciones.manage_estados_transacciones'),
        
        # Usuarios y Roles
        'puede_ver_usuarios': request.user.has_perm('users.view_all_usuarios'),
        'puede_gestionar_usuarios': request.user.has_perm('users.manage_usuarios'),
        'puede_gestionar_roles': request.user.has_perm('auth.change_group'),
        
        # Operaciones (para operadores de cuenta)
        'puede_realizar_operaciones': request.user.has_perm('divisas.realizar_operacion'),
    }
    
    return {
        # ✅ Variables actuales
        'usuario_es_staff': usuario_es_staff,
        'usuario_es_cliente': usuario_es_cliente,  # CON clientes asignados
        'usuario_es_registrado': usuario_es_registrado,  # SIN clientes asignados
        'tipo_usuario': obtener_tipo_usuario(request.user),
        'grupos_usuario': grupos,
        'permisos_comunes': permisos_comunes,
        
        # ⚠️ Variables obsoletas (mantener temporalmente)
        'grupo_admin': 'admin' in grupos,
        'grupo_operador': 'operador' in grupos,
        'grupo_cliente': 'cliente' in grupos,
    }