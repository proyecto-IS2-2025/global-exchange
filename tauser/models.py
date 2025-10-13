from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from divisas.models import Divisa
from transacciones.models import Transaccion
from clientes.models import Cliente
from decimal import Decimal


User = get_user_model()

class Terminal(models.Model):
    """Representa una terminal de autoservicio física."""
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=20, unique=True, help_text="Código identificador de la terminal")
    ubicacion = models.CharField(max_length=255)
    usuario_responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='terminales_a_cargo'
    )
    is_activa = models.BooleanField(default=True, verbose_name="¿Activa?")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Terminal"
        verbose_name_plural = "Terminales"
        ordering = ['nombre']
    
    def __str__(self):
        return f"Terminal {self.nombre} ({self.ubicacion})"
    
    def tiene_inventario_suficiente(self, divisa, monto):
        """Verifica si hay inventario suficiente para una divisa"""
        try:
            inventario = self.inventario.get(divisa=divisa)
            return inventario.cantidad >= monto
        except InventarioDivisaTerminal.DoesNotExist:
            return False


class InventarioDivisaTerminal(models.Model):
    """Inventario (stock) de una divisa en una terminal específica."""
    terminal = models.ForeignKey(
        Terminal, 
        on_delete=models.CASCADE, 
        related_name='inventario'
    )
    divisa = models.ForeignKey(
        Divisa, 
        on_delete=models.PROTECT,
        limit_choices_to={'is_active': True}
    )
    cantidad = models.DecimalField(
        max_digits=20, 
        decimal_places=8, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Cantidad disponible en esta terminal"
    )
    cantidad_minima = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('100.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Cantidad mínima de alerta"
    )
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actualizaciones_inventario'
    )

    class Meta:
        unique_together = ('terminal', 'divisa')
        verbose_name = "Inventario de Divisa por Terminal"
        verbose_name_plural = "Inventarios de Divisa por Terminal"
        ordering = ['terminal', 'divisa']

    def __str__(self):
        return f"{self.terminal.nombre}: {self.cantidad} de {self.divisa.code}"
    
    @property
    def necesita_reposicion(self):
        """Indica si el inventario está por debajo del mínimo"""
        return self.cantidad < self.cantidad_minima
    
    def descontar(self, monto):
        """Descuenta una cantidad del inventario"""
        if self.cantidad < monto:
            raise ValueError(f"Inventario insuficiente. Disponible: {self.cantidad}, Solicitado: {monto}")
        self.cantidad -= monto
        self.save()
    
    def agregar(self, monto):
        """Agrega una cantidad al inventario"""
        self.cantidad += monto
        self.save()


class PINTerminalCliente(models.Model):
    """PINs temporales generados para que los clientes accedan a la terminal"""
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='pines_terminal'
    )
    pin = models.CharField(
        max_length=6,
        help_text="PIN de 6 dígitos"
    )
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(
        help_text="Fecha y hora de expiración del PIN"
    )
    usado = models.BooleanField(default=False)
    fecha_uso = models.DateTimeField(null=True, blank=True)
    terminal_usada = models.ForeignKey(
        Terminal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "PIN de Terminal"
        verbose_name_plural = "PINs de Terminal"
        ordering = ['-fecha_generacion']
        indexes = [
            models.Index(fields=['pin', 'usado']),
            models.Index(fields=['cliente', 'fecha_expiracion']),
        ]
    
    def __str__(self):
        return f"PIN {self.pin} - {self.cliente.nombre_completo}"
    
    def esta_vigente(self):
        """Verifica si el PIN está vigente"""
        from django.utils import timezone
        return not self.usado and self.fecha_expiracion > timezone.now()
    
    def marcar_usado(self, terminal):
        """Marca el PIN como usado"""
        from django.utils import timezone
        self.usado = True
        self.fecha_uso = timezone.now()
        self.terminal_usada = terminal
        self.save()


class RegistroTransaccionTerminal(models.Model):
    """Registro de operaciones realizadas en terminales"""
    TIPO_OPERACION_CHOICES = [
        ('RETIRO', 'Retiro de Divisa'),
        ('PAGO', 'Pago/Depósito'),
        ('CONSULTA', 'Consulta'),
    ]
    
    terminal = models.ForeignKey(
        Terminal,
        on_delete=models.PROTECT,
        related_name='operaciones'
    )
    transaccion_original = models.ForeignKey(
        Transaccion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Transacción del sistema relacionada"
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='operaciones_terminal'
    )
    tipo_operacion = models.CharField(
        max_length=20,
        choices=TIPO_OPERACION_CHOICES
    )
    divisa = models.ForeignKey(
        Divisa,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    monto_operacion = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True
    )
    fue_exitoso = models.BooleanField(default=False)
    mensaje_error = models.TextField(blank=True)
    fecha_operacion = models.DateTimeField(auto_now_add=True)
    pin_usado = models.ForeignKey(
        PINTerminalCliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "Registro de Operación en Terminal"
        verbose_name_plural = "Registros de Operaciones en Terminal"
        ordering = ['-fecha_operacion']
        indexes = [
            models.Index(fields=['terminal', 'fecha_operacion']),
            models.Index(fields=['cliente', 'fecha_operacion']),
        ]
    
    def __str__(self):
        return f"{self.tipo_operacion} - {self.cliente.nombre_completo} - {self.fecha_operacion}"