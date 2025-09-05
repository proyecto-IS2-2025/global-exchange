from django.db import models
from django.db.models import functions


class MedioDePago(models.Model):
    # Tipos de medios de pago según los requerimientos
    TIPO_MEDIO_CHOICES = [
        ('TARJETA', 'Tarjeta de Crédito'),
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('BILLETERA', 'Billetera Digital'),
        ('CHEQUE', 'Cheque')
    ]

    nombre = models.CharField('Nombre del medio', max_length=100, unique=True)
    tipo = models.CharField(
        'Tipo de medio',
        max_length=20,
        choices=TIPO_MEDIO_CHOICES,
        default='TARJETA'
    )
    comision_porcentaje = models.DecimalField(
        'Comisión (%)',
        max_digits=5,
        decimal_places=2,
        default=0
    )
    is_active = models.BooleanField('Activo', default=False)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Medio de Pago'
        verbose_name_plural = 'Medios de Pago'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['tipo']),
        ]

    def __str__(self):
        estado = 'Activo' if self.is_active else 'Deshabilitado'
        return f'{self.nombre} ({self.get_tipo_display()}) - {estado}'