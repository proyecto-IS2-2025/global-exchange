"""
Modelos para límites diarios y mensuales de operaciones.
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class LimiteDiario(models.Model):
    """Límite diario de operaciones."""
    fecha = models.DateField(unique=True, help_text="Fecha a la que aplica el límite")
    monto = models.DecimalField(
        max_digits=20, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    inicio_vigencia = models.DateTimeField(help_text="Fecha y hora en que entra en vigencia el límite")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Límite Diario"
        verbose_name_plural = "Límites Diarios"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Límite Diario {self.fecha}: {self.monto}"


class LimiteMensual(models.Model):
    """Límite mensual de operaciones."""
    mes = models.DateField(unique=True, help_text="Se guarda como el primer día del mes")
    monto = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    inicio_vigencia = models.DateTimeField()
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Límite Mensual"
        verbose_name_plural = "Límites Mensuales"
        ordering = ["-mes"]

    def __str__(self):
        return f"Límite Mensual {self.mes.strftime('%B %Y')}: {self.monto}"