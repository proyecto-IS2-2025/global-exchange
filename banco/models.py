# models.py
from django.db import models
import uuid

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

# --------- CUENTA BANCARIA ---------
class Cuenta(models.Model):
    # Definimos las opciones para el tipo de cuenta
    TIPO_CUENTA_CHOICES = [
        ('DEBITO', 'Débito'),
        ('CREDITO', 'Crédito'),
    ]

    usuario = models.ForeignKey(
        BancoUser,
        on_delete=models.CASCADE,
        related_name="cuentas"  # ¡Nueva relación inversa!
    )
    numero_cuenta = models.CharField(max_length=20, unique=True)
    entidad = models.ForeignKey(EntidadBancaria, on_delete=models.CASCADE)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tipo_cuenta = models.CharField(
        max_length=7,
        choices=TIPO_CUENTA_CHOICES,
        default='DEBITO'
    )

    def __str__(self):
        return f"{self.numero_cuenta} - {self.entidad.codigo} ({self.get_tipo_cuenta_display()})"

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
        return f"Transferencia de ₲{self.monto} - {self.comprobante}"

# --------- PAGO CON TARJETA ---------
class PagoTarjeta(models.Model):
    TIPO_CHOICES = [
        ('DEBITO', 'Débito'),
        ('CREDITO', 'Crédito'),
    ]
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name="pagos_con_tarjeta")
    tipo = models.CharField(max_length=7, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    comprobante = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago con {self.tipo} de ₲{self.monto} - {self.comprobante}"
# --------- TRANSFERENCIA RECIBIDA DESDE BILLETERA ---------
class TransferenciaRecibidaBilletera(models.Model):
    billetera_origen = models.CharField(max_length=20)  # Teléfono de la billetera
    cuenta_destino = models.ForeignKey(
        'Cuenta', on_delete=models.CASCADE, related_name="recargas_desde_billetera"
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    comprobante = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recarga de ₲{self.monto} desde Billetera {self.billetera_origen}"