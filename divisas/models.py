from django.db import models
from django.db.models import Q
from django.db.models.functions import Upper
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
creado_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)


Q8 = Decimal('0.00000001')
C100 = Decimal('100')


class CotizacionSegmentoQuerySet(models.QuerySet):
    def recientes(self):
        return self.order_by('-fecha')

    def ultima_para(self, divisa, segmento):
        return (self.filter(divisa=divisa, segmento=segmento)
                    .order_by('-fecha')
                    .first())


class CotizacionSegmento(models.Model):
    """
    Una cotización 'unitaria' por segmento (Gs x 1 USD) en una fecha.
    Congela: precio_base y comisiones de la tasa, y el % de descuento del segmento.
    """
    fecha = models.DateTimeField(auto_now_add=True)

    # claves
    divisa = models.ForeignKey('divisas.Divisa', on_delete=models.PROTECT)
    segmento = models.ForeignKey('clientes.Segmento', on_delete=models.PROTECT)

    # snapshot de la tasa usada (si mañana cambia, esta fila no cambia)
    precio_base = models.DecimalField(max_digits=20, decimal_places=8)      # Gs x 1 USD
    comision_compra = models.DecimalField(max_digits=20, decimal_places=8)  # Gs x 1 USD
    comision_venta  = models.DecimalField(max_digits=20, decimal_places=8)  # Gs x 1 USD

    # snapshot del % descuento del segmento (0..100)
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # resultados ya calculados (Gs x 1 USD)
    # Compra (yo compro dólares): PB - (COM_COM - COM_COM*%/100)
    valor_compra_unit = models.DecimalField(max_digits=20, decimal_places=8)
    # Venta  (yo vendo dólares): PB + (COM_VTA - COM_VTA*%/100)
    valor_venta_unit  = models.DecimalField(max_digits=20, decimal_places=8)

    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    objects = CotizacionSegmentoQuerySet.as_manager()

    class Meta:
        verbose_name = 'Cotización por segmento'
        verbose_name_plural = 'Cotizaciones por segmento'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['divisa', 'segmento', 'fecha']),
        ]

    # ---------- helpers internos ----------
    @staticmethod
    def _ajustar_comision(comision, por_des):
        # comision_efectiva = COMISION - (COMISION * % / 100)
        return (comision - (comision * por_des / C100)).quantize(Q8, ROUND_HALF_UP)

    def calcular_valores(self):
        d = self.porcentaje_descuento or Decimal('0')
        com_vta_ef = self._ajustar_comision(self.comision_venta, d)
        com_com_ef = self._ajustar_comision(self.comision_compra, d)

        self.valor_venta_unit  = (self.precio_base + com_vta_ef).quantize(Q8, ROUND_HALF_UP)
        self.valor_compra_unit = (self.precio_base - com_com_ef).quantize(Q8, ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        # Si no están pre-calculados, calcúlalos
        if self.valor_compra_unit is None or self.valor_venta_unit is None:
            self.calcular_valores()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.divisa.code} / {self.segmento.name} @ {self.fecha:%Y-%m-%d %H:%M}"

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
    divisa = models.ForeignKey(Divisa, on_delete=models.CASCADE, related_name='tasas')

    fecha = models.DateTimeField('Fecha y hora', auto_now_add=True)

    precio_base = models.DecimalField('Precio base', max_digits=20, decimal_places=8)
    comision_compra = models.DecimalField('Comisión compra', max_digits=20, decimal_places=8, default=0)
    comision_venta = models.DecimalField('Comisión venta', max_digits=20, decimal_places=8, default=0)

    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tasa de Cambio'
        verbose_name_plural = 'Tasas de Cambio'
        ordering = ['-fecha']
        indexes = [models.Index(fields=['divisa', 'fecha'])]

    def __str__(self):
        return f"{self.divisa.code} - {self.fecha}: {self.precio_base} (Compra:{self.comision_compra}, Venta:{self.comision_venta})"
