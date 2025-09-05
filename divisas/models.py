from django.db import models
from django.db.models import Q
from django.db.models.functions import Upper


class Divisa(models.Model):
    code = models.CharField('Código', max_length=10, unique=True)
    nombre = models.CharField('Nombre', max_length=100)
    simbolo = models.CharField('Símbolo', max_length=5, default='', blank=True)
    is_active = models.BooleanField('Activa', default=False)  # nace deshabilitada
    decimales = models.PositiveSmallIntegerField('Decimales', default=2)  # nuevo campo
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Divisa'
        verbose_name_plural = 'Divisas'
        constraints = [
            # Unicidad case-insensitive del código
            models.UniqueConstraint(
                Upper('code'),
                name='uniq_divisa_code_upper'
            ),
            # Rango válido para cantidad de decimales
            models.CheckConstraint(
                check=Q(decimales__gte=0) & Q(decimales__lte=8),
                name='chk_divisa_decimales_0_8',
            ),
        ]
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def save(self, *args, **kwargs):
        self.code = (self.code or '').upper().strip()
        self.simbolo = (self.simbolo or '').strip()
        # Clamp defensivo por si llega algo fuera de rango antes del CheckConstraint
        if self.decimales is None:
            self.decimales = 2
        else:
            self.decimales = max(0, min(8, int(self.decimales)))
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
    precio_base = models.DecimalField(
        'Precio base',
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
        return f"{self.divisa.code} - {self.fecha}: {self.precio_base}"
