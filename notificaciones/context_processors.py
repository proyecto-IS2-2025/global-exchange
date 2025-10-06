from .models import Notificacion

def notificaciones_usuario(request):
    if request.user.is_authenticated:
        # 🔹 Primero obtenemos todas las notificaciones del usuario
        notificaciones_qs = Notificacion.objects.filter(
            usuario=request.user
        ).order_by('-fecha_creacion')

        # 🔹 Luego contamos las pendientes
        cantidad_no_leidas = notificaciones_qs.filter(estado_lectura='pendiente').count()

        # 🔹 Y finalmente recortamos para mostrar solo las últimas 5
        notificaciones = notificaciones_qs[:5]
    else:
        notificaciones = []
        cantidad_no_leidas = 0

    return {
        'notificaciones_header': notificaciones,
        'notificaciones_count': cantidad_no_leidas
    }
