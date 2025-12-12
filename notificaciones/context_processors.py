from .models import Notificacion

def notificaciones_usuario(request):
    if hasattr(request, 'user') and request.user.is_authenticated:
        # 🔹 Obtenemos solo las notificaciones pendientes del usuario
        notificaciones_pendientes = Notificacion.objects.filter(
            usuario=request.user,
            estado_lectura='pendiente'
        ).order_by('-fecha_creacion')

        # 🔹 Contamos las pendientes
        cantidad_no_leidas = notificaciones_pendientes.count()

        # 🔹 Mostramos solo las últimas 5 pendientes
        notificaciones = notificaciones_pendientes
    else:
        notificaciones = []
        cantidad_no_leidas = 0

    return {
        'notificaciones_header': notificaciones,
        'notificaciones_count': cantidad_no_leidas
    }
