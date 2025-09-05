from django.db import models
from django.db.models import functions


class Divisa(models.Model):
    """
    Modelo que representa una divisa o moneda en el sistema.

    Almacena información como el código, nombre, símbolo y estado de la divisa.
    El campo `code` tiene una restricción de unicidad que no distingue entre mayúsculas y minúsculas.
    
    :param code: Código único de la divisa (ej. USD, EUR).
    :type code: str
    :param nombre: Nombre completo de la divisa (ej. Dólar Americano).
    :type nombre: str
    :param simbolo: Símbolo de la divisa (ej. $, €).
    :type simbolo: str
    :param is_active: Estado de la divisa, `False` por defecto.
    :type is_active: bool
    """
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
        """
        Sobreescribe el método save para formatear el código y el símbolo antes de guardar.
        """
        self.code = (self.code or '').upper().strip()
        self.simbolo = (self.simbolo or '').strip()
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Representación de cadena del modelo Divisa.
        
        :return: Una cadena que describe la divisa y su estado.
        :rtype: str
        """
        estado = 'Activa' if self.is_active else 'Deshabilitada'
        return f'{self.code} - {self.nombre} ({estado})'


class TasaCambio(models.Model):
    """
    Modelo que almacena las tasas de cambio de una divisa en una fecha específica.

    Cada instancia de este modelo está ligada a una :class:`~divisas.models.Divisa`.

    :param divisa: La divisa a la que se aplica esta tasa de cambio.
    :type divisa: :class:`~divisas.models.Divisa`
    :param fecha: La fecha en la que la tasa es válida.
    :type fecha: date
    :param valor_compra: El valor de compra de la divisa.
    :type valor_compra: Decimal
    :param valor_venta: El valor de venta de la divisa.
    :type valor_venta: Decimal
    """
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
                name='unique_tasa_por_divisa_fecha'
            ),
        ]
        indexes = [
            models.Index(fields=['divisa', 'fecha']),
        ]

    def __str__(self):
        """
        Representación de cadena del modelo TasaCambio.

        :return: Una cadena que describe la tasa de cambio.
        :rtype: str
        """
        return f'{self.divisa.code} - {self.fecha}'
