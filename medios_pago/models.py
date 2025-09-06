# models.py - Versión corregida para soft delete
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class MedioDePago(models.Model):
    """
    Representa un medio de pago, como tarjeta de crédito, transferencia, etc.

    Los medios de pago pueden tener una comisión asociada y pueden ser
    desactivados. Utiliza un sistema de "soft delete" para
    mantener un registro histórico.

    :ivar nombre: Nombre único del medio de pago.
    :ivar comision_porcentaje: Porcentaje de comisión a aplicar.
    :ivar is_active: Booleano que indica si el medio de pago está activo.
    :ivar deleted_at: Fecha y hora en que el medio de pago fue "eliminado" (soft delete).
    :ivar creado: Fecha de creación del registro.
    :ivar actualizado: Fecha de la última actualización del registro.
    """
    nombre = models.CharField('Nombre del medio', max_length=100, unique=True)
    comision_porcentaje = models.DecimalField(
        'Comisión (%)',
        max_digits=6,  # Aumentado para soportar hasta 100.000
        decimal_places=3,  # 3 decimales para precisión
        default=0,
        help_text='Porcentaje de comisión del 0 al 100'
    )
    is_active = models.BooleanField('Activo', default=False)
    deleted_at = models.DateTimeField('Eliminado en', null=True, blank=True)
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
        estado = 'Activo' if self.is_active else 'Deshabilitado'
        return f'{self.nombre} - {estado}'
        
    def toggle_active(self):
        """Cambiar estado activo/inactivo"""
        if self.is_deleted:
            raise ValidationError('No se puede cambiar el estado de un medio eliminado.')
        self.is_active = not self.is_active
        self.save(update_fields=['is_active'])
        return self.is_active

    def soft_delete(self):
        """Eliminación suave del medio de pago"""
        if self.is_deleted:
            raise ValidationError('El medio ya está eliminado.')
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['deleted_at', 'is_active'])

    def restore(self):
        """Restaurar medio de pago eliminado"""
        if not self.is_deleted:
            raise ValidationError('No se puede restaurar un medio que no está eliminado.')
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=['deleted_at', 'is_active'])

    @property
    def is_deleted(self):
        """
        Indica si el medio de pago está eliminado.
        """
        return self.deleted_at is not None

    @property
    def can_be_edited_freely(self):
        """Determina si el medio puede editarse libremente"""
        return True

    @property
    def total_campos_activos(self):
        return self.campos.filter(deleted_at__isnull=True).count()


class CampoMedioDePago(models.Model):
    """
    Representa un campo dinámico asociado a un MedioDePago.

    Estos campos adicionales permiten a los usuarios ingresar información
    específica para cada medio de pago (ej. CBU para transferencia).

    :ivar medio_de_pago: Medio de pago al que pertenece el campo.
    :ivar nombre_campo: Nombre del campo.
    :ivar tipo_dato: Tipo de dato del campo (ej. texto, número, fecha).
    :ivar is_required: Booleano que indica si el campo es obligatorio.
    :ivar deleted_at: Fecha de eliminación suave.
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
    deleted_at = models.DateTimeField('Eliminado en', null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Campo de Medio de Pago'
        verbose_name_plural = 'Campos de Medios de Pago'
        # QUITAR unique_together para evitar conflictos con soft delete
        # unique_together = ('medio_de_pago', 'nombre_campo')  # ← Comentar esta línea
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

        # Validación personalizada de unicidad que excluye eliminados
        # Solo validar si el medio_de_pago ya está guardado (tiene pk)
        if self.nombre_campo and self.medio_de_pago and self.medio_de_pago.pk:
            existing = CampoMedioDePago.objects.filter(
                medio_de_pago=self.medio_de_pago,
                nombre_campo__iexact=self.nombre_campo.strip(),
                deleted_at__isnull=True  # Solo considerar campos NO eliminados
            )
            
            # Excluir el objeto actual si está siendo editado
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError({
                    'nombre_campo': f'Ya existe un campo con el nombre "{self.nombre_campo}" en este medio de pago.'
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

    def soft_delete(self):
        """Eliminación suave del campo"""
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restaurar campo eliminado"""
        self.deleted_at = None
        self.save()

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def __str__(self):
        requerido = ' (Requerido)' if self.is_required else ''
        deleted = ' [ELIMINADO]' if self.is_deleted else ''
        return f'{self.nombre_campo} ({self.get_tipo_dato_display()}){requerido} - {self.medio_de_pago.nombre}{deleted}'


# Managers personalizados
class ActiveManager(models.Manager):
    """
    Manager personalizado para filtrar objetos que no han sido eliminados.
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


# Agregar managers a los modelos
MedioDePago.add_to_class('objects', models.Manager())
MedioDePago.add_to_class('active', ActiveManager())

CampoMedioDePago.add_to_class('objects', models.Manager())
CampoMedioDePago.add_to_class('active', ActiveManager())