# clientes/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from clientes.models import Segmento, Descuento
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

    for divisa in Divisa.objects.filter(is_active=True):
        tasa = TasaCambio.objects.filter(divisa=divisa).order_by('-fecha').first()
        if tasa:
            generar_cotizaciones_por_segmento(divisa, tasa, usuario)


@receiver(post_save, sender=Descuento)
def regenerar_cotizaciones_si_descuento_cambia(sender, instance, created, **kwargs):
    """
    Cuando se crea o edita un Descuento, regenerar cotizaciones para el segmento afectado.
    """
    usuario = None  # igual que arriba

    for divisa in Divisa.objects.filter(is_active=True):
        tasa = TasaCambio.objects.filter(divisa=divisa).order_by('-fecha').first()
        if tasa:
            generar_cotizaciones_por_segmento(divisa, tasa, usuario)
