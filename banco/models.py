# models.py
from django.db import models
import uuid
from django.core.exceptions import ValidationError

# --------- ENTIDAD BANCARIA ---------
class EntidadBancaria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=10, unique=True)
    color_principal = models.CharField(max_length=7, default="#1d3557")
    color_secundario = models.CharField(max_length=7, default="#457b9d")
    logo_url = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.nombre


# --------- USUARIO BANCARIO ---------
class BancoUser(models.Model):
    entidad = models.ForeignKey(
        EntidadBancaria,
        on_delete=models.CASCADE,
        related_name="usuarios",
        default=1
    )
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    def __str__(self):
        return f"{self.email} ({self.entidad.nombre})"


# --------- CUENTA CORRIENTE ---------
class Cuenta(models.Model):
    usuario = models.ForeignKey(
        BancoUser,
        on_delete=models.CASCADE,
        related_name="cuentas"
    )
    numero_cuenta = models.CharField(max_length=20, unique=True)
    entidad = models.ForeignKey(EntidadBancaria, on_delete=models.CASCADE)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.numero_cuenta} - {self.entidad.codigo}"


# --------- TRANSFERENCIA ---------
class Transferencia(models.Model):
    cuenta_origen = models.ForeignKey(
        Cuenta, on_delete=models.CASCADE, related_name="transferencias_enviadas"
    )
    cuenta_destino = models.ForeignKey(
        Cuenta, on_delete=models.CASCADE, related_name="transferencias_recibidas"
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    comprobante = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transferencia ₲{self.monto} - {self.comprobante}"


# --------- TARJETA DE DÉBITO ---------
class TarjetaDebito(models.Model):
    usuario = models.ForeignKey(BancoUser, on_delete=models.CASCADE, related_name="tarjetas_debito", null = True, blank = True)
    entidad = models.ForeignKey(EntidadBancaria, on_delete=models.CASCADE)
    cuenta = models.OneToOneField(Cuenta, on_delete=models.CASCADE, related_name="tarjeta_debito", null = True, blank = True)  
    numero = models.CharField(max_length=16, unique=True)
    mes_vencimiento = models.PositiveSmallIntegerField()
    anho_vencimiento = models.PositiveSmallIntegerField()
    cvv = models.CharField(max_length=3)

    def __str__(self):
        return f"Débito {self.numero[-4:]} ({self.entidad.codigo})"


# --------- TARJETA DE CRÉDITO ---------
class TarjetaCredito(models.Model):
    usuario = models.ForeignKey(BancoUser, on_delete=models.CASCADE, related_name="tarjetas_credito", null = True, blank = True)
    entidad = models.ForeignKey(EntidadBancaria, on_delete=models.CASCADE)
    numero = models.CharField(max_length=16, unique=True)
    mes_vencimiento = models.PositiveSmallIntegerField()
    anho_vencimiento = models.PositiveSmallIntegerField()
    cvv = models.CharField(max_length=3)
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, default=2000000)
    saldo_usado = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def disponible(self):
        return self.limite_credito - self.saldo_usado

    def __str__(self):
        return f"Crédito {self.numero[-4:]} ({self.entidad.codigo})"

# --------- PAGOS ---------
from django.core.exceptions import ValidationError

class PagoTarjeta(models.Model):
    tarjeta_debito = models.ForeignKey("TarjetaDebito", on_delete=models.SET_NULL, null=True, blank=True)
    tarjeta_credito = models.ForeignKey("TarjetaCredito", on_delete=models.SET_NULL, null=True, blank=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    comprobante = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Validación de integridad
        if not self.tarjeta_debito and not self.tarjeta_credito:
            raise ValidationError("Debe especificar una tarjeta de débito o crédito.")
        if self.tarjeta_debito and self.tarjeta_credito:
            raise ValidationError("No puede usar ambas tarjetas en un mismo pago.")

        # Pago con débito
        if self.tarjeta_debito:
            cuenta = self.tarjeta_debito.cuenta
            if cuenta.saldo < self.monto:
                raise ValidationError("Saldo insuficiente en cuenta corriente.")
            cuenta.saldo -= self.monto
            cuenta.save()

        # Pago con crédito
        if self.tarjeta_credito:
            if self.tarjeta_credito.disponible() < self.monto:
                raise ValidationError("Límite de crédito excedido.")
            self.tarjeta_credito.saldo_usado += self.monto
            self.tarjeta_credito.save()

        super().save(*args, **kwargs)

    def __str__(self):
        if self.tarjeta_debito:
            return f"Pago Débito ₲{self.monto} ({self.tarjeta_debito.numero[-4:]})"
        elif self.tarjeta_credito:
            return f"Pago Crédito ₲{self.monto} ({self.tarjeta_credito.numero[-4:]})"
        return f"Pago ₲{self.monto}"
