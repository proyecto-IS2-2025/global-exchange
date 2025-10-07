from django.core.exceptions import ValidationError
from django.db import models
from users.models import CustomUser
from django.core.validators import MinValueValidator
from clientes.models import Cliente

# Opciones fijas para los campos (sin cambios)
CANAL_CHOICES = [
    ('sistema', 'Solo por el Sistema'),
    ('sistema_correo', 'Sistema y Correo Electrónico'),
]

TIPO_ALERTA_CHOICES = [
    ('general', 'Cambio General'),
    ('umbral', 'Alcanzar Umbral'),
]

OPERACION_CHOICES = [
    ('compra', 'Compra'),
    ('venta', 'Venta'),
    ('ambos', 'Compra y Venta'),
]

UMBRAL_CONDICION_CHOICES = [
    ('mayor', 'Mayor o igual que'),
    ('menor', 'Menor o igual que'),
]

ESTADO_LECTURA_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('leida', 'Leída'),
]


class ConfiguracionGeneral(models.Model):
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    habilitar_notificaciones = models.BooleanField(default=True)
    canal_notificacion = models.CharField(max_length=20, choices=CANAL_CHOICES, default='sistema')

    def __str__(self):
        return f"Configuración de {self.usuario.username}"


class NotificacionTasa(models.Model):
    # Criterios de Aceptación: Notificación específica

    # QUIÉN creó/es dueño de la notificación (el usuario que está logueado)
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Usuario Creador")

    # NUEVA RELACIÓN: EL CONTEXTO (el Cliente asociado y su Segmento)
    cliente_asociado = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        verbose_name="Cliente Asociado"
    )

    divisa = models.CharField(max_length=5)

    # Estado y tipo
    activa = models.BooleanField(default=True)
    tipo_alerta = models.CharField(max_length=10, choices=TIPO_ALERTA_CHOICES)
    tipo_operacion = models.CharField(max_length=10, choices=OPERACION_CHOICES)

    # Campos de Umbral
    condicion_umbral = models.CharField(max_length=10, choices=UMBRAL_CONDICION_CHOICES, blank=True, null=True)
    monto_umbral = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0)]
    )

    # --- PROPIEDADES PARA FACILITAR LA EVALUACIÓN Y MENSAJES ---
    @property
    def segmento(self):
        """Acceso directo al segmento del cliente asociado para la evaluación."""
        # Asume que el modelo Cliente tiene un campo 'segmento' (FK a Segmento)
        return self.cliente_asociado.segmento

    @property
    def operacion_display(self):
        """Devuelve el valor legible de tipo_operacion ('Compra', 'Venta', etc.)."""
        return self.get_tipo_operacion_display()

    # -----------------------------------------------------------

    class Meta:
        verbose_name = "Notificación de Tasa"
        verbose_name_plural = "Notificaciones de Tasa"

    def __str__(self):
        return f"Alerta de {self.divisa} para {self.cliente_asociado.nombre} ({self.get_tipo_alerta_display()})"
    def clean(self):
        super().clean()
        # Solo permitir 'ambos' si no hay cliente (caso de configuración general)
        if self.tipo_operacion == 'ambos' and self.cliente_asociado_id:
            raise ValidationError("La opción 'Compra y Venta' solo se permite en la configuración general.")

class Notificacion(models.Model):
    # La persona que recibe la notificación
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Renombrado para claridad

    # La regla que disparó la notificación (útil para trazar)
    alerta_base = models.ForeignKey(
        NotificacionTasa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Regla de Alerta"
    )

    # El contenido del mensaje (lo que el usuario lee)
    mensaje = models.TextField()

    # Metadatos del evento
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Estado de la notificación para el usuario
    estado_lectura = models.CharField(
        max_length=10,
        choices=ESTADO_LECTURA_CHOICES,
        default='pendiente'
    )

    # Si se envió un correo
    correo_enviado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Notificación de Usuario"
        verbose_name_plural = "Notificaciones de Usuario"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Notificación para {self.usuario.username}: {self.mensaje[:30]}..."