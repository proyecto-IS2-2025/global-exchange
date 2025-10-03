# roles/context_processors.py
from .utils import es_staff, obtener_tipo_usuario

def grupo_usuario(request):
    """
    Context processor que inyecta información dinámica del usuario.
    """
    if not request.user.is_authenticated:
        return {
            'usuario_es_staff': False,
            'usuario_es_cliente': False,
            'tipo_usuario': 'anonimo',
            'grupos_usuario': [],
            
            # Mantener por compatibilidad temporal
            'grupo_admin': False,
            'grupo_operador': False,
            'grupo_cliente': False,
        }
    
    usuario_es_staff = es_staff(request.user)
    grupos = list(request.user.groups.values_list('name', flat=True))
    
    return {
        # NUEVAS variables dinámicas
        'usuario_es_staff': usuario_es_staff,
        'usuario_es_cliente': not usuario_es_staff,
        'tipo_usuario': obtener_tipo_usuario(request.user),
        'grupos_usuario': grupos,
        
        # MANTENER temporalmente para no romper templates existentes
        # TODO: Eliminar una vez migrados todos los templates
        'grupo_admin': 'admin' in grupos,
        'grupo_operador': 'operador' in grupos,
        'grupo_cliente': 'cliente' in grupos,
    }


def grupos_context(request):
    """
    Deprecated - Mantener vacío por compatibilidad.
    Usar grupo_usuario() en su lugar.
    """
    return {}