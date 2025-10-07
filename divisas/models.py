#divisas
from django.db import models
from django.db.models import Q
from django.db.models.functions import Upper
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.contrib.auth import get_user_model
"""
Modelos de divisas y cotizaciones.

Este módulo define las entidades principales para manejar divisas, tasas de cambio
y cotizaciones por segmento. Los modelos permiten almacenar información sobre las
monedas disponibles, su historial de tasas y los valores ajustados por segmento.
"""
User = get_user_model()
creado_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)


Q8 = Decimal('0.00000001')
C100 = Decimal('100')


class CotizacionSegmentoQuerySet(models.QuerySet):
    """
    Conjunto de consultas personalizado para CotizacionSegmento.

    Proporciona métodos auxiliares para obtener registros recientes
    y la última cotización para un segmento específico.
    """
    def recientes(self):
        return self.order_by('-fecha')

    def ultima_para(self, divisa, segmento):
        return (self.filter(divisa=divisa, segmento=segmento)
                    .order_by('-fecha')
                    .first())


class CotizacionSegmento(models.Model):
    """
    Representa una cotización unitaria de una divisa para un segmento.

    :param divisa: Divisa relacionada con la cotización.
    :type divisa: Divisa
    :param segmento: Segmento de cliente asociado.
    :type segmento: clientes.Segmento
    :param precio_base: Precio base congelado de la tasa.
    :type precio_base: Decimal
    :param comision_compra: Comisión de compra congelada.
    :type comision_compra: Decimal
    :param comision_venta: Comisión de venta congelada.
    :type comision_venta: Decimal
    :param porcentaje_descuento: Descuento aplicado al segmento.
    :type porcentaje_descuento: Decimal
    :param valor_compra_unit: Valor de compra final (con descuento).
    :type valor_compra_unit: Decimal
    :param valor_venta_unit: Valor de venta final (con descuento).
    :type valor_venta_unit: Decimal
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

    @property
    def comision_compra_ajustada(self):
        return self._ajustar_comision(self.comision_compra, self.porcentaje_descuento)
    
    @property
    def comision_venta_ajustada(self):
        return self._ajustar_comision(self.comision_venta, self.porcentaje_descuento)

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
    is_active = models.BooleanField('Activa', default=False)
    decimales = models.PositiveSmallIntegerField('Decimales', default=2)
    es_moneda_base = models.BooleanField('Moneda Base', default=False, editable=False)  # NUEVO
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Divisa'
        verbose_name_plural = 'Divisas'
        constraints = [
            models.UniqueConstraint(
                Upper('code'),
                name='uniq_divisa_code_upper'
            ),
            models.CheckConstraint(
                check=Q(decimales__gte=0) & Q(decimales__lte=8),
                name='chk_divisa_decimales_0_8',
            ),
        ]
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['es_moneda_base']),  # NUEVO
        ]

    def save(self, *args, **kwargs):
        self.code = (self.code or '').upper().strip()
        self.simbolo = (self.simbolo or '').strip()
        
        # Auto-marcar PYG como moneda base
        if self.code == 'PYG':
            self.es_moneda_base = True
            self.is_active = True
        
        if self.decimales is None:
            self.decimales = 2
        else:
            self.decimales = max(0, min(8, int(self.decimales)))
        
        super().save(*args, **kwargs)

    def __str__(self):
        if self.es_moneda_base:
            return f'{self.code} - {self.nombre} (Moneda base)'
        estado = 'Activa' if self.is_active else 'Deshabilitada'
        return f'{self.code} - {self.nombre} ({estado})'


class TasaCambio(models.Model):
    """
    Representa una tasa de cambio histórica de una divisa.

    Incluye precio base, comisiones de compra y venta, y fecha de creación.

    :param divisa: Divisa asociada a la tasa.
    :type divisa: Divisa
    :param fecha: Fecha y hora de registro.
    :type fecha: datetime
    :param precio_base: Precio base de la divisa.
    :type precio_base: Decimal
    :param comision_compra: Comisión aplicada en la compra.
    :type comision_compra: Decimal
    :param comision_venta: Comisión aplicada en la venta.
    :type comision_venta: Decimal
    """
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
