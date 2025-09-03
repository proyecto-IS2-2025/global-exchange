from django.db import models
from django.db.models import functions


class Divisa(models.Model):
    code = models.CharField('Código', max_length=10, unique=True)
    nombre = models.CharField('Nombre', max_length=100)
    simbolo = models.CharField('Símbolo', max_length=5, default='', blank=True)
    is_active = models.BooleanField('Activa', default=False)  # nace deshabilitada
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Divisa'
        verbose_name_plural = 'Divisas'
        constraints = [
            # Unicidad case-insensitive del código
            models.UniqueConstraint(
                functions.Upper('code'),
                name='uniq_divisa_code_upper'
            ),
        ]
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def save(self, *args, **kwargs):
        self.code = (self.code or '').upper().strip()
        self.simbolo = (self.simbolo or '').strip()
        super().save(*args, **kwargs)

    def __str__(self):
        estado = 'Activa' if self.is_active else 'Deshabilitada'
        return f'{self.code} - {self.nombre} ({estado})'


class TasaCambio(models.Model):
    divisa = models.ForeignKey(
        Divisa,
        on_delete=models.CASCADE,
        related_name='tasas'
    )
    fecha = models.DateField('Fecha')
    valor_compra = models.DecimalField(
        'Valor de compra',
        max_digits=12,
        decimal_places=4
    )
    valor_venta = models.DecimalField(
        'Valor de venta',
        max_digits=12,
        decimal_places=4
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tasa de Cambio'
        verbose_name_plural = 'Tasas de Cambio'
        ordering = ['fecha']
        constraints = [
            models.UniqueConstraint(
                fields=['divisa', 'fecha'],
                name='uniq_divisa_fecha'
            ),
        ]
        indexes = [
            models.Index(fields=['divisa', 'fecha']),
        ]

    def __str__(self):
        return f"{self.divisa.code} - {self.fecha}: {self.valor_compra}/{self.valor_venta}"
