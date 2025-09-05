def grupo_usuario(request):
    """
    Procesador de contexto que expone el nombre del primer grupo del usuario autenticado
    en el contexto de la plantilla.

    Esto permite acceder al nombre del grupo directamente en las plantillas HTML
    como ``{{ grupo_usuario }}``.

    :param request: Objeto de solicitud HTTP.
    :type request: :class:`~django.http.HttpRequest`
    :return: Un diccionario de contexto que contiene el nombre del grupo del usuario.
    :rtype: dict
    """
    if request.user.is_authenticated:
        grupos = request.user.groups.all()
        return {'grupo_usuario': grupos[0].name if grupos else None}
    return {'grupo_usuario': None}
