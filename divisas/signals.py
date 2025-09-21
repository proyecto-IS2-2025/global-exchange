#divisas
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TasaCambio
from .services import generar_cotizaciones_por_segmento
from django.db import transaction
from django.contrib.auth import get_user_model

@receiver(post_save, sender=TasaCambio)
def crear_cotizaciones_segmento(sender, instance, created, **kwargs):
    if not created:
        return
    
    # Obtener un usuario por defecto (puede ser el primer superusuario)
    User = get_user_model()
    try:
        usuario_default = User.objects.filter(is_superuser=True).first()
    except:
        usuario_default = None
    
    transaction.on_commit(
        lambda: generar_cotizaciones_por_segmento(
            divisa=instance.divisa,
            tasa=instance,
            usuario=usuario_default  # Usar un usuario por defecto
        )
    )