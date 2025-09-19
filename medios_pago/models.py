# models.py - Versión simplificada sin soft delete
from django.db import models
from django.core.exceptions import ValidationError


class MedioDePago(models.Model):
    """
    Representa un medio de pago, como tarjeta de crédito, transferencia, etc.

    Los medios de pago pueden tener una comisión asociada y pueden ser
    activados/desactivados mediante el campo is_active.

    :ivar nombre: Nombre único del medio de pago.
    :ivar comision_porcentaje: Porcentaje de comisión a aplicar.
    :ivar is_active: Booleano que indica si el medio de pago está activo.
    :ivar creado: Fecha de creación del registro.
    :ivar actualizado: Fecha de la última actualización del registro.
    """
    nombre = models.CharField('Nombre del medio', max_length=100, unique=True)
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
        """
        Valida que el porcentaje de comisión esté en el rango correcto.
        """
        if self.comision_porcentaje < 0 or self.comision_porcentaje > 100:
            raise ValidationError({
                'comision_porcentaje': 'La comisión debe estar entre 0 y 100.'
            })

    def save(self, *args, **kwargs):
        """
        Override del método save para realizar la validación del modelo.
        """
        self.nombre = self.nombre.strip() if self.nombre else ''
        if not self.nombre:
            raise ValidationError('El nombre del medio de pago no puede estar vacío.')
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


class CampoMedioDePago(models.Model):
    """
    Representa un campo dinámico asociado a un MedioDePago.

    Estos campos adicionales permiten a los usuarios ingresar información
    específica para cada medio de pago (ej. CBU para transferencia).

    :ivar medio_de_pago: Medio de pago al que pertenece el campo.
    :ivar nombre_campo: Nombre del campo.
    :ivar tipo_dato: Tipo de dato del campo (ej. texto, número, fecha).
    :ivar is_required: Booleano que indica si el campo es obligatorio.
    :ivar creado: Fecha de creación del registro.
    :ivar actualizado: Fecha de la última actualización del registro.
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
    nombre_campo = models.CharField('Nombre del campo', max_length=100)
    tipo_dato = models.CharField(
        'Tipo de Dato',
        max_length=10,
        choices=TIPO_DATO_CHOICES
    )
    is_required = models.BooleanField('Requerido', default=True)
    orden = models.PositiveIntegerField('Orden', default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Campo de Medio de Pago'
        verbose_name_plural = 'Campos de Medios de Pago'
        unique_together = ('medio_de_pago', 'nombre_campo')  # Restaurar unique_together
        ordering = ['orden', 'id']

    def clean(self):
        """
        Valida que el nombre del campo no esté duplicado dentro del mismo medio de pago.
        """
        if not self.nombre_campo or not self.nombre_campo.strip():
            raise ValidationError({
                'nombre_campo': 'El nombre del campo no puede estar vacío.'
            })
        
        if not self.tipo_dato:
            raise ValidationError({
                'tipo_dato': 'Debe seleccionar un tipo de dato.'
            })

    def save(self, *args, **kwargs):
        """
        Override del método save para limpiar el nombre del campo y ejecutar la validación.
        """
        self.nombre_campo = self.nombre_campo.strip() if self.nombre_campo else ''
        if not self.nombre_campo:
            raise ValidationError('El nombre del campo no puede estar vacío.')
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        requerido = ' (Requerido)' if self.is_required else ''
        return f'{self.nombre_campo} ({self.get_tipo_dato_display()}){requerido} - {self.medio_de_pago.nombre}'


# Manager personalizado para filtrar por activos
class ActiveManager(models.Manager):
    """
    Manager personalizado para filtrar objetos activos.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


# Agregar manager de activos solo a MedioDePago
MedioDePago.add_to_class('active_objects', ActiveManager())