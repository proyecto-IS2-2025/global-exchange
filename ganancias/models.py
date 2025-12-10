from django.db import models
from django.utils import timezone
from decimal import Decimal
from divisas.models import Divisa
from transacciones.models import Transaccion
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta


class RegistroGanancia(models.Model):
    """
    Modelo para registrar las ganancias generadas por cada transacción
    """
    TIPO_GANANCIA_CHOICES = [
        ('comision', 'Comisión'),
        ('spread', 'Margen'),
    ]
    
    transaccion = models.OneToOneField(
        'transacciones.Transaccion',
        on_delete=models.CASCADE,
        related_name='ganancia',
        verbose_name='Transacción'
    )
    
    tipo_ganancia = models.CharField(
        'Tipo de Ganancia',
        max_length=10,
        choices=TIPO_GANANCIA_CHOICES
    )
    
    monto_comision = models.DecimalField(
        'Monto de Comisión',
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Ganancia por comisión cobrada al cliente'
    )
    
    monto_spread = models.DecimalField(
        'Monto de Margen',
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Ganancia por diferencia entre tasa de compra y venta'
    )
    
    monto_total = models.DecimalField(
        'Monto Total de Ganancia',
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Ganancia total (comisión + spread) en PYG'
    )
    
    divisa_referencia = models.ForeignKey(
        'divisas.Divisa',
        on_delete=models.PROTECT,
        related_name='ganancias',
        verbose_name='Divisa de Referencia',
        help_text='Divisa extranjera involucrada en la transacción'
    )
    
    porcentaje_comision = models.DecimalField(
        'Porcentaje de Comisión',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Porcentaje de comisión aplicado'
    )
    
    fecha_registro = models.DateTimeField(
        'Fecha de Registro',
        auto_now_add=True
    )
    
    fecha_transaccion = models.DateTimeField(
        'Fecha de Transacción',
        help_text='Fecha de la transacción asociada'
    )
    
    notas = models.TextField(
        'Notas',
        blank=True,
        help_text='Observaciones adicionales sobre la ganancia'
    )
    
    class Meta:
        verbose_name = 'Registro de Ganancia'
        verbose_name_plural = 'Registros de Ganancias'
        ordering = ['-fecha_transaccion']
        indexes = [
            models.Index(fields=['fecha_transaccion']),
            models.Index(fields=['tipo_ganancia']),
            models.Index(fields=['divisa_referencia']),
        ]
    
    def __str__(self):
        return f"Ganancia {self.transaccion.numero_transaccion} - {self.get_tipo_ganancia_display()}: {self.monto_total} PYG"
    
    def save(self, *args, **kwargs):
        # El monto total ES SOLO el spread (ganancia real), no incluye comisión
        self.monto_total = self.monto_spread
        
        # Si no se ha establecido la fecha de transacción, usar la de la transacción asociada
        if not self.fecha_transaccion and self.transaccion:
            self.fecha_transaccion = self.transaccion.fecha_creacion
        
        super().save(*args, **kwargs)
    
    @classmethod
    def calcular_ganancia_transaccion(cls, transaccion):
        """
        Calcula y crea/actualiza el registro de ganancia para una transacción.
        La ganancia real proviene solo del margen de spread, no de la comisión del medio de pago.
        """
        from decimal import Decimal, ROUND_HALF_UP
        
        # Solo calcular para transacciones completadas o pagadas
        if transaccion.estado not in ['completado', 'pagada']:
            return None
        
        # Determinar la divisa extranjera
        divisa_extranjera = None
        if transaccion.divisa_origen.code.upper() in ['PYG', '116']:
            divisa_extranjera = transaccion.divisa_destino
        else:
            divisa_extranjera = transaccion.divisa_origen
        
        # La comisión del medio de pago NO es ganancia, solo se registra como información
        monto_comision = Decimal('0.00')
        porcentaje_comision = Decimal('0.00')
        
        if hasattr(transaccion, 'comision_aplicada') and transaccion.comision_aplicada:
            monto_comision = transaccion.comision_aplicada
        
        if hasattr(transaccion, 'porcentaje_comision') and transaccion.porcentaje_comision:
            porcentaje_comision = transaccion.porcentaje_comision
        
        # Calcular margen (ESTA ES LA GANANCIA REAL)
        monto_spread = Decimal('0.00')
        
        if hasattr(transaccion, 'margen_spread') and transaccion.margen_spread:
            # Ganancia = margen_spread × cantidad de divisa extranjera
            if transaccion.tipo_operacion == 'compra':
                # En compra: compramos divisa extranjera (monto_destino)
                # margen_spread × monto_destino (divisa comprada)
                cantidad_divisa = transaccion.monto_destino
                monto_spread = (transaccion.margen_spread * cantidad_divisa).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
            else:
                # En venta: vendemos divisa extranjera (monto_origen)
                # margen_spread × monto_origen (divisa vendida)
                cantidad_divisa = transaccion.monto_origen
                monto_spread = (transaccion.margen_spread * cantidad_divisa).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
        
        # Crear o actualizar el registro
        registro, created = cls.objects.update_or_create(
            transaccion=transaccion,
            defaults={
                'tipo_ganancia': 'spread' if monto_spread > 0 else 'comision',
                'monto_comision': Decimal('0.00'),  # No contamos comisión como ganancia
                'monto_spread': monto_spread,  # Esta es la ganancia real (margen)
                'divisa_referencia': divisa_extranjera,
                'porcentaje_comision': porcentaje_comision,
                'fecha_transaccion': transaccion.fecha_creacion,
            }
        )
        
        return registro


class ResumenGananciaDiaria(models.Model):
    """
    Resumen consolidado de ganancias por día
    """
    fecha = models.DateField(
        'Fecha',
        unique=True,
        db_index=True
    )
    
    total_comisiones = models.DecimalField(
        'Total Comisiones',
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    total_spread = models.DecimalField(
        'Total Margen',
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    total_general = models.DecimalField(
        'Total General',
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    cantidad_transacciones = models.IntegerField(
        'Cantidad de Transacciones',
        default=0
    )
    
    ultima_actualizacion = models.DateTimeField(
        'Última Actualización',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Resumen de Ganancia Diaria'
        verbose_name_plural = 'Resúmenes de Ganancias Diarias'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Resumen {self.fecha}: {self.total_general} PYG"
    
    @classmethod
    def actualizar_resumen(cls, fecha):
        """
        Actualiza el resumen de ganancias para una fecha específica
        """
        ganancias_dia = RegistroGanancia.objects.filter(
            fecha_transaccion__date=fecha
        )
        
        totales = ganancias_dia.aggregate(
            total_comisiones=Sum('monto_comision'),
            total_spread=Sum('monto_spread'),
            total_general=Sum('monto_total'),
            cantidad=Count('id')
        )
        
        resumen, created = cls.objects.update_or_create(
            fecha=fecha,
            defaults={
                'total_comisiones': totales['total_comisiones'] or Decimal('0.00'),
                'total_spread': totales['total_spread'] or Decimal('0.00'),
                'total_general': totales['total_general'] or Decimal('0.00'),
                'cantidad_transacciones': totales['cantidad'] or 0,
            }
        )
        
        return resumen


class ResumenGananciaMensual(models.Model):
    """
    Resumen consolidado de ganancias por mes
    """
    año = models.IntegerField('Año')
    mes = models.IntegerField('Mes')
    
    total_comisiones = models.DecimalField(
        'Total Comisiones',
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    total_spread = models.DecimalField(
        'Total Margen',
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    total_general = models.DecimalField(
        'Total General',
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    cantidad_transacciones = models.IntegerField(
        'Cantidad de Transacciones',
        default=0
    )
    
    promedio_diario = models.DecimalField(
        'Promedio Diario',
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    ultima_actualizacion = models.DateTimeField(
        'Última Actualización',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Resumen de Ganancia Mensual'
        verbose_name_plural = 'Resúmenes de Ganancias Mensuales'
        ordering = ['-año', '-mes']
        unique_together = ['año', 'mes']
    
    def __str__(self):
        return f"Resumen {self.mes}/{self.año}: {self.total_general} PYG"
    
    @classmethod
    def actualizar_resumen(cls, año, mes):
        """
        Actualiza el resumen de ganancias para un mes específico
        """
        ganancias_mes = RegistroGanancia.objects.filter(
            fecha_transaccion__year=año,
            fecha_transaccion__month=mes
        )
        
        totales = ganancias_mes.aggregate(
            total_comisiones=Sum('monto_comision'),
            total_spread=Sum('monto_spread'),
            total_general=Sum('monto_total'),
            cantidad=Count('id')
        )
        
        # Calcular promedio diario
        dias_en_mes = ResumenGananciaDiaria.objects.filter(
            fecha__year=año,
            fecha__month=mes
        ).count()
        
        promedio = Decimal('0.00')
        if dias_en_mes > 0:
            promedio = (totales['total_general'] or Decimal('0.00')) / Decimal(str(dias_en_mes))
        
        resumen, created = cls.objects.update_or_create(
            año=año,
            mes=mes,
            defaults={
                'total_comisiones': totales['total_comisiones'] or Decimal('0.00'),
                'total_spread': totales['total_spread'] or Decimal('0.00'),
                'total_general': totales['total_general'] or Decimal('0.00'),
                'cantidad_transacciones': totales['cantidad'] or 0,
                'promedio_diario': promedio,
            }
        )
        
        return resumen
