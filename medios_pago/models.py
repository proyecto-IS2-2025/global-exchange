# models.py - VersiÃ³n con campos predefinidos
from django.db import models
from django.core.exceptions import ValidationError


# DefiniciÃ³n de campos predefinidos por tipo de API
PREDEFINED_FIELDS = {
    # Campos comunes para tarjetas de crÃ©dito/dÃ©bito
    'card_number': {
        'label': 'NÃºmero de tarjeta',
        'type': 'NUMERO',
        'required': True,
        'description': 'NÃºmero de 16 dÃ­gitos de la tarjeta'
    },
    'exp_month': {
        'label': 'Mes de vencimiento',
        'type': 'NUMERO',
        'required': True,
        'description': 'Mes de vencimiento (1-12)'
    },
    'exp_year': {
        'label': 'AÃ±o de vencimiento', 
        'type': 'NUMERO',
        'required': True,
        'description': 'AÃ±o de vencimiento (4 dÃ­gitos)'
    },
    'cvc': {
        'label': 'CÃ³digo de seguridad',
        'type': 'NUMERO',
        'required': True,
        'description': 'CÃ³digo CVV/CVC de 3 o 4 dÃ­gitos'
    },
    'cardholder_name': {
        'label': 'Nombre en la tarjeta',
        'type': 'TEXTO',
        'required': True,
        'description': 'Nombre como aparece en la tarjeta'
    },
    
    # Campos para PayPal
    'paypal_email': {
        'label': 'Email de PayPal',
        'type': 'EMAIL',
        'required': True,
        'description': 'DirecciÃ³n de email asociada a PayPal'
    },
    
    # Campos bancarios
    'account_number': {
        'label': 'NÃºmero de cuenta',
        'type': 'NUMERO',
        'required': True,
        'description': 'NÃºmero de cuenta bancaria'
    },
    'bank_name': {
        'label': 'Nombre del banco',
        'type': 'TEXTO',
        'required': True,
        'description': 'Nombre completo del banco'
    },
    'account_holder': {
        'label': 'Titular de la cuenta',
        'type': 'TEXTO',
        'required': True,
        'description': 'Nombre del titular de la cuenta'
    },
    'routing_number': {
        'label': 'CÃ³digo de routing',
        'type': 'NUMERO',
        'required': False,
        'description': 'CÃ³digo de routing bancario (USA)'
    },
    'swift_code': {
        'label': 'CÃ³digo SWIFT',
        'type': 'TEXTO',
        'required': False,
        'description': 'CÃ³digo SWIFT para transferencias internacionales'
    },
    'cbu_cvu': {
        'label': 'CBU/CVU',
        'type': 'NUMERO',
        'required': True,
        'description': 'Clave Bancaria Uniforme o Clave Virtual Uniforme'
    },
    
    # Campos generales
    'email': {
        'label': 'Email',
        'type': 'EMAIL',
        'required': True,
        'description': 'DirecciÃ³n de correo electrÃ³nico'
    },
    'phone': {
        'label': 'TelÃ©fono',
        'type': 'TELEFONO',
        'required': False,
        'description': 'NÃºmero de telÃ©fono'
    },
    'amount': {
        'label': 'Monto',
        'type': 'NUMERO',
        'required': True,
        'description': 'Monto de la transacciÃ³n'
    },
    'currency': {
        'label': 'Moneda',
        'type': 'TEXTO',
        'required': True,
        'description': 'CÃ³digo de moneda (USD, EUR, etc.)'
    },
    'description': {
        'label': 'DescripciÃ³n',
        'type': 'TEXTO',
        'required': False,
        'description': 'DescripciÃ³n de la transacciÃ³n'
    },
    
    # Campos para criptomonedas
    'wallet_address': {
        'label': 'DirecciÃ³n de billetera',
        'type': 'TEXTO',
        'required': True,
        'description': 'DirecciÃ³n de billetera de criptomoneda'
    },
    'network': {
        'label': 'Red',
        'type': 'TEXTO',
        'required': True,
        'description': 'Red blockchain (ETH, BTC, etc.)'
    },
}

# Templates predefinidos para tipos comunes de medios de pago
PAYMENT_TEMPLATES = {
    'stripe': {
        'name': 'Stripe (Tarjeta)',
        'fields': ['card_number', 'exp_month', 'exp_year', 'cvc', 'cardholder_name', 'email']
    },
    'paypal': {
        'name': 'PayPal',
        'fields': ['paypal_email', 'amount', 'currency', 'description']
    },
    'bank_transfer': {
        'name': 'Transferencia Bancaria',
        'fields': ['account_number', 'bank_name', 'account_holder', 'cbu_cvu']
    },
    'international_transfer': {
        'name': 'Transferencia Internacional',
        'fields': ['account_number', 'bank_name', 'account_holder', 'swift_code', 'routing_number']
    },
    'bitcoin': {
        'name': 'Bitcoin',
        'fields': ['wallet_address', 'network', 'amount']
    },
    'efectivo': {
        'name': 'Efectivo',
        'fields': ['amount', 'description']
    }
}


class MedioDePago(models.Model):
    """
    Representa un medio de pago, como tarjeta de crÃ©dito, transferencia, etc.
    """
    nombre = models.CharField('Nombre del medio', max_length=100, unique=True)
    template_usado = models.CharField(
        'Template utilizado', 
        max_length=50, 
        choices=[(k, v['name']) for k, v in PAYMENT_TEMPLATES.items()],
        blank=True,
        help_text='Template predefinido usado como base'
    )
    comision_porcentaje = models.DecimalField(
        'ComisiÃ³n (%)',
        max_digits=6,
        decimal_places=3,
        default=0,
        help_text='Porcentaje de comisiÃ³n del 0 al 100'
    )
    is_active = models.BooleanField('Activo', default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Medio de Pago'
        verbose_name_plural = 'Medios de Pago'
        ordering = ['nombre']

    def clean(self):
        if self.comision_porcentaje < 0 or self.comision_porcentaje > 100:
            raise ValidationError({
                'comision_porcentaje': 'La comisiÃ³n debe estar entre 0 y 100.'
            })

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip() if self.nombre else ''
        if not self.nombre:
            raise ValidationError('El nombre del medio de pago no puede estar vacÃ­o.')
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        estado = 'Activo' if self.is_active else 'Inactivo'
        return f'{self.nombre} - {estado}'
        
    def toggle_active(self):
        """Cambiar estado activo/inactivo"""
        self.is_active = not self.is_active
        self.save(update_fields=['is_active'])
        return self.is_active

    @property
    def can_be_edited_freely(self):
        """Determina si el medio puede editarse libremente"""
        return True

    @property
    def total_campos_activos(self):
        """Cuenta los campos asociados al medio de pago"""
        return self.campos.count()

    def aplicar_template(self, template_key):
        """
        Aplica un template predefinido al medio de pago,
        creando automÃ¡ticamente los campos necesarios.
        """
        if template_key not in PAYMENT_TEMPLATES:
            raise ValueError(f"Template '{template_key}' no existe")
        
        template = PAYMENT_TEMPLATES[template_key]
        self.template_usado = template_key
        self.save()
        
        # Crear campos del template
        for field_key in template['fields']:
            if field_key in PREDEFINED_FIELDS:
                field_def = PREDEFINED_FIELDS[field_key]
                CampoMedioDePago.objects.get_or_create(
                    medio_de_pago=self,
                    campo_api=field_key,
                    defaults={
                        'nombre_campo': field_def['label'],
                        'tipo_dato': field_def['type'],
                        'is_required': field_def['required'],
                        'descripcion': field_def['description']
                    }
                )


class CampoMedioDePago(models.Model):
    """
    Representa un campo predefinido asociado a un MedioDePago.
    """
    TIPO_DATO_CHOICES = [
        ('TEXTO', 'Texto'),
        ('NUMERO', 'NÃºmero'),
        ('FECHA', 'Fecha'),
        ('EMAIL', 'Email'),
        ('TELEFONO', 'TelÃ©fono'),
        ('URL', 'URL'),
    ]

    medio_de_pago = models.ForeignKey(
        MedioDePago,
        related_name='campos',
        on_delete=models.CASCADE,
        verbose_name='Medio de Pago'
    )
    # Campo que ve el usuario (espaÃ±ol)
    nombre_campo = models.CharField('Nombre del campo', max_length=100)
    # Campo para la API (inglÃ©s, estandarizado)
    campo_api = models.CharField(
        'Campo API', 
        max_length=100,
        choices=[(k, v['label']) for k, v in PREDEFINED_FIELDS.items()],
        help_text='Campo estandarizado para la API'
    )
    tipo_dato = models.CharField(
        'Tipo de Dato',
        max_length=10,
        choices=TIPO_DATO_CHOICES
    )
    is_required = models.BooleanField('Requerido', default=True)
    descripcion = models.TextField('DescripciÃ³n', blank=True, help_text='Ayuda para el usuario')
    orden = models.PositiveIntegerField('Orden', default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Campo de Medio de Pago'
        verbose_name_plural = 'Campos de Medios de Pago'
        unique_together = ('medio_de_pago', 'campo_api')  # Evitar duplicados por API
        ordering = ['orden', 'id']

    def clean(self):
        # Si campo_api estÃ¡ definido, auto-completar antes de validar
        if self.campo_api in PREDEFINED_FIELDS:
            field_def = PREDEFINED_FIELDS[self.campo_api]
            self.nombre_campo = field_def['label']
            self.tipo_dato = field_def['type']
            if not self.descripcion:
                self.descripcion = field_def['description']
        
        # Validar despuÃ©s del auto-completado
        if not self.nombre_campo or not self.nombre_campo.strip():
            raise ValidationError({
                'campo_api': 'Error en la configuraciÃ³n del campo seleccionado.'
            })
        
        if not self.campo_api:
            raise ValidationError({
                'campo_api': 'Debe seleccionar un campo de API.'
            })

    def save(self, *args, **kwargs):
        # Auto-completar desde la definiciÃ³n predefinida si existe
        if self.campo_api in PREDEFINED_FIELDS:
            field_def = PREDEFINED_FIELDS[self.campo_api]
            # Siempre auto-completar desde la definiciÃ³n
            self.nombre_campo = field_def['label']
            self.tipo_dato = field_def['type']
            if not self.descripcion:
                self.descripcion = field_def['description']
        
        # Validar que tenemos nombre_campo despuÃ©s del auto-completado
        if not self.nombre_campo:
            raise ValidationError('Error: No se pudo determinar el nombre del campo.')
        
        # Limpiar el nombre
        self.nombre_campo = self.nombre_campo.strip()
        
        # Llamar a full_clean solo si tenemos datos vÃ¡lidos
        if self.nombre_campo and self.tipo_dato:
            self.full_clean()
        
        super().save(*args, **kwargs)

    def __str__(self):
        requerido = ' (Requerido)' if self.is_required else ''
        return f'{self.nombre_campo} ({self.get_tipo_dato_display()}){requerido} - {self.medio_de_pago.nombre}'

    def get_api_field_info(self):
        """Retorna informaciÃ³n completa del campo API"""
        if self.campo_api in PREDEFINED_FIELDS:
            return PREDEFINED_FIELDS[self.campo_api]
        return None


# Manager personalizado para filtrar por activos
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

# Agregar manager de activos solo a MedioDePago
MedioDePago.add_to_class('active_objects', ActiveManager())