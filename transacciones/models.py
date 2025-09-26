# transacciones/models.py
from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone
import json
from django.db import transaction # Necesario para transacciones atómicas
import logging # Para registrar la acción
from django.db.models.signals import post_save # Para la señal
from django.dispatch import receiver # Para la señal
from django.db.models import Q # Para filtros complejos en la señal


# ASUMIDO: Divisa y CotizacionSegmento están disponibles en la app 'divisas'
from divisas.models import CotizacionSegmento # Importar el modelo de tasa

logger = logging.getLogger(__name__)




class Transaccion(models.Model):
    """
    Modelo principal para las transacciones de compra y venta de divisas
    """
    TIPO_OPERACION_CHOICES = [
        ('compra', 'Compra de Divisa'),
        ('venta', 'Venta de Divisa'),
    ]

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
        ('anulada', 'Anulada'),
        ('a_retirar', 'A Retirar'),
    ]

    # Identificación de la transacción
    numero_transaccion = models.CharField(
        'Número de Transacción', 
        max_length=20, 
        unique=True, 
        editable=False
    )
    
    # Información básica de la operación
    tipo_operacion = models.CharField(
        'Tipo de Operación',
        max_length=10,
        choices=TIPO_OPERACION_CHOICES
    )
    
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='transacciones'
    )
    
    # Información de las divisas
    divisa_origen = models.ForeignKey(
        'divisas.Divisa',
        related_name='transacciones_origen',
        on_delete=models.PROTECT
    )
    
    divisa_destino = models.ForeignKey(
        'divisas.Divisa',
        related_name='transacciones_destino',
        on_delete=models.PROTECT
    )
    
    # Montos y tasas
    monto_origen = models.DecimalField(
        'Monto Origen',
        max_digits=20,
        decimal_places=8
    )
    
    monto_destino = models.DecimalField(
        'Monto Destino',
        max_digits=20,
        decimal_places=8
    )
    
    tasa_de_cambio_aplicada = models.DecimalField(
        'Tasa de Cambio Aplicada',
        max_digits=20,
        decimal_places=8
    )
    
    # Estado y fechas
    estado = models.CharField(
        'Estado',
        max_length=15,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    
    fecha_creacion = models.DateTimeField(
        'Fecha de Creación',
        auto_now_add=True
    )
    
    fecha_actualizacion = models.DateTimeField(
        'Última Actualización',
        auto_now=True
    )

    observacion = models.TextField('Observación/Motivo de estado', blank=True, default='')
    
    # Información del medio de pago/acreditación
    medio_pago_datos = models.JSONField(
        'Datos del Medio de Pago/Acreditación',
        default=dict,
        help_text='Información del medio utilizado para la operación'
    )
    
    # Información adicional
    observaciones = models.TextField(
        'Observaciones',
        blank=True,
        help_text='Notas adicionales sobre la transacción'
    )
    
    # Usuario que procesó la transacción
    procesado_por = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones_procesadas'
    )

    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['cliente', 'fecha_creacion']),
            models.Index(fields=['tipo_operacion', 'estado']),
            models.Index(fields=['numero_transaccion']),
            models.Index(fields=['fecha_creacion']),
        ]

    def save(self, *args, **kwargs):
        if not self.numero_transaccion:
            self.numero_transaccion = self._generate_transaction_number()
        super().save(*args, **kwargs)

    def _generate_transaction_number(self):
        """Generar número único de transacción"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        prefix = 'TRX'
        return f"{prefix}{timestamp}"

    def __str__(self):
        return f"{self.numero_transaccion} - {self.cliente.nombre_completo} - {self.get_tipo_operacion_display()}"

    @property
    def es_compra(self):
        """True si es una operación de compra"""
        return self.tipo_operacion == 'compra'

    @property
    def es_venta(self):
        """True si es una operación de venta"""
        return self.tipo_operacion == 'venta'

    @property
    def puede_cancelarse(self):
        """True si la transacción puede cancelarse"""
        return self.estado in ['pendiente']

    @property
    def puede_anularse(self):
        """True si la transacción puede anularse"""
        return self.estado in ['pagada', 'a_retirar']

    def get_medio_pago_info(self):
        """Obtener información del medio de pago de forma segura"""
        try:
            return self.medio_pago_datos
        except (TypeError, ValueError):
            return {}

    def set_medio_pago_info(self, info):
        """Establecer información del medio de pago"""
        if isinstance(info, dict):
            self.medio_pago_datos = info
        else:
            self.medio_pago_datos = {}

    def cambiar_estado(self, nuevo_estado, observacion=None, usuario=None):
        """
        Cambiar el estado de la transacción con validaciones
        """
        estados_validos = dict(self.ESTADO_CHOICES).keys()
        
        if nuevo_estado not in estados_validos:
            raise ValidationError(f'Estado "{nuevo_estado}" no es válido')

        estado_anterior = self.estado
        self.estado = nuevo_estado
        
        if observacion:
            if self.observaciones:
                self.observaciones += f"\n[{timezone.now()}] {observacion}"
            else:
                self.observaciones = f"[{timezone.now()}] {observacion}"

        # Crear historial del cambio
        HistorialTransaccion.objects.create(
            transaccion=self,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            observaciones=observacion or f'Cambio de estado de {estado_anterior} a {nuevo_estado}',
            modificado_por=usuario
        )

        self.save()

    def get_comision_aplicada(self):
        """Obtener la comisión aplicada desde los datos del medio de pago"""
        medio_info = self.get_medio_pago_info()
        return medio_info.get('comision', '0%')
    
    def _enviar_notificacion_cancelacion(self, razon):
        """
        Función placeholder para simular el envío de una notificación (Email).
        En un sistema real, aquí se implementaría el código real de envío de email/push.
        """
        cliente_email = None
        try:
            # Asumo que puedes acceder al email del usuario a través del cliente
            cliente_email = self.cliente.usuario.email 
        except Exception:
            pass
        
        if cliente_email:
            email_subject = f"Cancelación de Transacción #{self.numero_transaccion} - Actualización de Tasa"
            email_body = (
                f"Estimado(a) cliente {self.cliente.nombre_completo or self.cliente.id},\n\n"
                f"Te informamos que tu transacción de cambio **#{self.numero_transaccion}** ha sido **CANCELADA automáticamente**.\n\n"
                f"**Razón:** {razon}.\n"
                f"La cotización de la divisa involucrada ha sido actualizada en nuestro sistema, invalidando la tasa anterior.\n\n"
                "Para continuar con la operación, por favor, inicia una nueva transacción con la cotización actualizada.\n\n"
                "Gracias por tu comprensión.\n"
                "Equipo de Soporte."
            )
            
            # NOTA: En un sistema real, se usaría send_mail(email_subject, email_body, ...)
            logger.info(f"EMAIL_SIMULADO enviado a {cliente_email} por trans. {self.numero_transaccion}. Asunto: {email_subject}")
        else:
            logger.warning(f"No se pudo enviar notificación de cancelación a cliente de trans. {self.numero_transaccion}. Email no encontrado.")
    
    def cancelar_automaticamente(self, razon):
        """
        Cancela la transacción automáticamente si está pendiente y envía una notificación.
        """
        # Se usa 'pendiente' como string si no definiste la constante en este snippet
        if self.estado != 'pendiente': 
            return False
        
        estado_anterior = self.estado 
        observacion_completa = f"CANCELACIÓN AUTOMÁTICA POR TASA: {razon}"

        with transaction.atomic():
            self.estado = 'cancelada' # Usar 'cancelada'
            self.observacion = f"CANCELACIÓN AUTOMÁTICA POR TASA: {razon}"
            
            # Solo actualizar los campos modificados
            self.save(update_fields=['estado', 'observacion'])

             # 💡 PASO CLAVE: Crear el registro de historial con el motivo
            HistorialTransaccion.objects.create(
                transaccion=self,
                fecha_cambio=timezone.now(),
                estado_anterior=estado_anterior,
                estado_nuevo=self.estado,
                observaciones=observacion_completa,
                # El campo 'usuario' puede ser nulo o apuntar a un usuario de sistema
                modificado_por=None, 
            )
            
            # Enviar notificación (ver helper abajo)
            self._enviar_notificacion_cancelacion(razon)
            
            logger.info(f"Transacción {self.numero_transaccion} cancelada automáticamente por: {razon}")

            return True


class HistorialTransaccion(models.Model):
    """
    Historial de cambios en las transacciones
    """
    transaccion = models.ForeignKey(
        Transaccion,
        on_delete=models.CASCADE,
        related_name='historial'
    )
    
    estado_anterior = models.CharField(
        'Estado Anterior',
        max_length=15,
        choices=Transaccion.ESTADO_CHOICES
    )
    
    estado_nuevo = models.CharField(
        'Estado Nuevo',
        max_length=15,
        choices=Transaccion.ESTADO_CHOICES
    )
    
    fecha_cambio = models.DateTimeField(
        'Fecha del Cambio',
        auto_now_add=True
    )
    
    observaciones = models.TextField(
        'Observaciones',
        blank=True
    )
    
    modificado_por = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Historial de Transacción'
        verbose_name_plural = 'Historiales de Transacciones'
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"{self.transaccion.numero_transaccion} - {self.estado_anterior} → {self.estado_nuevo}"


class ConfiguracionTransaccion(models.Model):
    """
    Configuración general para las transacciones
    """
    nombre = models.CharField(
        'Nombre de Configuración',
        max_length=100,
        unique=True
    )
    
    valor = models.TextField(
        'Valor'
    )
    
    descripcion = models.TextField(
        'Descripción',
        blank=True
    )
    
    fecha_modificacion = models.DateTimeField(
        'Última Modificación',
        auto_now=True
    )
    
    modificado_por = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Configuración de Transacción'
        verbose_name_plural = 'Configuraciones de Transacciones'

    def __str__(self):
        return self.nombre

    @classmethod
    def get_valor(cls, nombre, default=None):
        """Obtener valor de configuración"""
        try:
            config = cls.objects.get(nombre=nombre)
            try:
                # Intentar parsear como JSON
                return json.loads(config.valor)
            except json.JSONDecodeError:
                # Si no es JSON válido, devolver como string
                return config.valor
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_valor(cls, nombre, valor, descripcion=None, usuario=None):
        """Establecer valor de configuración"""
        if isinstance(valor, (dict, list)):
            valor_str = json.dumps(valor)
        else:
            valor_str = str(valor)

        config, created = cls.objects.get_or_create(
            nombre=nombre,
            defaults={
                'valor': valor_str,
                'descripcion': descripcion or '',
                'modificado_por': usuario
            }
        )

        if not created:
            config.valor = valor_str
            if descripcion:
                config.descripcion = descripcion
            config.modificado_por = usuario
            config.save()

        return config

# ----------------------------------------------------------------------
# --- SEÑAL PARA CANCELACIÓN AUTOMÁTICA DE TRANSACCIONES ---
# ----------------------------------------------------------------------

@receiver(post_save, sender=CotizacionSegmento)
def cancelar_transacciones_pendientes_por_tasa(sender, instance, created, **kwargs):
    """
    Se ejecuta CADA VEZ que se guarda una CotizacionSegmento.
    Busca transacciones pendientes con la misma divisa y las cancela.
    """
    
    # 1. Validación de la divisa base
    # Si la cotización actualizada es del Guaraní (PYG o código '116'), no hacemos nada.
    if instance.divisa.code in ['PYG', '116']:
         return 

    divisa_actualizada = instance.divisa
    
    # 2. Encontrar transacciones PENDIENTES afectadas
    transacciones_a_cancelar = Transaccion.objects.filter(
        Q(divisa_origen=divisa_actualizada) | Q(divisa_destino=divisa_actualizada),
        estado='pendiente'
    ).select_related('cliente', 'divisa_origen', 'divisa_destino')
    
    razon_cancelacion = (
        f"Cotización de {divisa_actualizada.code} ha sido actualizada en el sistema. "
        f"(Segmento: {instance.segmento.name})"
    )
    
    # 3. Cancelar cada transacción
    for transaccion in transacciones_a_cancelar:
        transaccion.cancelar_automaticamente(razon=razon_cancelacion)