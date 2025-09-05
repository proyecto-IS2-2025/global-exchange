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
    if request.user.is_authenticated:
        grupos = request.user.groups.all()
        return {'grupo_usuario': grupos[0].name if grupos else None}
    return {'grupo_usuario': None}
"""