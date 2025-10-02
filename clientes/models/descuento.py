"""
Modelos relacionados con descuentos por segmento.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser


class Descuento(models.Model):
    """Descuentos aplicados por segmento de cliente."""
    segmento = models.OneToOneField(
        'clientes.Segmento',
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name="Segmento de Cliente"
    )
    porcentaje_descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)],
        verbose_name="Descuento aplicado (%)"
    )
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Modificación")
    modificado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Modificado por"
    )

    class Meta:
        verbose_name = "Descuento"
        verbose_name_plural = "Descuentos"

    def __str__(self):
        return f"Descuento para {self.segmento.name}"


class HistorialDescuentos(models.Model):
    """Historial de cambios en descuentos."""
    descuento = models.ForeignKey(Descuento, on_delete=models.CASCADE, verbose_name="Descuento")
    porcentaje_descuento_anterior = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="Descuento anterior (%)"
    )
    porcentaje_descuento_nuevo = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="Nuevo descuento (%)"
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Cambio")
    modificado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Modificado por"
    )

    class Meta:
        verbose_name = "Historial de Descuento"
        verbose_name_plural = "Historial de Descuentos"
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"Cambio en descuento de {self.descuento.segmento.name} el {self.fecha_cambio.strftime('%Y-%m-%d')}"