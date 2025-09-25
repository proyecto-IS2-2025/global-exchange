# transacciones/models.py
from django.db import models
from clientes.models import Cliente
from divisas.models import Divisa

class Transaccion(models.Model):
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_PAGADA = 'pagada'
    ESTADO_CANCELADA = 'cancelada'
    
    ESTADOS_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_PAGADA, 'Pagada'),
        (ESTADO_CANCELADA, 'Cancelada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    divisa_origen = models.ForeignKey(Divisa, related_name='transacciones_origen', on_delete=models.CASCADE)
    divisa_destino = models.ForeignKey(Divisa, related_name='transacciones_destino', on_delete=models.CASCADE)
    monto_origen = models.DecimalField(max_digits=15, decimal_places=2)
    monto_destino = models.DecimalField(max_digits=15, decimal_places=2)
    tasa_de_cambio_aplicada = models.DecimalField(max_digits=10, decimal_places=4)
    estado = models.CharField(max_length=10, choices=ESTADOS_CHOICES, default=ESTADO_PENDIENTE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transacción #{self.id} - {self.cliente}"
