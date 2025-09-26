# models.py - Versión actualizada con billetera electrónica
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
import json
from django.conf import settings

# Tipos de medios de pago - Mapeo técnico a etiquetas de usuario
TIPO_MEDIO_CHOICES = [
    ('stripe', 'Tarjeta de Crédito/Débito'),
    ('paypal', 'PayPal'),
    ('bank_local', 'Transferencia Bancaria Local'),
    ('bank_international', 'Transferencia Bancaria Internacional'),
    ('bitcoin', 'Criptomonedas (Bitcoin, Ethereum)'),
    ('billetera_electronica', 'Billetera Electrónica'),
    ('efectivo', 'Pago en Efectivo'),
]

# Mapeo de tipos de medios a procesadores de API
API_MAPPING = {
    'stripe': 'StripeProcessor',
    'paypal': 'PayPalProcessor', 
    'bank_local': 'BankLocalProcessor',
    'bank_international': 'BankInternationalProcessor',
    'bitcoin': 'BitcoinProcessor',
    'billetera_electronica': 'EWalletProcessor',
    'efectivo': 'CashProcessor'
}

# Definición de campos predefinidos por tipo de API
PREDEFINED_FIELDS = {
    # Campos comunes para tarjetas de crédito/débito
    'card_number': {
        'label': 'Número de tarjeta',
        'type': 'NUMERO',
        'required': True,
        'description': 'Número de 16 dígitos de la tarjeta'
    },
    'exp_month': {
        'label': 'Mes de vencimiento',
        'type': 'NUMERO',
        'required': True,
        'description': 'Mes de vencimiento (1-12)'
    },
    'exp_year': {
        'label': 'Año de vencimiento', 
        'type': 'NUMERO',
        'required': True,
        'description': 'Año de vencimiento (4 dígitos)'
    },
    'cvc': {
        'label': 'Código de seguridad',
        'type': 'NUMERO',
        'required': True,
        'description': 'Código CVV/CVC de 3 o 4 dígitos'
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
        'description': 'Dirección de email asociada a PayPal'
    },
    
    # Campos bancarios
    'account_number': {
        'label': 'Número de cuenta',
        'type': 'NUMERO',
        'required': True,
        'description': 'Número de cuenta bancaria'
    },
    'bank_name': {  # <-- CAMBIO: era 'entidad'
        'label': 'Entidad',
        'type': 'TEXTO',
        'required': True,
        'description': 'Nombre de la entidad financiera (banco, billetera, etc.)'
    },
    'account_holder': {
        'label': 'Titular de la cuenta',
        'type': 'TEXTO',
        'required': True,
        'description': 'Nombre del titular de la cuenta'
    },
    'routing_number': {
        'label': 'Código de routing',
        'type': 'NUMERO',
        'required': False,
        'description': 'Código de routing bancario (USA)'
    },
    'swift_code': {
        'label': 'Código SWIFT',
        'type': 'TEXTO',
        'required': False,
        'description': 'Código SWIFT para transferencias internacionales'
    },
    'cbu_cvu': {
        'label': 'CBU/CVU',
        'type': 'NUMERO',
        'required': True,
        'description': 'Clave Bancaria Uniforme o Clave Virtual Uniforme'
    },
    'ruc': {
        'label': 'RUC',
        'type': 'NUMERO',
        'required': False,
        'description': 'Registro Único del Contribuyente'
    },
    
    # Campos generales
    'email': {
        'label': 'Email',
        'type': 'EMAIL',
        'required': True,
        'description': 'Dirección de correo electrónico'
    },
    'phone': {
        'label': 'Teléfono',
        'type': 'TELEFONO',
        'required': False,
        'description': 'Número de teléfono'
    },
    'description': {
        'label': 'Descripción',
        'type': 'TEXTO',
        'required': False,
        'description': 'Descripción del medio de pago'
    },
    # Campos para criptomonedas
    'wallet_address': {
        'label': 'Dirección de billetera',
        'type': 'TEXTO',
        'required': True,
        'description': 'Dirección de billetera de criptomoneda'
    },
    'network': {
        'label': 'Red',
        'type': 'TEXTO',
        'required': True,
        'description': 'Red blockchain (ETH, BTC, etc.)'
    },
    # Campos específicos para billeteras electrónicas
    'wallet_phone': {
        'label': 'Teléfono de billetera',
        'type': 'TELEFONO',
        'required': True,
        'description': 'Número de teléfono asociado a la billetera'
    },
    'wallet_email': {
        'label': 'Email de billetera',
        'type': 'EMAIL',
        'required': False,
        'description': 'Email asociado a la billetera electrónica'
    },
    'wallet_user_id': {
        'label': 'ID de usuario',
        'type': 'TEXTO',
        'required': False,
        'description': 'Identificador de usuario en la billetera'
    },
    'document_number': {
        'label': 'Número de documento',
        'type': 'NUMERO',
        'required': False,
        'description': 'Número de cédula o documento de identidad'
    },
}

# Templates predefinidos para tipos comunes de medios de pago
PAYMENT_TEMPLATES = {
    'stripe_card': {
        'name': 'Tarjeta de Crédito/Débito (Stripe)',
        'tipo_medio': 'stripe',
        'fields': ['card_number', 'exp_month', 'exp_year', 'cvc', 'cardholder_name', 'email'],
        'is_custom': False
    },
    'paypal_standard': {
        'name': 'PayPal Estándar',
        'tipo_medio': 'paypal',
        'fields': ['paypal_email', 'description'],
        'is_custom': False
    },
    'bank_local_ar': {
        'name': 'Transferencia Bancaria local',
        'tipo_medio': 'bank_local',
        'fields': ['account_number', 'bank_name', 'account_holder', 'cbu_cvu', 'ruc'],  # <-- bank_name
        'is_custom': False
    },
    'bank_international': {
        'name': 'Transferencia Bancaria Internacional',
        'tipo_medio': 'bank_international',
        'fields': ['account_number', 'bank_name', 'account_holder', 'swift_code', 'routing_number'],  # <-- bank_name
        'is_custom': False
    },
    'bitcoin_wallet': {
        'name': 'Billetera Bitcoin',
        'tipo_medio': 'bitcoin',
        'fields': ['wallet_address', 'network'],
        'is_custom': False
    },
    'billetera_electronica_py': {
        'name': 'Billetera Electrónica Paraguay',
        'tipo_medio': 'billetera_electronica',
        'fields': ['wallet_phone', 'bank_name', 'account_holder', 'document_number', 'wallet_email'],  # <-- bank_name
        'is_custom': False
    },
    'efectivo_simple': {
        'name': 'Pago en Efectivo',
        'tipo_medio': 'efectivo',
        'fields': ['description'],
        'is_custom': False
    }
}


class PaymentTemplate(models.Model):
    """
    Modelo para templates de medios de pago creados dinámicamente por el admin
    """
    name = models.CharField('Nombre del template', max_length=100, unique=True)
    description = models.TextField('Descripción', blank=True)
    fields_config = models.JSONField('Configuración de campos', default=list)
    is_active = models.BooleanField('Activo', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        verbose_name='Creado por',
        null=True, blank=True
    )
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Template de Pago'
        verbose_name_plural = 'Templates de Pago'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_fields_list(self):
        """Retorna la lista de campos API del template"""
        return [field['campo_api'] for field in self.fields_config if field.get('campo_api')]

    def to_payment_template_format(self):
        """Convierte el template a formato compatible con PAYMENT_TEMPLATES"""
        return {
            'name': self.name,
            'fields': self.get_fields_list(),
            'is_custom': True,
            'template_id': self.pk
        }

    @classmethod
    def get_all_templates(cls):
        """
        Retorna todos los templates (predefinidos + dinámicos) en formato unificado
        """
        templates = {}
        
        # Agregar templates predefinidos
        templates.update(PAYMENT_TEMPLATES)
        
        # Agregar templates dinámicos
        for template in cls.objects.filter(is_active=True):
            key = f'custom_{template.pk}'
            templates[key] = template.to_payment_template_format()
        
        return templates

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)


class MedioDePago(models.Model):
    """
    Representa un medio de pago, como tarjeta de crédito, transferencia, etc.
    """
    nombre = models.CharField('Nombre del medio', max_length=100, unique=True)
    template_usado = models.CharField(
        'Template utilizado', 
        max_length=50, 
        blank=True,
        help_text='Template predefinido o personalizado usado como base'
    )

    tipo_medio = models.CharField(
        'Tipo de Medio de Pago',
        max_length=50,
        choices=TIPO_MEDIO_CHOICES,
        blank=True,
        null=True,
        help_text='Tipo de procesador que manejará este medio de pago'
    )

    custom_template = models.ForeignKey(
        PaymentTemplate,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Template personalizado',
        help_text='Template personalizado usado'
    )
    comision_porcentaje = models.DecimalField(
        'Comisión (%)',
        max_digits=6,
        decimal_places=3,
        default=0,
        help_text='Porcentaje de comisión del 0 al 100'
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
                'comision_porcentaje': 'La comisión debe estar entre 0 y 100.'
            })

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip() if self.nombre else ''
        if not self.nombre:
            raise ValidationError('El nombre del medio de pago no puede estar vacío.')
        self.full_clean()
        super().save(*args, **kwargs)

    def get_processor_class(self):
        """Retorna la clase de procesador para este medio de pago"""
        if not self.tipo_medio:
            return self._infer_processor_from_fields()
        return API_MAPPING.get(self.tipo_medio)
    
    def _infer_processor_from_fields(self):
        """Inferir procesador basado en campos cuando no hay tipo_medio definido"""
        campos = list(self.campos.values_list('campo_api', flat=True))
        
        if 'card_number' in campos and 'cvc' in campos:
            return 'StripeProcessor'
        elif 'paypal_email' in campos:
            return 'PayPalProcessor'
        elif 'swift_code' in campos:
            return 'BankInternationalProcessor'
        elif 'wallet_phone' in campos or 'wallet_user_id' in campos:
            return 'EWalletProcessor'
        elif 'account_number' in campos:
            return 'BankLocalProcessor'
        elif 'wallet_address' in campos:
            return 'BitcoinProcessor'
        else:
            return 'CashProcessor'

    def get_api_info(self):
        """Retorna información del tipo de API"""
        tipo_efectivo = self.tipo_medio or self._infer_tipo_from_fields()
        
        return {
            'tipo_interno': tipo_efectivo,
            'nombre_usuario': dict(TIPO_MEDIO_CHOICES).get(tipo_efectivo, 'No definido'),
            'procesador': self.get_processor_class(),
            'es_inferido': not bool(self.tipo_medio)
        }

    def _infer_tipo_from_fields(self):
        """Inferir tipo basado en campos cuando no hay tipo_medio definido"""
        campos = list(self.campos.values_list('campo_api', flat=True))
        
        if 'card_number' in campos and 'cvc' in campos:
            return 'stripe'
        elif 'paypal_email' in campos:
            return 'paypal'
        elif 'swift_code' in campos:
            return 'bank_international'
        elif 'wallet_phone' in campos or 'wallet_user_id' in campos:
            return 'billetera_electronica'
        elif 'account_number' in campos:
            return 'bank_local'
        elif 'wallet_address' in campos:
            return 'bitcoin'
        else:
            return 'efectivo'

    def validate_required_fields(self):
        """Valida que el medio tenga los campos requeridos según su tipo"""
        if not self.tipo_medio:
            return False, "Tipo de medio de pago no definido"
        
        required_fields = self.get_required_fields_for_type()
        missing_fields = []
        
        for field_key in required_fields:
            if not self.campos.filter(campo_api=field_key, is_required=True).exists():
                missing_fields.append(field_key)
        
        if missing_fields:
            return False, f"Campos requeridos faltantes: {', '.join(missing_fields)}"
        
        return True, "Validación exitosa"

    def get_required_fields_for_type(self):
        """Retorna los campos requeridos según el tipo de medio"""
        required_by_type = {
            'stripe': ['card_number', 'exp_month', 'exp_year', 'cvc'],
            'paypal': ['paypal_email'],
            'bank_local': ['account_number', 'bank_name', 'account_holder'],
            'bank_international': ['account_number', 'bank_name', 'account_holder', 'swift_code'],
            'bitcoin': ['wallet_address', 'network'],
            'billetera_electronica': ['wallet_phone', 'bank_name'],
            'efectivo': []
        }
        return required_by_type.get(self.tipo_medio, [])

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

    def create_template_from_current_fields(self, template_name, created_by=None):
        """
        Crea un template basado en los campos actuales del medio de pago
        """
        fields_config = []
        for campo in self.campos.all().order_by('orden', 'id'):
            fields_config.append({
                'campo_api': campo.campo_api,
                'is_required': campo.is_required
            })
        
        template = PaymentTemplate.objects.create(
            name=template_name,
            description=f'Template creado desde el medio de pago "{self.nombre}"',
            fields_config=fields_config,
            created_by=created_by
        )
        
        return template

    def aplicar_template(self, template_key):
        """
        Aplica un template predefinido o personalizado al medio de pago,
        creando automáticamente los campos necesarios y estableciendo el tipo_medio.
        """
        all_templates = PaymentTemplate.get_all_templates()
        
        if template_key not in all_templates:
            raise ValueError(f"Template '{template_key}' no existe")
        
        template = all_templates[template_key]
        
        # Establecer tipo_medio si el template lo define
        if template.get('tipo_medio'):
            self.tipo_medio = template['tipo_medio']
        
        # Guardar referencia del template usado
        if template.get('is_custom'):
            self.custom_template_id = template.get('template_id')
            self.template_usado = ''
        else:
            self.template_usado = template_key
            self.custom_template = None
        
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
        ('NUMERO', 'Número'),
        ('FECHA', 'Fecha'),
        ('EMAIL', 'Email'),
        ('TELEFONO', 'Teléfono'),
        ('URL', 'URL'),
    ]

    medio_de_pago = models.ForeignKey(
        MedioDePago,
        related_name='campos',
        on_delete=models.CASCADE,
        verbose_name='Medio de Pago'
    )
    # Campo que ve el usuario (español)
    nombre_campo = models.CharField('Nombre del campo', max_length=100)
    # Campo para la API (inglés, estandarizado)
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
    descripcion = models.TextField('Descripción', blank=True, help_text='Ayuda para el usuario')
    orden = models.PositiveIntegerField('Orden', default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Campo de Medio de Pago'
        verbose_name_plural = 'Campos de Medios de Pago'
        unique_together = ('medio_de_pago', 'campo_api')
        ordering = ['orden', 'id']

    def clean(self):
        if self.campo_api in PREDEFINED_FIELDS:
            field_def = PREDEFINED_FIELDS[self.campo_api]
            self.nombre_campo = field_def['label']
            self.tipo_dato = field_def['type']
            if not self.descripcion:
                self.descripcion = field_def['description']
        
        if not self.nombre_campo or not self.nombre_campo.strip():
            raise ValidationError({
                'campo_api': 'Error en la configuración del campo seleccionado.'
            })
        
        if not self.campo_api:
            raise ValidationError({
                'campo_api': 'Debe seleccionar un campo de API.'
            })

    def save(self, *args, **kwargs):
        if self.campo_api in PREDEFINED_FIELDS:
            field_def = PREDEFINED_FIELDS[self.campo_api]
            self.nombre_campo = field_def['label']
            self.tipo_dato = field_def['type']
            if not self.descripcion:
                self.descripcion = field_def['description']
        
        if not self.nombre_campo:
            raise ValidationError('Error: No se pudo determinar el nombre del campo.')
        
        self.nombre_campo = self.nombre_campo.strip()
        
        if self.nombre_campo and self.tipo_dato:
            self.full_clean()
        
        super().save(*args, **kwargs)

    def __str__(self):
        requerido = ' (Requerido)' if self.is_required else ''
        return f'{self.nombre_campo} ({self.get_tipo_dato_display()}){requerido} - {self.medio_de_pago.nombre}'

    def get_api_field_info(self):
        """Retorna información completa del campo API"""
        if self.campo_api in PREDEFINED_FIELDS:
            return PREDEFINED_FIELDS[self.campo_api]
        return None


# Manager personalizado para filtrar por activos
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

# Agregar manager de activos solo a MedioDePago
MedioDePago.add_to_class('active_objects', ActiveManager())