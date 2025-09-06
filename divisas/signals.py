from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TasaCambio, Divisa
from .services import generar_cotizaciones_por_segmento

from django.db import transaction

@receiver(post_save, sender=TasaCambio)
def crear_cotizaciones_segmento(sender, instance, created, **kwargs):
    if not created:
        return
    transaction.on_commit(  # dispara tras commit para evitar duplicados si hay rollbacks
        lambda: generar_cotizaciones_por_segmento(
            divisa=instance.divisa,
            tasa=instance,
            usuario=getattr(instance, 'creado_por', None)
        )
    )
