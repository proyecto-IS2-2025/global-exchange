"""
Integración de facturación electrónica con el modelo de Transacciones
"""
from django.db import models


class FacturaElectronica(models.Model):
    """
    Modelo para registrar las facturas electrónicas generadas
    """
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Relación con la transacción
    transaccion = models.OneToOneField(
        'transacciones.Transaccion',
        on_delete=models.PROTECT,
        related_name='factura_electronica'
    )
    
    # Datos de la factura
    numero_factura = models.CharField(
        'Número de Factura',
        max_length=20,
        unique=True,
        help_text='Formato: 001-003-0000051'
    )
    
    establecimiento = models.CharField(
        'Establecimiento',
        max_length=3,
        default='001'
    )
    
    punto_expedicion = models.CharField(
        'Punto de Expedición',
        max_length=3,
        default='003'
    )
    
    numero_documento = models.CharField(
        'Número de Documento',
        max_length=7,
        help_text='Formato: 0000051'
    )
    
    # ID del documento en el SQL Proxy
    de_id = models.IntegerField(
        'ID en SQL Proxy',
        null=True,
        blank=True
    )
    
    # CDC (Código de Control del documento)
    cdc = models.CharField(
        'CDC',
        max_length=50,
        blank=True,
        null=True,
        help_text='Código de Control asignado por SIFEN'
    )
    
    # Estado
    estado = models.CharField(
        'Estado',
        max_length=15,
        choices=ESTADO_CHOICES,
        default='borrador'
    )
    
    estado_sifen = models.CharField(
        'Estado SIFEN',
        max_length=255,
        blank=True
    )
    
    descripcion_sifen = models.TextField(
        'Descripción SIFEN',
        blank=True
    )
    
    error_sifen = models.TextField(
        'Error SIFEN',
        blank=True
    )
    
    # Fechas
    fecha_emision = models.DateTimeField(
        'Fecha de Emisión',
        auto_now_add=True
    )
    
    fecha_aprobacion = models.DateTimeField(
        'Fecha de Aprobación SIFEN',
        null=True,
        blank=True
    )
    
    # URL del KuDE (PDF)
    url_kude_pdf = models.URLField(
        'URL KuDE PDF',
        blank=True,
        null=True,
        help_text='URL para descargar el PDF de la factura'
    )
    
    # URL del XML
    url_kude_xml = models.URLField(
        'URL KuDE XML',
        blank=True,
        null=True,
        help_text='URL para descargar el XML firmado'
    )
    
    # Datos adicionales
    datos_factura = models.JSONField(
        'Datos de la Factura',
        default=dict,
        blank=True,
        help_text='Datos completos utilizados para generar la factura'
    )
    
    class Meta:
        verbose_name = 'Factura Electrónica'
        verbose_name_plural = 'Facturas Electrónicas'
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['numero_factura']),
            models.Index(fields=['cdc']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_emision']),
        ]
    
    def __str__(self):
        return f"{self.numero_factura} - {self.transaccion.cliente.nombre_completo}"
    
    def get_numero_completo(self):
        """Retorna el número de factura completo"""
        return f"{self.establecimiento}-{self.punto_expedicion}-{self.numero_documento}"
    
    def esta_aprobada(self):
        """Verifica si la factura está aprobada por SIFEN"""
        return self.estado == 'aprobado' and bool(self.cdc)
