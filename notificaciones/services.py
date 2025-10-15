from .models import NotificacionTasa, Notificacion
from divisas.models import CotizacionSegmento
from django.core.mail import send_mail
from .models import ConfiguracionGeneral


def evaluar_alertas(nueva_cotizacion: CotizacionSegmento):
    """
    Evalúa las alertas configuradas por los usuarios según la nueva cotización.
    Crea notificaciones con formato uniforme y mensajes claros.
    """

    reglas_activas = NotificacionTasa.objects.filter(
        divisa=nueva_cotizacion.divisa.code,
        activa=True,
        cliente_asociado__segmento=nueva_cotizacion.segmento
    )

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
        if canal in ["sistema_correo"]:
            asunto = "📢 Nueva notificación de tasa de cambio"
            # URL de destino (por ahora localhost)
            url_notificaciones = "http://127.0.0.1:8000/"

            # cuerpo del correo con botón HTML
            cuerpo = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #333;">
                <p>Hola <strong>{regla.usuario.first_name or regla.usuario.username}</strong>,</p>
                <p>{mensaje}</p>
                <p>
                  <a href="{url_notificaciones}" 
                     style="background-color:#0d6efd; color:white; padding:10px 18px; 
                            text-decoration:none; border-radius:6px; display:inline-block;">
                     Ir a Global Exchange
                  </a>
                </p>
                <p style="font-size:12px; color:#777;">Global Exchange ©</p>
              </body>
            </html>
            """

            # envío del correo
            send_mail(
                asunto,
                "",  # cuerpo plano vacío
                "glex.globalexchange@gmail.com",  # remitente
                [regla.usuario.email],  # destinatario
                fail_silently=True,
                html_message=cuerpo,  # cuerpo HTML con botón
            )

        # 🔹 Crear la notificación si corresponde
        if condicion_cumplida:
            Notificacion.objects.create(
                usuario=regla.usuario,
                alerta_base=regla,
                mensaje=mensaje,
                correo_enviado=True if canal in ["correo", "sistema_y_correo"] else False
            )
