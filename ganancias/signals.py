from django.db.models.signals import post_save
from django.dispatch import receiver
from transacciones.models import Transaccion
from .models import RegistroGanancia, ResumenGananciaDiaria, ResumenGananciaMensual
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transaccion)
def calcular_ganancia_automatica(sender, instance, created, **kwargs):
    """
    Señal para calcular automáticamente la ganancia cuando una transacción se completa o paga
    """
    # Solo calcular ganancia para transacciones completadas o pagadas
    if instance.estado in ['completado', 'pagada']:
        try:
            # Calcular y crear/actualizar el registro de ganancia
            registro = RegistroGanancia.calcular_ganancia_transaccion(instance)
            
            if registro:
                # Actualizar resúmenes
                fecha = instance.fecha_creacion.date()
                ResumenGananciaDiaria.actualizar_resumen(fecha)
                ResumenGananciaMensual.actualizar_resumen(fecha.year, fecha.month)
                
                logger.info(f"Ganancia calculada automáticamente para transacción {instance.numero_transaccion}")
        except Exception as e:
            logger.error(f"Error al calcular ganancia para transacción {instance.numero_transaccion}: {str(e)}")
