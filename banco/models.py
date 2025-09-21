# banco/models.py
from django.db import models
import uuid

class BancoUser(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # lo guardamos en texto plano o hash simple

    def __str__(self):
        return self.email


class Cuenta(models.Model):
    usuario = models.OneToOneField(
        BancoUser,
        on_delete=models.CASCADE,
        related_name="cuenta"
    )
    numero_cuenta = models.CharField(max_length=20, unique=True)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.usuario.email} - {self.numero_cuenta}"


class Transferencia(models.Model):
    cuenta_origen = models.ForeignKey(
        Cuenta, on_delete=models.CASCADE, related_name="transferencias_enviadas"
    )
    cuenta_destino = models.ForeignKey(
        Cuenta, on_delete=models.CASCADE, related_name="transferencias_recibidas"
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    comprobante = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"{self.comprobante} - {self.cuenta_origen} → {self.cuenta_destino} (${self.monto})"
