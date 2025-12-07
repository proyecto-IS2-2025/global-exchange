from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from divisas.models import Divisa, Denominacion
from transacciones.models import Transaccion
from clientes.models import Cliente
from decimal import Decimal
from .services import calcular_desglose_optimo

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
        
    def tiene_denominaciones_suficientes(self, divisa, monto_total):
        """
        Verifica si hay denominaciones suficientes para entregar el monto.
        Retorna (bool, dict) donde dict contiene el desglose sugerido.
        """
        inventarios = InventarioDenominacionTerminal.objects.filter(
            terminal=self,
            denominacion__divisa=divisa,
            denominacion__is_active=True,
            cantidad__gt=0
        ).select_related('denominacion').order_by('-denominacion__valor')
        
        if not inventarios.exists():
            return False, {}
        
        resultado = calcular_desglose_optimo(inventarios, monto_total)
        return resultado['posible'], resultado.get('desglose', {})
    
    def tiene_denominaciones_disponibles_para_retiro(self, divisa, monto_total):
        """
        Verifica si hay denominaciones disponibles (descontando reservas) 
        para entregar el monto solicitado.
        Retorna (bool, dict, dict) donde los dicts contienen el desglose sugerido 
        y las cantidades disponibles considerando reservas.
        """
        from django.db.models import Sum, Q
        
        # Obtener inventarios con cantidades disponibles (real - reservado)
        inventarios = InventarioDenominacionTerminal.objects.filter(
            terminal=self,
            denominacion__divisa=divisa,
            denominacion__is_active=True,
            cantidad__gt=0
        ).select_related('denominacion')
        
        if not inventarios.exists():
            return False, {}, {}
        
        # Calcular cantidades reservadas para cada inventario
        inventarios_con_disponible = []
        for inventario in inventarios:
            # Sumar cantidades reservadas (solo estado 'reservada')
            cantidad_reservada = inventario.reservas.filter(
                estado='reservada'
            ).aggregate(
                total_reservado=Sum('cantidad_reservada')
            )['total_reservado'] or 0
            
            cantidad_disponible = inventario.cantidad - cantidad_reservada
            
            if cantidad_disponible > 0:
                # Crear objeto temporal con cantidad disponible
                inventario.cantidad_disponible_real = cantidad_disponible
                inventarios_con_disponible.append(inventario)
        
        if not inventarios_con_disponible:
            return False, {}, {}
        
        # Usar el algoritmo de desglose pero con las cantidades disponibles
        # Creamos una lista temporal modificando 'cantidad' por 'cantidad_disponible_real'
        resultado = self._calcular_desglose_con_disponibles(
            inventarios_con_disponible, 
            monto_total
        )
        
        return resultado['posible'], resultado.get('desglose', {}), resultado.get('disponibilidad', {})
    
    def _calcular_desglose_con_disponibles(self, inventarios, monto_total):
        """
        Calcula desglose usando las cantidades disponibles reales (descontando reservas).
        Similar a calcular_desglose_optimo pero usa cantidad_disponible_real.
        """
        from decimal import Decimal
        
        monto_pendiente = Decimal(str(monto_total))
        desglose = {}
        disponibilidad = {}
        
        # Ordenar por valor descendente
        inventarios_ordenados = sorted(
            inventarios,
            key=lambda x: x.denominacion.valor,
            reverse=True
        )
        
        for inventario in inventarios_ordenados:
            if monto_pendiente <= 0:
                break
            
            valor_billete = inventario.denominacion.valor
            cantidad_disponible = inventario.cantidad_disponible_real
            
            # Calcular cuántos billetes se necesitan
            cantidad_necesaria = int(monto_pendiente / valor_billete)
            
            if cantidad_necesaria > 0:
                cantidad_a_usar = min(cantidad_necesaria, cantidad_disponible)
                
                if cantidad_a_usar > 0:
                    desglose[inventario.id] = {
                        'inventario': inventario,
                        'cantidad': cantidad_a_usar,
                        'valor_unitario': valor_billete,
                        'subtotal': valor_billete * cantidad_a_usar
                    }
                    
                    disponibilidad[inventario.id] = {
                        'cantidad_total': inventario.cantidad,
                        'cantidad_disponible': cantidad_disponible,
                        'cantidad_a_reservar': cantidad_a_usar
                    }
                    
                    monto_pendiente -= (valor_billete * cantidad_a_usar)
        
        posible = (monto_pendiente == 0)
        
        return {
            'posible': posible,
            'desglose': desglose,
            'disponibilidad': disponibilidad,
            'sobrante': monto_pendiente,
            'monto_cubierto': monto_total - monto_pendiente
        }

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

class InventarioDenominacionTerminal(models.Model):
    """
    Inventario de denominaciones (billetes) en una terminal.
    
    Permite gestionar cantidades específicas de cada billete.
    """
    terminal = models.ForeignKey(
        Terminal,
        on_delete=models.CASCADE,
        related_name='inventario_denominaciones',
        verbose_name='Terminal'
    )
    denominacion = models.ForeignKey(
        Denominacion,
        on_delete=models.PROTECT,
        related_name='inventarios_terminal',
        verbose_name='Denominación'
    )
    cantidad = models.PositiveIntegerField(
        'Cantidad de billetes',
        default=0,
        help_text='Cantidad de billetes disponibles'
    )
    cantidad_minima = models.PositiveIntegerField(
        'Cantidad mínima',
        default=10,
        help_text='Alerta cuando la cantidad sea menor a este valor'
    )
    ultima_reposicion = models.DateTimeField(
        'Última reposición',
        null=True,
        blank=True
    )
    actualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Actualizado por'
    )
    actualizado = models.DateTimeField(auto_now=True)
    creado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Inventario de denominación'
        verbose_name_plural = 'Inventarios de denominaciones'
        unique_together = [['terminal', 'denominacion']]
        ordering = ['terminal', '-denominacion__valor']
        indexes = [
            models.Index(fields=['terminal', 'denominacion']),
            models.Index(fields=['cantidad']),
        ]
    
    def __str__(self):
        return f"{self.terminal.codigo} - {self.denominacion} (x{self.cantidad})"
    
    @property
    def valor_total(self):
        """Calcula el valor total de esta línea de inventario"""
        return self.denominacion.valor * self.cantidad
    
    @property
    def necesita_reposicion(self):
        """Indica si necesita reposición"""
        return self.cantidad < self.cantidad_minima
    
    def agregar(self, cantidad):
        """Agrega billetes al inventario"""
        self.cantidad += cantidad
        self.save()
    
    def descontar(self, cantidad):
        """Descuenta billetes del inventario"""
        if cantidad > self.cantidad:
            raise ValueError(
                f"Inventario insuficiente. Disponible: {self.cantidad}, "
                f"Solicitado: {cantidad}"
            )
        self.cantidad -= cantidad
        self.save()

class DesgloseDenominacionOperacion(models.Model):
    """
    Registra el desglose de denominaciones usado en una operación del TAUSER.
    
    Similar a DesgloseDenominacion pero para operaciones de terminal.
    """
    registro_operacion = models.ForeignKey(
        'RegistroTransaccionTerminal',
        on_delete=models.CASCADE,
        related_name='desglose_denominaciones',
        verbose_name='Operación'
    )
    denominacion = models.ForeignKey(
        Denominacion,
        on_delete=models.PROTECT,
        related_name='usos_terminal',
        verbose_name='Denominación'
    )
    cantidad = models.PositiveIntegerField(
        'Cantidad',
        default=1,
        help_text='Cantidad de billetes entregados/recibidos'
    )

    tipo_movimiento = models.CharField(
        'Tipo de movimiento',
        max_length=10,
        choices=[
            ('ENTREGA', 'Entrega al cliente'),
            ('RECEPCION', 'Recepción del cliente'),
        ]
    )
    creado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Desglose de operación'
        verbose_name_plural = 'Desgloses de operaciones'
        ordering = ['-denominacion__valor']
        unique_together = [['registro_operacion', 'denominacion']]
    
    def __str__(self):
        accion = "Entregados" if self.tipo_movimiento == 'ENTREGA' else "Recibidos"
        return f"{self.cantidad}x {self.denominacion.valor_formateado} ({accion})"
    
    @property
    def subtotal(self):
        """Calcula el subtotal de esta línea"""
        return self.denominacion.valor * self.cantidad

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


class LogRecargaInventario(models.Model):
    """
    Registro histórico de cada recarga de inventario realizada.
    Permite trazabilidad completa de quién recargó qué y cuándo.
    """
    terminal = models.ForeignKey(
        Terminal,
        on_delete=models.CASCADE,
        related_name='historial_recargas',
        verbose_name='Terminal'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recargas_realizadas',
        verbose_name='Usuario que realizó la recarga'
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y hora'
    )
    denominacion = models.ForeignKey(
        Denominacion,
        on_delete=models.CASCADE,
        verbose_name='Denominación'
    )
    cantidad_agregada = models.IntegerField(
        verbose_name='Cantidad agregada',
        validators=[MinValueValidator(1)]
    )
    cantidad_anterior = models.IntegerField(
        verbose_name='Cantidad antes de la recarga'
    )
    cantidad_nueva = models.IntegerField(
        verbose_name='Cantidad después de la recarga'
    )
    valor_total_agregado = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        verbose_name='Valor total agregado',
        help_text='Cantidad agregada × Valor denominación'
    )
    observaciones = models.TextField(
        blank=True,
        default='',
        verbose_name='Observaciones'
    )
    
    class Meta:
        verbose_name = "Log de Recarga de Inventario"
        verbose_name_plural = "Logs de Recargas de Inventario"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['terminal', '-fecha']),
            models.Index(fields=['usuario', '-fecha']),
        ]
    
    def __str__(self):
        return f"{self.denominacion} +{self.cantidad_agregada} - {self.terminal.nombre} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"
    
    def save(self, *args, **kwargs):
        """Calcular valor total agregado antes de guardar"""
        if not self.valor_total_agregado:
            self.valor_total_agregado = self.cantidad_agregada * self.denominacion.valor
        super().save(*args, **kwargs)


class MovimientoInventarioTerminal(models.Model):
    """
    Registro unificado de todos los movimientos de stock en el TAUSER.
    Incluye recargas manuales, depósitos de clientes y extracciones.
    """
    TIPO_MOVIMIENTO_CHOICES = [
        ('RECARGA', 'Recarga Manual'),
        ('DEPOSITO', 'Depósito de Cliente'),
        ('EXTRACCION', 'Extracción/Retiro'),
    ]
    
    terminal = models.ForeignKey(
        Terminal,
        on_delete=models.CASCADE,
        related_name='movimientos_inventario',
        verbose_name='Terminal'
    )
    tipo_movimiento = models.CharField(
        max_length=15,
        choices=TIPO_MOVIMIENTO_CHOICES,
        verbose_name='Tipo de Movimiento'
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y hora'
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_tauser',
        verbose_name='Cliente',
        help_text='Cliente asociado (solo para depósitos y extracciones)'
    )
    transaccion = models.ForeignKey(
        Transaccion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_tauser',
        verbose_name='Transacción',
        help_text='Transacción relacionada (solo para depósitos y extracciones)'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_inventario_tauser',
        verbose_name='Usuario',
        help_text='Usuario que realizó la recarga (solo para recargas manuales)'
    )
    observaciones = models.TextField(
        blank=True,
        default='',
        verbose_name='Observaciones'
    )
    
    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['terminal', '-fecha']),
            models.Index(fields=['tipo_movimiento', '-fecha']),
            models.Index(fields=['cliente', '-fecha']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.terminal.codigo} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"
    
    @property
    def cantidad_total_billetes(self):
        """Retorna la cantidad total de billetes del movimiento"""
        return sum(d.cantidad for d in self.detalles.all())
    
    @property
    def valor_total(self):
        """Retorna el valor total del movimiento"""
        return sum(d.subtotal for d in self.detalles.all())


class DetalleMovimientoInventario(models.Model):
    """
    Detalle de cada denominación involucrada en un movimiento de inventario.
    """
    movimiento = models.ForeignKey(
        MovimientoInventarioTerminal,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name='Movimiento'
    )
    denominacion = models.ForeignKey(
        Denominacion,
        on_delete=models.PROTECT,
        verbose_name='Denominación'
    )
    cantidad = models.IntegerField(
        verbose_name='Cantidad',
        help_text='Cantidad de billetes (positivo para ingreso, se usa para extracciones también)'
    )
    cantidad_anterior = models.IntegerField(
        verbose_name='Stock anterior',
        help_text='Cantidad en stock antes del movimiento'
    )
    cantidad_nueva = models.IntegerField(
        verbose_name='Stock nuevo',
        help_text='Cantidad en stock después del movimiento'
    )
    
    class Meta:
        verbose_name = "Detalle de Movimiento"
        verbose_name_plural = "Detalles de Movimientos"
        ordering = ['-denominacion__valor']
    
    def __str__(self):
        return f"{self.cantidad}x {self.denominacion.valor_formateado}"
    
    @property
    def subtotal(self):
        """Calcula el subtotal de esta línea"""
        return self.denominacion.valor * self.cantidad


class ReservaDenominacion(models.Model):
    """
    Representa la reserva de denominaciones en un tauser para una transacción.
    Las denominaciones reservadas no se descuentan del inventario, pero tampoco
    están disponibles para nuevas transacciones hasta que se liberen o confirmen.
    """
    ESTADO_CHOICES = [
        ('reservada', 'Reservada'),
        ('confirmada', 'Confirmada (Retirada)'),
        ('liberada', 'Liberada (Cancelada)'),
    ]
    
    transaccion = models.ForeignKey(
        Transaccion,
        on_delete=models.CASCADE,
        related_name='reservas_denominaciones',
        verbose_name='Transacción'
    )
    terminal = models.ForeignKey(
        Terminal,
        on_delete=models.PROTECT,
        related_name='reservas_denominaciones',
        verbose_name='Terminal'
    )
    inventario_denominacion = models.ForeignKey(
        InventarioDenominacionTerminal,
        on_delete=models.PROTECT,
        related_name='reservas',
        verbose_name='Inventario de Denominación'
    )
    cantidad_reservada = models.PositiveIntegerField(
        verbose_name='Cantidad Reservada',
        help_text='Cantidad de billetes reservados'
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='reservada',
        verbose_name='Estado'
    )
    fecha_reserva = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Reserva'
    )
    fecha_confirmacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Confirmación/Liberación'
    )
    
    class Meta:
        verbose_name = 'Reserva de Denominación'
        verbose_name_plural = 'Reservas de Denominaciones'
        ordering = ['-fecha_reserva']
        indexes = [
            models.Index(fields=['transaccion', 'estado']),
            models.Index(fields=['terminal', 'estado']),
        ]
    
    def __str__(self):
        return f"Reserva {self.id} - {self.cantidad_reservada}x {self.inventario_denominacion.denominacion} ({self.estado})"
    
    @property
    def valor_total_reservado(self):
        """Calcula el valor total reservado"""
        return self.inventario_denominacion.denominacion.valor * self.cantidad_reservada
    
    def confirmar_retiro(self):
        """Confirma el retiro y descuenta del inventario"""
        from django.utils import timezone
        
        if self.estado != 'reservada':
            raise ValueError(f"La reserva debe estar en estado 'reservada', no '{self.estado}'")
        
        # Descontar del inventario
        self.inventario_denominacion.descontar(self.cantidad_reservada)
        
        # Cambiar estado
        self.estado = 'confirmada'
        self.fecha_confirmacion = timezone.now()
        self.save()
    
    def liberar_reserva(self):
        """Libera la reserva sin descontar del inventario"""
        from django.utils import timezone
        
        if self.estado != 'reservada':
            raise ValueError(f"La reserva debe estar en estado 'reservada', no '{self.estado}'")
        
        # Solo cambiar estado, no tocar inventario
        self.estado = 'liberada'
        self.fecha_confirmacion = timezone.now()
        self.save()