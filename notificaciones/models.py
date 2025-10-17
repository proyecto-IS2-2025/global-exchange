"""
Módulo de notificaciones de tasas de cambio.

Este módulo gestiona el sistema de notificaciones personalizadas para alertas
de cambios en las tasas de divisas. Permite a los usuarios configurar reglas
de alerta basadas en diferentes criterios y recibir notificaciones cuando
se cumplan las condiciones especificadas.

Modelos principales:
    - ConfiguracionGeneral: Preferencias globales de notificaciones del usuario
    - NotificacionTasa: Reglas de alerta personalizadas
    - Notificacion: Instancias de notificaciones enviadas al usuario
"""

from django.core.exceptions import ValidationError
from django.db import models
from users.models import CustomUser
from django.core.validators import MinValueValidator
from clientes.models import Cliente

# Constantes de opciones para campos de elección

CANAL_CHOICES = [
    ('sistema', 'Solo por el Sistema'),
    ('sistema_correo', 'Sistema y Correo Electrónico'),
]
"""Canales disponibles para recibir notificaciones."""

TIPO_ALERTA_CHOICES = [
    ('general', 'Cambio General'),
    ('umbral', 'Alcanzar Umbral'),
    ('transaccion_cancelada', 'Transacción Cancelada'),
]
"""Tipos de alertas disponibles para notificaciones de tasas."""

OPERACION_CHOICES = [
    ('compra', 'Compra'),
    ('venta', 'Venta'),
    ('ambos', 'Compra y Venta'),
]
"""Tipos de operaciones que pueden generar alertas."""

UMBRAL_CONDICION_CHOICES = [
    ('mayor', 'Mayor o igual que'),
    ('menor', 'Menor o igual que'),
]
"""Condiciones de comparación para alertas de umbral."""

ESTADO_LECTURA_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('leida', 'Leída'),
]
"""Estados de lectura para notificaciones individuales."""


class ConfiguracionGeneral(models.Model):
    """
    Configuración global de notificaciones para un usuario.

    Almacena las preferencias generales del usuario respecto a cómo y cuándo
    desea recibir notificaciones del sistema. Cada usuario tiene una única
    configuración general.

    :param usuario: Usuario propietario de esta configuración (relación uno a uno)
    :type usuario: CustomUser
    :param habilitar_notificaciones: Si el usuario desea recibir notificaciones
    :type habilitar_notificaciones: bool
    :param canal_notificacion: Canal preferido para recibir notificaciones
    :type canal_notificacion: str
    """
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    habilitar_notificaciones = models.BooleanField(default=True)
    canal_notificacion = models.CharField(max_length=20, choices=CANAL_CHOICES, default='sistema')

    def __str__(self):
        """
        Representación en cadena de la configuración.

        :return: Cadena descriptiva con el nombre de usuario
        :rtype: str
        """
        return f"Configuración de {self.usuario.username}"


class NotificacionTasa(models.Model):
    """
    Regla de notificación personalizada para alertas de tasas de cambio.

    Permite a los usuarios configurar alertas automáticas basadas en cambios
    generales de tasas o cuando se alcancen umbrales específicos. Cada regla
    está asociada a un usuario, cliente y divisa específicos.

    :param usuario: Usuario que creó y es propietario de la regla.
    :type usuario: CustomUser
    :param cliente_asociado: Cliente al que se aplica esta regla.
    :type cliente_asociado: Cliente
    :param divisa: Código de la divisa a monitorear (ej: 'USD', 'EUR').
    :type divisa: str
    :param activa: Si la regla está activa o pausada.
    :type activa: bool
    :param tipo_alerta: Tipo de alerta ('general', 'umbral', 'transaccion_cancelada').
    :type tipo_alerta: str
    :param tipo_operacion: Operación a monitorear ('compra', 'venta', 'ambos').
    :type tipo_operacion: str
    :param condicion_umbral: Condición de comparación ('mayor', 'menor').
    :type condicion_umbral: str, opcional
    :param monto_umbral: Valor umbral en guaraníes.
    :type monto_umbral: Decimal, opcional
    """
    
    # Usuario propietario de la regla de notificación
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Usuario Creador")

    # NUEVA RELACIÓN: EL CONTEXTO (el Cliente asociado y su Segmento)
    cliente_asociado = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        verbose_name="Cliente Asociado"
    )

    # Divisa a monitorear
    divisa = models.CharField(max_length=5)

    # Estado y configuración de la alerta
    activa = models.BooleanField(default=True)
    tipo_alerta = models.CharField(max_length=25, choices=TIPO_ALERTA_CHOICES)
    tipo_operacion = models.CharField(max_length=10, choices=OPERACION_CHOICES)

    # Campos específicos para alertas de umbral
    condicion_umbral = models.CharField(max_length=10, choices=UMBRAL_CONDICION_CHOICES, blank=True, null=True)
    monto_umbral = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0)]
    )

    @property
    def segmento(self):
        """
        Acceso directo al segmento del cliente asociado.

        :return: Segmento del cliente asociado a esta regla.
        :rtype: clientes.Segmento
        """
        return self.cliente_asociado.segmento

    @property
    def operacion_display(self):
        """
        Obtiene la representación legible del tipo de operación.

        :return: Texto descriptivo ('Compra', 'Venta', 'Compra y Venta').
        :rtype: str
        """
        return self.get_tipo_operacion_display()

    class Meta:
        verbose_name = "Notificación de Tasa"
        verbose_name_plural = "Notificaciones de Tasa"

    def __str__(self):
        """
        Representación en cadena de la regla de notificación.

        :return: Cadena con divisa, cliente y tipo de alerta
        :rtype: str
        """
        return f"Alerta de {self.divisa} para {self.cliente_asociado.nombre_completo} ({self.get_tipo_alerta_display()})"
    
    def clean(self):
        """
        Validación personalizada del modelo.

        Verifica que:
        - Las alertas de umbral no tengan tipo_operacion='ambos'.
        - Las alertas de umbral tengan condicion_umbral y monto_umbral definidos.

        .. note::
           La validación de duplicados se realiza en la vista para evitar
           problemas con campos no asignados durante la validación del formulario.

        :raises ValidationError: Si las validaciones fallan.
        """
        super().clean()
        errors = {}
        
        # Validar que umbral no tenga 'ambos'
        if self.tipo_alerta == 'umbral' and self.tipo_operacion == 'ambos':
            errors['tipo_operacion'] = 'Para notificaciones de umbral debe seleccionar Compra o Venta, no ambos.'
        
        # Validar campos requeridos para umbral
        if self.tipo_alerta == 'umbral':
            if not self.condicion_umbral:
                errors['condicion_umbral'] = 'La condición de umbral es requerida.'
            if not self.monto_umbral:
                errors['monto_umbral'] = 'El monto de umbral es requerido.'
        
        # 3. Validar duplicados (misma configuración) - solo si usuario está asignado
        if self.usuario_id:
            duplicados = NotificacionTasa.objects.filter(
                usuario_id=self.usuario_id,
                cliente_asociado=self.cliente_asociado,
                divisa=self.divisa,
                tipo_alerta=self.tipo_alerta,
                tipo_operacion=self.tipo_operacion
            )
        else:
            duplicados = NotificacionTasa.objects.none()
        
        # Si es umbral, también verificar condición y monto
        if self.tipo_alerta == 'umbral':
            duplicados = duplicados.filter(
                condicion_umbral=self.condicion_umbral,
                monto_umbral=self.monto_umbral
            )
        
        # Excluir la instancia actual si estamos editando
        if self.pk:
            duplicados = duplicados.exclude(pk=self.pk)
        
        if duplicados.exists():
            errors['__all__'] = 'Ya existe una notificación idéntica con esta configuración.'
        
        if errors:
            raise ValidationError(errors)

class Notificacion(models.Model):
    """
    Notificación individual enviada a un usuario.

    Representa una instancia específica de notificación generada cuando se cumplen
    las condiciones de una regla de alerta. Contiene el mensaje, estado de lectura
    y metadatos sobre el envío.

    :param usuario: Usuario destinatario de la notificación
    :type usuario: CustomUser
    :param alerta_base: Regla de alerta que generó esta notificación (puede ser null)
    :type alerta_base: NotificacionTasa, optional
    :param mensaje: Contenido del mensaje de la notificación
    :type mensaje: str
    :param fecha_creacion: Fecha y hora de creación automática
    :type fecha_creacion: datetime
    :param estado_lectura: Estado de lectura ('pendiente' o 'leida')
    :type estado_lectura: str
    :param correo_enviado: Indica si se envió notificación por correo electrónico
    :type correo_enviado: bool
    """
    
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    alerta_base = models.ForeignKey(
        NotificacionTasa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Regla de Alerta"
    )

    mensaje = models.TextField()

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    estado_lectura = models.CharField(
        max_length=10,
        choices=ESTADO_LECTURA_CHOICES,
        default='pendiente'
    )

    correo_enviado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Notificación de Usuario"
        verbose_name_plural = "Notificaciones de Usuario"
        ordering = ['-fecha_creacion']

    def __str__(self):
        """
        Representación en cadena de la notificación.

        :return: Cadena con usuario y primeros 30 caracteres del mensaje
        :rtype: str
        """
        return f"Notificación para {self.usuario.username}: {self.mensaje[:30]}..."