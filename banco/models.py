from django.db import models
import uuid

# --------- ENTIDAD BANCARIA ---------
class EntidadBancaria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=10, unique=True)  # Ej: BAN001
    color_principal = models.CharField(max_length=7, default="#1d3557")  # Código hexadecimal
    color_secundario = models.CharField(max_length=7, default="#457b9d")  # Código hexadecimal
    logo_url = models.CharField(max_length=200, blank=True, null=True)  # URL o path a logo

    def __str__(self):
        return self.nombre
    
# --------- USUARIO BANCARIO ---------
class BancoUser(models.Model):
    entidad = models.ForeignKey(
        EntidadBancaria,
        on_delete=models.CASCADE,
        related_name="usuarios",
        default=1  # ✅ valor por defecto para registros existentes
    )
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # En producción usar hash seguro

    def __str__(self):
        return f"{self.email} ({self.entidad.nombre})"

# --------- CUENTA BANCARIA ---------
class Cuenta(models.Model):
    entidad = models.ForeignKey(
        EntidadBancaria,
        on_delete=models.CASCADE,
        related_name="cuentas",
        default=1  # ✅ valor por defecto para registros existentes
    )
    usuario = models.OneToOneField(BancoUser, on_delete=models.CASCADE, related_name="cuenta")
    numero_cuenta = models.CharField(max_length=20, unique=True)
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
    fecha = models.DateTimeField(auto_now_add=True)
    comprobante = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"{self.comprobante} - {self.cuenta_origen} → {self.cuenta_destino} (${self.monto})"
