from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Notificacion, NotificacionTasa, ConfiguracionGeneral
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task
def procesar_notificaciones_periodicas():
    """
    Task que procesa todas las notificaciones periódicas activas.
    Se ejecuta cada 5 minutos según la configuración de Celery Beat.
    """
    ahora = timezone.now()
    
    # Obtener todas las notificaciones periódicas activas
    notificaciones = NotificacionTasa.objects.filter(
        tipo_alerta='periodica',
        activa=True
    )
    
    print(f"[{ahora}] Procesando {notificaciones.count()} notificaciones periódicas")
    
    for notif in notificaciones:
        if debe_enviar_notificacion(notif, ahora):
            try:
                enviar_reporte_periodico(notif)
                notif.ultima_ejecucion = ahora
                notif.save()
                print(f"  ✓ Notificación enviada: {notif.divisa} - {notif.periodicidad}")
            except Exception as e:
                print(f"  ✗ Error al enviar notificación {notif.id}: {str(e)}")
                import traceback
                traceback.print_exc()
    
    return f"Procesadas {notificaciones.count()} notificaciones"


def debe_enviar_notificacion(notif, ahora):
    """
    Determina si una notificación periódica debe ser enviada en este momento.
    """
    # Si nunca se ha ejecutado, verificar si es hora de enviarla
    if not notif.ultima_ejecucion:
        return es_hora_de_enviar(notif, ahora)
    
    # Verificar según la periodicidad
    if notif.periodicidad == 'diaria':
        # Enviar si ya pasó un día y es la hora configurada
        diff_dias = (ahora.date() - notif.ultima_ejecucion.date()).days
        return diff_dias >= 1 and es_hora_de_enviar(notif, ahora)
    
    elif notif.periodicidad == 'semanal':
        # Enviar si es el día de la semana configurado y es la hora
        diff_dias = (ahora.date() - notif.ultima_ejecucion.date()).days
        return (diff_dias >= 7 and 
                ahora.weekday() == int(notif.dia_semana) and 
                es_hora_de_enviar(notif, ahora))
    
    elif notif.periodicidad == 'mensual':
        # Enviar si es el día del mes configurado y es la hora
        diff_dias = (ahora.date() - notif.ultima_ejecucion.date()).days
        return (diff_dias >= 28 and  # Al menos un mes
                ahora.day == notif.dia_mes and 
                es_hora_de_enviar(notif, ahora))
    
    return False


def es_hora_de_enviar(notif, ahora):
    """
    Verifica si es el momento del día configurado para enviar la notificación.
    Permite una ventana de ±3 minutos para evitar perder notificaciones.
    """
    if not notif.hora_envio:
        return False
    
    # Convertir la hora actual a la zona horaria local configurada
    ahora_local = ahora.astimezone()
    
    # Crear la hora configurada en la zona horaria local
    hora_configurada = timezone.datetime.combine(ahora_local.date(), notif.hora_envio)
    hora_configurada = timezone.make_aware(hora_configurada, timezone=ahora_local.tzinfo)
    
    # Ventana de ±3 minutos (considerando que el task se ejecuta cada 5 minutos)
    ventana_inicio = hora_configurada - timedelta(minutes=3)
    ventana_fin = hora_configurada + timedelta(minutes=3)
    
    return ventana_inicio <= ahora_local <= ventana_fin


def enviar_reporte_periodico(notif):
    """
    Crea una notificación con el reporte periódico de la divisa.
    """
    from divisas.models import CotizacionSegmento, Divisa
    
    # Obtener la divisa
    try:
        divisa_obj = Divisa.objects.get(code=notif.divisa)
    except Divisa.DoesNotExist:
        Notificacion.objects.create(
            usuario=notif.usuario,
            alerta_base=notif,
            mensaje=f"❌ Error en Reporte {notif.get_periodicidad_display()}: No se encontró la divisa {notif.divisa}."
        )
        return
    
    # Obtener el segmento del cliente asociado
    segmento = notif.cliente_asociado.segmento
    
    # Obtener la cotización actual para este segmento
    try:
        cotizacion_actual = CotizacionSegmento.objects.filter(
            divisa=divisa_obj,
            segmento=segmento
        ).latest('fecha')
        
        # Crear el mensaje del reporte
        mensaje = f"""
📊 Reporte {notif.get_periodicidad_display()} - {divisa_obj.nombre} ({divisa_obj.code})

💰 Tasas actuales (Segmento: {segmento.name}):
   • Compra: {cotizacion_actual.valor_compra_unit:,.2f} Gs.
   • Venta: {cotizacion_actual.valor_venta_unit:,.2f} Gs.

📈 Detalles:
   • Precio base: {cotizacion_actual.precio_base:,.2f} Gs.
   • Descuento del segmento: {cotizacion_actual.porcentaje_descuento}%

🕐 Actualizado: {cotizacion_actual.fecha.strftime('%d/%m/%Y %H:%M')}
        """.strip()
        
        # Crear la notificación
        Notificacion.objects.create(
            usuario=notif.usuario,
            alerta_base=notif,
            mensaje=mensaje
        )
        
    except CotizacionSegmento.DoesNotExist:
        # Si no hay cotización disponible, notificar al usuario
        Notificacion.objects.create(
            usuario=notif.usuario,
            alerta_base=notif,
            mensaje=f"⚠️ Reporte {notif.get_periodicidad_display()}: No hay cotización disponible para {divisa_obj.nombre} en el segmento {segmento.name}."
        )


def enviar_notificacion_websocket(usuario_id, mensaje):
    """
    Envía una notificación en tiempo real mediante WebSocket.
    """
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notificaciones_{usuario_id}',
            {
                'type': 'notificacion_nueva',
                'mensaje': mensaje
            }
        )
    except Exception as e:
        print(f"Error al enviar notificación WebSocket: {str(e)}")


# ========================================
# TAREAS ESPECÍFICAS POR PERIODICIDAD
# ========================================

@shared_task
def enviar_notificaciones_diarias():
    """
    Procesa y envía notificaciones configuradas como DIARIAS.
    Se ejecuta cada minuto y verifica si es la hora de enviar.
    """
    ahora = timezone.now()
    
    # Filtrar solo notificaciones diarias activas
    notificaciones = NotificacionTasa.objects.filter(
        tipo_alerta='periodica',
        periodicidad='diaria',
        activa=True
    )
    
    enviadas = 0
    for notif in notificaciones:
        if debe_enviar_notificacion(notif, ahora):
            try:
                enviar_reporte_periodico(notif)
                notif.ultima_ejecucion = ahora
                notif.save()
                
                # Enviar notificación en tiempo real
                enviar_notificacion_websocket(
                    notif.usuario.id,
                    f"Nuevo reporte diario de {notif.divisa} disponible"
                )
                enviadas += 1
                print(f"✓ Notificación diaria enviada: {notif.divisa} para {notif.usuario.username}")
            except Exception as e:
                print(f"✗ Error al enviar notificación diaria {notif.id}: {str(e)}")
    
    return f"Enviadas {enviadas} notificaciones diarias"


@shared_task
def enviar_notificaciones_semanales():
    """
    Procesa y envía notificaciones configuradas como SEMANALES.
    Se ejecuta cada minuto y verifica si es el día y hora correctos.
    """
    ahora = timezone.now()
    
    # Filtrar solo notificaciones semanales activas
    notificaciones = NotificacionTasa.objects.filter(
        tipo_alerta='periodica',
        periodicidad='semanal',
        activa=True
    )
    
    enviadas = 0
    for notif in notificaciones:
        if debe_enviar_notificacion(notif, ahora):
            try:
                enviar_reporte_periodico(notif)
                notif.ultima_ejecucion = ahora
                notif.save()
                
                # Enviar notificación en tiempo real
                enviar_notificacion_websocket(
                    notif.usuario.id,
                    f"Nuevo reporte semanal de {notif.divisa} disponible"
                )
                enviadas += 1
                print(f"✓ Notificación semanal enviada: {notif.divisa} para {notif.usuario.username}")
            except Exception as e:
                print(f"✗ Error al enviar notificación semanal {notif.id}: {str(e)}")
    
    return f"Enviadas {enviadas} notificaciones semanales"


@shared_task
def enviar_notificaciones_mensuales():
    """
    Procesa y envía notificaciones configuradas como MENSUALES.
    Se ejecuta cada minuto y verifica si es el día del mes y hora correctos.
    """
    ahora = timezone.now()
    
    # Filtrar solo notificaciones mensuales activas
    notificaciones = NotificacionTasa.objects.filter(
        tipo_alerta='periodica',
        periodicidad='mensual',
        activa=True
    )
    
    enviadas = 0
    for notif in notificaciones:
        if debe_enviar_notificacion(notif, ahora):
            try:
                enviar_reporte_periodico(notif)
                notif.ultima_ejecucion = ahora
                notif.save()
                
                # Enviar notificación en tiempo real
                enviar_notificacion_websocket(
                    notif.usuario.id,
                    f"Nuevo reporte mensual de {notif.divisa} disponible"
                )
                enviadas += 1
                print(f"✓ Notificación mensual enviada: {notif.divisa} para {notif.usuario.username}")
            except Exception as e:
                print(f"✗ Error al enviar notificación mensual {notif.id}: {str(e)}")
    
    return f"Enviadas {enviadas} notificaciones mensuales"
