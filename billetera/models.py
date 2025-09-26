# billetera/models.py
from django.db import models
from django.core.exceptions import ValidationError
import uuid
from decimal import Decimal

# Importar modelos del sistema bancario existente
from banco.models import EntidadBancaria, TarjetaDebito
from django.utils import timezone

class UsuarioBilletera(models.Model):
    numero_celular = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=128)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.numero_celular}"


class Billetera(models.Model):
    usuario = models.OneToOneField(
        UsuarioBilletera, 
        on_delete=models.CASCADE, 
        related_name="billetera"
    )
    entidad = models.ForeignKey(
        EntidadBancaria, 
        on_delete=models.CASCADE,
        related_name="billeteras", null=True, blank=True
    )
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Billetera {self.usuario.numero_celular} - {self.entidad.nombre}"

    class Meta:
        unique_together = ('usuario', 'entidad')


class MovimientoBilletera(models.Model):
    TIPO_MOVIMIENTO = [
        ('RECARGA', 'Recarga'),
        ('ENVIO', 'Envío'),
        ('RECEPCION', 'Recepción'),
    ]

    billetera = models.ForeignKey(
        Billetera, 
        on_delete=models.CASCADE, 
        related_name="movimientos"
    )
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.TextField(default="Sin descripción")
    comprobante = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    # Para envíos y recepciones
    billetera_destino = models.ForeignKey(
        Billetera, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="movimientos_recibidos"
    )

    def __str__(self):
        return f"{self.tipo} - ₲{self.monto} - {self.comprobante}"

    class Meta:
        ordering = ['-fecha']


class RecargaBilletera(models.Model):
    billetera = models.ForeignKey(
        Billetera, 
        on_delete=models.CASCADE, 
        related_name="recargas"
    )
    tarjeta_debito = models.ForeignKey(
        TarjetaDebito, 
        on_delete=models.CASCADE
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    comprobante = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)
    exitosa = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:  # Solo en creación
            # Verificar que la tarjeta existe y tiene saldo suficiente
            if not self.tarjeta_debito.cuenta:
                raise ValidationError("La tarjeta de débito no tiene cuenta asociada.")
            
            if self.tarjeta_debito.cuenta.saldo < self.monto:
                raise ValidationError("Saldo insuficiente en la tarjeta de débito.")
            
            # Realizar la transacción
            self.tarjeta_debito.cuenta.saldo -= self.monto
            self.tarjeta_debito.cuenta.save()
            
            self.billetera.saldo += self.monto
            self.billetera.save()
            
            self.exitosa = True
            
            # Crear movimiento en el historial
            MovimientoBilletera.objects.create(
                billetera=self.billetera,
                tipo='RECARGA',
                monto=self.monto,
                descripcion=f"Recarga desde tarjeta {self.tarjeta_debito.numero[-4:]}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Recarga ₲{self.monto} - {self.comprobante}"


class TransferenciaBilletera(models.Model):
    billetera_origen = models.ForeignKey(
        Billetera, 
        on_delete=models.CASCADE, 
        related_name="transferencias_enviadas"
    )
    billetera_destino = models.ForeignKey(
        Billetera, 
        on_delete=models.CASCADE, 
        related_name="transferencias_recibidas"
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    comprobante = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)
    exitosa = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:  # Solo en creación
            # Verificar saldo suficiente
            if self.billetera_origen.saldo < self.monto:
                raise ValidationError("Saldo insuficiente en la billetera de origen.")
            
            # Realizar la transferencia
            self.billetera_origen.saldo -= self.monto
            self.billetera_origen.save()
            
            self.billetera_destino.saldo += self.monto
            self.billetera_destino.save()
            
            self.exitosa = True
            
            # Crear movimientos en el historial
            MovimientoBilletera.objects.create(
                billetera=self.billetera_origen,
                tipo='ENVIO',
                monto=self.monto,
                descripcion=f"Envío a {self.billetera_destino.usuario.numero_celular}",
                billetera_destino=self.billetera_destino
            )
            
            MovimientoBilletera.objects.create(
                billetera=self.billetera_destino,
                tipo='RECEPCION',
                monto=self.monto,
                descripcion=f"Recepción de {self.billetera_origen.usuario.numero_celular}",
                billetera_destino=self.billetera_origen
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Transferencia ₲{self.monto} - {self.comprobante}"