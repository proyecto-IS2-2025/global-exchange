from django.db import models
from django.conf import settings
from decimal import Decimal


class StripeTransaction(models.Model):
    """
    Modelo para registrar transacciones procesadas con Stripe
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('succeeded', 'Exitosa'),
        ('failed', 'Fallida'),
        ('canceled', 'Cancelada'),
        ('requires_action', 'Requiere Acción'),
        ('refunded', 'Reembolsada'),
    ]

    TRANSACTION_TYPE_CHOICES = [
        ('compra', 'Compra de Divisa'),
        ('venta', 'Venta de Divisa'),
    ]

    # Información del cliente
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='stripe_transactions',
        verbose_name='Cliente'
    )
    
    # Información de la transacción
    transaction_type = models.CharField(
        'Tipo de Transacción',
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        default='compra'
    )
    
    # IDs de Stripe
    payment_intent_id = models.CharField(
        'Payment Intent ID',
        max_length=255,
        unique=True,
        db_index=True,
        help_text='ID del Payment Intent en Stripe'
    )
    
    charge_id = models.CharField(
        'Charge ID',
        max_length=255,
        blank=True,
        null=True,
        help_text='ID del cargo en Stripe (si aplica)'
    )
    
    # Montos
    amount = models.DecimalField(
        'Monto',
        max_digits=15,
        decimal_places=2,
        help_text='Monto de la transacción en guaraníes'
    )
    
    currency = models.CharField(
        'Moneda',
        max_length=3,
        default='PYG',
        help_text='Código de moneda ISO'
    )
    
    # Información de la operación de divisa
    divisa_code = models.CharField(
        'Código de Divisa',
        max_length=10,
        blank=True,
        help_text='Código de la divisa operada (USD, EUR, etc.)'
    )
    
    monto_divisa = models.DecimalField(
        'Monto en Divisa',
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        help_text='Monto en la divisa extranjera'
    )
    
    tasa_cambio = models.DecimalField(
        'Tasa de Cambio',
        max_digits=15,
        decimal_places=6,
        blank=True,
        null=True,
        help_text='Tasa de cambio aplicada'
    )
    
    # Estado y respuesta
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    stripe_response = models.JSONField(
        'Respuesta de Stripe',
        blank=True,
        null=True,
        help_text='Respuesta completa de la API de Stripe'
    )
    
    error_message = models.TextField(
        'Mensaje de Error',
        blank=True,
        null=True,
        help_text='Mensaje de error si la transacción falló'
    )
    
    # Información de tarjeta (parcial por seguridad)
    card_last4 = models.CharField(
        'Últimos 4 dígitos',
        max_length=4,
        blank=True,
        help_text='Últimos 4 dígitos de la tarjeta'
    )
    
    card_brand = models.CharField(
        'Marca de Tarjeta',
        max_length=50,
        blank=True,
        help_text='Marca de la tarjeta (Visa, Mastercard, etc.)'
    )
    
    # Información del medio de pago del cliente
    cliente_medio_pago_id = models.IntegerField(
        'ID Medio de Pago Cliente',
        blank=True,
        null=True,
        help_text='ID del ClienteMedioDePago usado'
    )
    
    # Metadatos adicionales
    metadata = models.JSONField(
        'Metadatos',
        blank=True,
        null=True,
        help_text='Información adicional de la operación'
    )
    
    # Auditoría
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    # IP del cliente (opcional)
    client_ip = models.GenericIPAddressField(
        'IP del Cliente',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Transacción Stripe'
        verbose_name_plural = 'Transacciones Stripe'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['cliente', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.payment_intent_id} - {self.get_status_display()} - {self.amount} {self.currency}"

    @property
    def is_successful(self):
        """Verifica si la transacción fue exitosa"""
        return self.status == 'succeeded'

    @property
    def is_pending(self):
        """Verifica si la transacción está pendiente"""
        return self.status in ['pending', 'processing', 'requires_action']

    @property
    def is_failed(self):
        """Verifica si la transacción falló"""
        return self.status in ['failed', 'canceled']

    def get_amount_display(self):
        """Retorna el monto formateado"""
        return f"₲ {self.amount:,.0f}"

    def get_status_badge_class(self):
        """Retorna la clase CSS para el badge de estado"""
        status_classes = {
            'succeeded': 'badge-success',
            'failed': 'badge-danger',
            'canceled': 'badge-warning',
            'pending': 'badge-info',
            'processing': 'badge-primary',
            'requires_action': 'badge-warning',
        }
        return status_classes.get(self.status, 'badge-secondary')
