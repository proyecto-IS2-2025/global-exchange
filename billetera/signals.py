from django.db.models.signals import post_save
from django.dispatch import receiver
from billetera.models import BilleteraUser, Billetera

@receiver(post_save, sender=BilleteraUser)
def crear_billetera_automatica(sender, instance, created, **kwargs):
    if created:
        Billetera.objects.get_or_create(usuario=instance)
