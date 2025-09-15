# clientes/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from clientes.models import Segmento
from divisas.models import Divisa, TasaCambio
from divisas.services import generar_cotizaciones_por_segmento


@receiver(post_save, sender=Segmento)
def generar_cotizaciones_para_segmento_nuevo(sender, instance, created, **kwargs):
    """
    Cuando se crea un Segmento nuevo, generar cotizaciones para cada divisa activa
    usando la última tasa de cambio disponible.
    """
    if not created:
        return

    usuario = None  # o asignar un usuario de sistema si corresponde

    # recorrer todas las divisas activas
    for divisa in Divisa.objects.filter(is_active=True):
        # tomar la última tasa creada para esa divisa
        tasa = TasaCambio.objects.filter(divisa=divisa).order_by('-fecha').first()
        if tasa:
            generar_cotizaciones_por_segmento(divisa, tasa, usuario)
