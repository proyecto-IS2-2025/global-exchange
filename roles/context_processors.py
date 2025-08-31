def grupo_usuario(request):
    if request.user.is_authenticated:
        grupos = request.user.groups.all()
        return {'grupo_usuario': grupos[0].name if grupos else None}
    return {'grupo_usuario': None}
