# transacciones/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import json
from django.core.exceptions import ValidationError
from clientes.services import verificar_limites
from django.db import transaction # Necesario para transacciones atómicas
import logging # Para registrar la acción
from django.db.models.signals import post_save # Para la señal
from notificaciones.models import Notificacion  # Para crear notificaciones
from django.dispatch import receiver # Para la señal
from django.db.models import Q # Para filtros complejos en la señal
from decimal import Decimal, ROUND_HALF_UP
import uuid

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
        ('completado', 'Completado'),  # <-- NUEVO estado
        ('cancelada', 'Cancelada'),
        ('anulada', 'Anulada'),
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

    # Campo antiguo (mantener para compatibilidad con BD existente)
    metodo_pago = models.CharField(
        'Método de Pago (obsoleto)',
        max_length=100,
        blank=True,
        null=True,
        help_text='Campo antiguo - usar medio_pago_datos en su lugar'
    )

    # Nuevo/Ajustado: datos completos del medio seleccionado (id, nombre, tipo, comision, datos_campos, etc.)
    medio_pago_datos = models.JSONField(
        'Datos del Medio de Pago/Acreditación',
        default=dict,
        blank=True,
        null=True,
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
    
    # Código Tauser: generado para compras pagadas y todas las ventas
    tauser_code = models.CharField(
        'Código Tauser',
        max_length=8,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text='Código alfanumérico de 8 caracteres para acceso en terminal'
    )
    
    # Terminal TAUSER asignado (solo para compras)
    tauser_terminal = models.ForeignKey(
        'tauser.Terminal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones_asignadas',
        help_text='Terminal TAUSER donde el cliente debe retirar la divisa (solo compras)'
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

    def redondear_monto(self, monto, codigo_divisa):
        """
        Redondea un monto según el código de divisa.
        - PYG: 0 decimales
        - Otras divisas: 2 decimales
        """
        try:
            decimales = 0 if codigo_divisa.upper() == 'PYG' else 2
            return Decimal(monto).quantize(
                Decimal("1") if decimales == 0 else Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )
        except Exception:
            return Decimal("0.00")

    def aplicar_redondeo_montos(self):
        """
        Aplica el redondeo a los montos según el tipo de divisa
        """
        if self.divisa_origen and self.monto_origen:
            self.monto_origen = self.redondear_monto(
                self.monto_origen, 
                self.divisa_origen.code
            )
        
        if self.divisa_destino and self.monto_destino:
            self.monto_destino = self.redondear_monto(
                self.monto_destino, 
                self.divisa_destino.code
            )
        
        # La tasa siempre se redondea a 2 decimales
        if self.tasa_de_cambio_aplicada:
            self.tasa_de_cambio_aplicada = Decimal(self.tasa_de_cambio_aplicada).quantize(
                Decimal("0.01"), 
                rounding=ROUND_HALF_UP
            )

    def clean(self):
        """
        Validaciones a nivel de modelo para la transacción
        """
        from django.core.exceptions import ValidationError
        errors = {}
        
        # Validar que las divisas existan
        if not self.divisa_origen:
            errors['divisa_origen'] = 'La divisa de origen es requerida'
            
        if not self.divisa_destino:
            errors['divisa_destino'] = 'La divisa de destino es requerida'
            
        # Validar que los montos sean positivos
        if self.monto_origen and self.monto_origen <= 0:
            errors['monto_origen'] = 'El monto origen debe ser mayor a 0'
            
        if self.monto_destino and self.monto_destino <= 0:
            errors['monto_destino'] = 'El monto destino debe ser mayor a 0'
            
        if self.tasa_de_cambio_aplicada and self.tasa_de_cambio_aplicada <= 0:
            errors['tasa_de_cambio_aplicada'] = 'La tasa de cambio debe ser mayor a 0'
        
        # Validar que no sea la misma divisa (a menos que sea un caso especial)
        if self.divisa_origen and self.divisa_destino and self.divisa_origen == self.divisa_destino:
            errors['divisa_destino'] = 'La divisa origen y destino no pueden ser iguales'
        
        # Validar tipo de operación vs divisas
        if self.tipo_operacion == 'venta':
            # En venta: cliente vende divisa extranjera, recibe PYG
            if self.divisa_destino and self.divisa_destino.code.upper() != 'PYG':
                errors['divisa_destino'] = 'En operaciones de venta, la divisa destino debe ser PYG'
                
        elif self.tipo_operacion == 'compra':
            # En compra: cliente paga PYG, recibe divisa extranjera  
            if self.divisa_origen and self.divisa_origen.code.upper() != 'PYG':
                errors['divisa_origen'] = 'En operaciones de compra, la divisa origen debe ser PYG'
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        print(">>> Entrando en save() de Transaccion")
        
        # Generar número si no existe
        if not getattr(self, 'numero_transaccion', None):
            self.numero_transaccion = self._generar_numero_transaccion()
        
        # Asignar código tauser si corresponde (ventas siempre, compras pagadas)
        self.asignar_tauser_code_si_corresponde()
        
        # Aplicar redondeo antes de cualquier validación
        self.aplicar_redondeo_montos()
        
        try:
            self.full_clean()  # 👈 esto llama a clean()
        except ValidationError as e:
            raise
        
        super().save(*args, **kwargs)

    def _generar_numero_transaccion(self):
        """Generar número único de transacción"""
        # Formato simple y único: TRX-YYYYMMDD-XXXX
        hoy = timezone.now().strftime('%Y%m%d')
        random = uuid.uuid4().hex[:6].upper()
        return f'TRX-{hoy}-{random}'
    
    def _generar_tauser_code(self):
        """Generar código tauser único de 8 caracteres alfanuméricos"""
        import random
        import string
        
        caracteres = string.ascii_uppercase + string.digits
        while True:
            codigo = ''.join(random.choices(caracteres, k=8))
            # Verificar que sea único
            if not Transaccion.objects.filter(tauser_code=codigo).exists():
                return codigo
    
    def asignar_tauser_code_si_corresponde(self):
        """
        Asigna código tauser si:
        - Es una compra con estado 'pagada' 
        - Es una venta (cualquier estado inicial)
        Y aún no tiene código asignado
        """
        if not self.tauser_code:
            debe_tener_codigo = False
            
            # Compras: solo si está en estado 'pagada'
            if self.tipo_operacion == 'compra' and self.estado == 'pagada':
                debe_tener_codigo = True
            
            # Ventas: siempre (desde cualquier estado)
            if self.tipo_operacion == 'venta':
                debe_tener_codigo = True
            
            if debe_tener_codigo:
                self.tauser_code = self._generar_tauser_code()
                logger.info(f"✅ Código Tauser '{self.tauser_code}' asignado a transacción {self.numero_transaccion}")

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

    @property
    def es_pago_stripe(self):
        """True si es un pago realizado con Stripe"""
        try:
            if not self.medio_pago_datos:
                return False
            
            # Verificar si el tipo de medio es 'stripe'
            if self.medio_pago_datos.get('tipo') == 'stripe':
                return True
            
            # Verificar si hay información de Stripe en el medio_pago_datos
            stripe_payment_intent_id = self.medio_pago_datos.get('stripe_payment_intent_id')
            if stripe_payment_intent_id:
                return True
            
            # Verificar si el nombre del medio contiene "stripe"
            nombre = self.medio_pago_datos.get('nombre', '').lower()
            if 'stripe' in nombre:
                return True
            
            return False
        except (TypeError, AttributeError):
            return False

    @property
    def card_last4(self):
        """Obtener los últimos 4 dígitos de la tarjeta si es pago Stripe"""
        try:
            if self.es_pago_stripe and self.medio_pago_datos:
                return self.medio_pago_datos.get('stripe_card_last4')
        except (TypeError, AttributeError):
            pass
        return None

    @property
    def card_brand(self):
        """Obtener la marca de la tarjeta si es pago Stripe"""
        try:
            if self.es_pago_stripe and self.medio_pago_datos:
                return self.medio_pago_datos.get('stripe_card_brand')
        except (TypeError, AttributeError):
            pass
        return None


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

    def cambiar_estado(self, nuevo_estado, observacion='', usuario=None):
        """
        Cambiar el estado de la transacción con validaciones
        """
        estado_actual = getattr(self, 'estado', '')
        if nuevo_estado == estado_actual:
            return
        if nuevo_estado not in dict(self.ESTADO_CHOICES):
            raise ValueError('Estado no válido')

        # Persistir cambio
        self.estado = nuevo_estado
        
        # Si es compra y pasa a 'pagada', asignar código tauser
        if self.tipo_operacion == 'compra' and nuevo_estado == 'pagada':
            self.asignar_tauser_code_si_corresponde()
        
        self.save(update_fields=['estado', 'tauser_code'] if self.tauser_code else ['estado'])

        # Registrar en historial
        try:
            HistorialTransaccion.objects.create(
                transaccion=self,
                estado_anterior=estado_actual,
                estado_nuevo=nuevo_estado,
                observaciones=observacion or '',
                modificado_por=usuario if usuario and usuario.is_authenticated else None,
            )
        except Exception:
            # Evitar romper si por alguna razón el historial falla
            pass

    def get_comision_aplicada(self):
        """Obtener la comisión aplicada desde los datos del medio de pago"""
        medio_info = self.get_medio_pago_info()
        return medio_info.get('comision', '0%')

    def _enviar_notificacion_cancelacion(self, razon, notificacion_obj=None):
        """
        Envía notificación por correo sobre la cancelación de transacción.
        Retorna True si el correo se envió exitosamente, False si no.
        """
        from django.core.mail import send_mail
        from django.conf import settings
        from notificaciones.models import ConfiguracionGeneral
        
        correo_enviado_exitosamente = False

        if self.procesado_por:
            # Verificar si el usuario tiene configurado recibir correos
            try:
                config = ConfiguracionGeneral.objects.get(usuario=self.procesado_por)
                canal = config.canal_notificacion
                
                # Solo enviar si el canal incluye correo
                if canal == "sistema_correo":
                    # Identificar la divisa extranjera (no PYG)
                    divisa_extranjera = None
                    if self.divisa_origen and self.divisa_origen.code not in ['PYG', '116']:
                        divisa_extranjera = self.divisa_origen.code
                    elif self.divisa_destino and self.divisa_destino.code not in ['PYG', '116']:
                        divisa_extranjera = self.divisa_destino.code
                    
                    divisa_texto = f"({divisa_extranjera})" if divisa_extranjera else ""
                    
                    email_subject = f"Cancelación de Transacción #{self.numero_transaccion} - Actualización de Tasa"
                    email_body = (
                        f"Estimado(a) cliente {self.cliente.nombre_completo or self.cliente.id},\n\n"
                        f"Te informamos que tu transacción de cambio #{self.numero_transaccion} ha sido CANCELADA automáticamente.\n\n"
                        f"Razón: {razon}\n\n"
                        f"La cotización de la divisa extranjera {divisa_texto} ha sido actualizada en nuestro sistema, "
                        f"invalidando la tasa de cambio anterior con la que iniciaste tu transacción.\n\n"
                        "Para continuar con la operación, por favor, inicia una nueva transacción con la cotización actualizada.\n\n"
                        "Gracias por tu comprensión.\n"
                        "Equipo de Soporte - Global Exchange"
                    )

                    try:
                        send_mail(
                            subject=email_subject,
                            message=email_body,
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=[self.procesado_por.email],
                            fail_silently=False
                        )
                        correo_enviado_exitosamente = True
                        logger.info(f"📧 Correo de cancelación enviado a {self.procesado_por.email} por trans. {self.numero_transaccion}")
                    except Exception as e:
                        logger.error(f"❌ Error al enviar correo de cancelación a {self.procesado_por.email}: {e}")
                        correo_enviado_exitosamente = False
                else:
                    logger.info(f"⏭️ Usuario {self.procesado_por.email} tiene canal='{canal}', no se envía correo de cancelación")
                    
            except ConfiguracionGeneral.DoesNotExist:
                logger.warning(f"⚠️ Usuario {self.procesado_por.email} no tiene ConfiguracionGeneral, no se envía correo")
        else:
            logger.warning(f"⚠️ No se pudo enviar correo de cancelación para trans. {self.numero_transaccion}. Email o usuario no encontrado.")
        
        # Actualizar el objeto Notificacion si se proporcionó
        if notificacion_obj and correo_enviado_exitosamente:
            notificacion_obj.correo_enviado = True
            notificacion_obj.save(update_fields=['correo_enviado'])
            
        return correo_enviado_exitosamente

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
            
            # 🔔 CREAR NOTIFICACIÓN para el usuario que procesó la transacción
            notificacion_obj = None
            if self.procesado_por:
                mensaje_notificacion = (
                    f"Su transacción {self.numero_transaccion} ha sido cancelada por un cambio en la cotización. "
                    f"Ingrese a su historial de transacciones para corroborarlo."
                )
                
                notificacion_obj = Notificacion.objects.create(
                    usuario=self.procesado_por,
                    mensaje=mensaje_notificacion,
                    estado_lectura='pendiente',
                    correo_enviado=False
                )

            # Enviar notificación por correo y actualizar correo_enviado si es exitoso
            self._enviar_notificacion_cancelacion(razon, notificacion_obj)

            logger.info(f"Transacción {self.numero_transaccion} cancelada automáticamente por: {razon}")

            return True

# ... (El resto del código de HistorialTransaccion, ConfiguracionTransaccion y señales permanece igual)

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
    try:
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
    except Exception as e:
        # Si hay un error (por ejemplo, columna faltante), no fallar
        # Solo registrar el error en logs si es necesario
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error al cancelar transacciones por tasa: {e}")