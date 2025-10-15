# divisas/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.contrib.auth import get_user_model

# Importaciones de modelos y servicios
from .models import TasaCambio, CotizacionSegmento
from .services import generar_cotizaciones_por_segmento
from notificaciones.services import evaluar_alertas


@receiver(post_save, sender=TasaCambio)
def crear_cotizaciones_segmento(sender, instance, created, **kwargs):
    """
    Señal post_save que se activa al crear una nueva TasaCambio.

    Esta función obtiene un usuario por defecto y delega la creación de las
    cotizaciones específicas por segmento al servicio `generar_cotizaciones_por_segmento`
    dentro de una transacción `on_commit`.

    Args:
        sender (Model): Modelo que envió la señal (TasaCambio).
        instance (TasaCambio): Instancia recién creada de TasaCambio.
        created (bool): True si el registro fue creado, False si fue actualizado.
        **kwargs: Argumentos de palabra clave adicionales.
    """
    if not created:
        return

    User = get_user_model()
    try:
        # Se obtiene el usuario dentro de la función para evitar RuntimeWarning.
        usuario_default = User.objects.filter(is_superuser=True).first()
    except Exception:
        usuario_default = None

    transaction.on_commit(
        lambda: generar_cotizaciones_por_segmento(
            divisa=instance.divisa,
            tasa=instance,
            usuario=usuario_default
        )
    )


@receiver(post_save, sender=CotizacionSegmento)
def evaluar_alertas_notificacion(sender, instance, created, **kwargs):
    """
    Señal post_save que se activa al crear una nueva CotizacionSegmento.

    Esta función dispara el servicio de evaluación de alertas para determinar
    si la nueva cotización unitaria (por segmento) cumple alguna de las reglas
    definidas por los usuarios en NotificacionTasa.

    Args:
        sender (Model): Modelo que envió la señal (CotizacionSegmento).
        instance (CotizacionSegmento): Instancia recién creada de CotizacionSegmento.
        created (bool): True si el registro fue creado, False si fue actualizado.
        **kwargs: Argumentos de palabra clave adicionales.
    """
    if not created:
        return

    transaction.on_commit(
        lambda: evaluar_alertas(instance)
    )