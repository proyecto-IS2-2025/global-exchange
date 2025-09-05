from django.db import models
from django.db.models import functions
from django.core.exceptions import ValidationError


class MedioDePago(models.Model):
    nombre = models.CharField('Nombre del medio', max_length=100, unique=True)
    comision_porcentaje = models.DecimalField(
        'Comisión (%)',
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Porcentaje de comisión del 0 al 100'
    )
    is_active = models.BooleanField('Activo', default=False)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Medio de Pago'
        verbose_name_plural = 'Medios de Pago'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['nombre']),
        ]

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

    def __str__(self):
        estado = 'Activo' if self.is_active else 'Deshabilitado'
        return f'{self.nombre} - {estado}'

    @property
    def total_campos(self):
        return self.campos.count()
    
    @property
    def campos_requeridos(self):
        return self.campos.filter(is_required=True).count()


class CampoMedioDePago(models.Model):
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
    nombre_campo = models.CharField('Nombre del campo', max_length=100)
    tipo_dato = models.CharField(
        'Tipo de Dato',
        max_length=10,
        choices=TIPO_DATO_CHOICES
    )
    is_required = models.BooleanField('Requerido', default=True)
    orden = models.PositiveIntegerField('Orden', default=0)

    class Meta:
        verbose_name = 'Campo de Medio de Pago'
        verbose_name_plural = 'Campos de Medios de Pago'
        unique_together = ('medio_de_pago', 'nombre_campo')
        ordering = ['orden', 'id']

    def clean(self):
        if not self.nombre_campo or not self.nombre_campo.strip():
            raise ValidationError({
                'nombre_campo': 'El nombre del campo no puede estar vacío.'
            })
        
        if not self.tipo_dato:
            raise ValidationError({
                'tipo_dato': 'Debe seleccionar un tipo de dato.'
            })

    def save(self, *args, **kwargs):
        self.nombre_campo = self.nombre_campo.strip() if self.nombre_campo else ''
        if not self.nombre_campo:
            raise ValidationError('El nombre del campo no puede estar vacío.')
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        requerido = ' (Requerido)' if self.is_required else ''
        return f'{self.nombre_campo} ({self.get_tipo_dato_display()}){requerido} - {self.medio_de_pago.nombre}'