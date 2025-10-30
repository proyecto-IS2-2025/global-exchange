from .models import NotificacionTasa, Notificacion
from divisas.models import CotizacionSegmento
from django.core.mail import send_mail
from .models import ConfiguracionGeneral
import logging

logger = logging.getLogger(__name__)


def evaluar_alertas(nueva_cotizacion: CotizacionSegmento):
    """
    Evalúa las alertas configuradas por los usuarios según la nueva cotización.
    Crea notificaciones con formato uniforme y mensajes claros.
    """
    
    logger.info(f"🔔 Evaluando alertas para: {nueva_cotizacion.divisa.code} - Segmento: {nueva_cotizacion.segmento}")

    reglas_activas = NotificacionTasa.objects.filter(
        divisa=nueva_cotizacion.divisa.code,
        activa=True,
        cliente_asociado__segmento=nueva_cotizacion.segmento
    )
    
    logger.info(f"📊 Reglas activas encontradas: {reglas_activas.count()}")
    for regla in reglas_activas:
        logger.info(f"  - Regla ID {regla.id}: {regla.usuario.username} - {regla.tipo_alerta} - {regla.cliente_asociado.nombre_completo}")

    for regla in reglas_activas:
        config = ConfiguracionGeneral.objects.filter(usuario=regla.usuario).first()
        canal = config.canal_notificacion if config else "sistema"
        condicion_cumplida = False
        mensaje = ""

        # 🔹 Valores actuales formateados en guaraníes
        valor_compra = f"{int(round(nueva_cotizacion.valor_compra_unit)):,}".replace(",", ".")
        valor_venta = f"{int(round(nueva_cotizacion.valor_venta_unit)):,}".replace(",", ".")
        cliente_nombre = regla.cliente_asociado.nombre_completo or "cliente no especificado"

        # 🔹 Tipo de alerta: General (siempre se crea)
        if regla.tipo_alerta == 'general':
            condicion_cumplida = True
            mensaje = (
                f"Se ha registrado una nueva tasa para {regla.divisa}: "
                f"Compra: Gs. {valor_compra} – Venta: Gs. {valor_venta} "
                f"para el cliente {cliente_nombre}."
            )

        elif regla.tipo_alerta == 'umbral':
            # Determinar valor actual según tipo de operación
            if regla.tipo_operacion == 'compra':
                valor_actual = nueva_cotizacion.valor_compra_unit
                tipo_texto = "compra"
            elif regla.tipo_operacion == 'venta':
                valor_actual = nueva_cotizacion.valor_venta_unit
                tipo_texto = "venta"
            else:
                continue

            if (
                (regla.condicion_umbral == 'mayor' and valor_actual >= regla.monto_umbral)
                or (regla.condicion_umbral == 'menor' and valor_actual <= regla.monto_umbral)
            ):
                condicion_cumplida = True
                valor_actual_fmt = f"{int(round(valor_actual)):,}".replace(",", ".")
                mensaje = (
                    f"El valor de {tipo_texto} del {regla.divisa} alcanzó Gs. {valor_actual_fmt} "
                    f"para el cliente {cliente_nombre} "
                )

        # 🔹 Crear la notificación si corresponde
        if condicion_cumplida:
            # Enviar correo si el canal está configurado para ello
            if canal in ["sistema_correo"]:
                try:
                    asunto = "📢 Nueva notificación de tasa de cambio"
                    url_notificaciones = "http://127.0.0.1:8000/notificaciones/"

                    cuerpo = f"""
                    <html>
                      <body style="font-family: Arial, sans-serif; color: #333;">
                        <p>Hola <strong>{regla.usuario.first_name or regla.usuario.username}</strong>,</p>
                        <p>{mensaje}</p>
                        <p>
                          <a href="{url_notificaciones}" 
                             style="background-color:#0d6efd; color:white; padding:10px 18px; 
                                    text-decoration:none; border-radius:6px; display:inline-block;">
                             Ver notificación
                          </a>
                        </p>
                        <p style="font-size:12px; color:#777;">Global Exchange ©</p>
                      </body>
                    </html>
                    """

                    send_mail(
                        asunto,
                        mensaje,  # texto plano como fallback
                        "glex.globalexchange.respaldo@gmail.com",
                        [regla.usuario.email],
                        fail_silently=False,
                        html_message=cuerpo,
                    )
                    logger.info(f"� Correo enviado a {regla.usuario.email}")
                except Exception as e:
                    logger.error(f"❌ Error al enviar correo a {regla.usuario.email}: {e}")

            notif = Notificacion.objects.create(
                usuario=regla.usuario,
                alerta_base=regla,
                mensaje=mensaje,
                correo_enviado=True if canal in ["correo", "sistema_correo"] else False
            )
            logger.info(f"✅ Notificación creada ID {notif.id} para {regla.usuario.username}")
        else:
            logger.info(f"⏭️  Condición no cumplida para regla ID {regla.id}")
