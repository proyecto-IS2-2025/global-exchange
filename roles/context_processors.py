# users/context_processors.py
def grupo_usuario(request):
    grupo = None
    grupo_admin = grupo_operador = grupo_cliente = False

    if request.user.is_authenticated:
        grupos = list(request.user.groups.values_list('name', flat=True))
        if 'admin' in grupos:
            grupo = 'admin'
            grupo_admin = True
        elif 'operador' in grupos:
            grupo = 'operador'
            grupo_operador = True
        elif 'cliente' in grupos:
            grupo = 'cliente'
            grupo_cliente = True

    return {
        'grupo_usuario': grupo,
        'grupo_admin': grupo_admin,
        'grupo_operador': grupo_operador,
        'grupo_cliente': grupo_cliente,
    }

"""
def grupo_usuario(request):

    Procesador de contexto que expone el nombre del primer grupo del usuario autenticado
    en el contexto de la plantilla.

    Esto permite acceder al nombre del grupo directamente en las plantillas HTML
    como ``{{ grupo_usuario }}``.

    :param request: Objeto de solicitud HTTP.
    :type request: :class:`~django.http.HttpRequest`
    :return: Un diccionario de contexto que contiene el nombre del grupo del usuario.
    :rtype: dict

    if request.user.is_authenticated:
        grupos = request.user.groups.all()
        return {'grupo_usuario': grupos[0].name if grupos else None}
    return {'grupo_usuario': None}
# users/context_processors.py
"""

def grupos_context(request):
    grupo_admin = grupo_operador = grupo_cliente = False
    if request.user.is_authenticated:
        grupos = list(request.user.groups.values_list('name', flat=True))
        grupo_admin = 'admin' in grupos
        grupo_operador = 'operador' in grupos
        grupo_cliente = 'cliente' in grupos
    return {
        'grupo_admin': grupo_admin,
        'grupo_operador': grupo_operador,
        'grupo_cliente': grupo_cliente,
    }
