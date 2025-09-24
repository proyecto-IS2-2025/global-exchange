# billetera/models.py
from django.db import models
import uuid
# Importamos la librería de encriptación de contraseñas de Django
from django.contrib.auth.hashers import make_password, check_password
from banco.models import Cuenta

# --------- USUARIO DE BILLETERA ---------
class BilleteraUser(models.Model):
    numero_telefono = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.numero_telefono
    
    # Sobreescribimos el método save() para hashear la contraseña
    def save(self, *args, **kwargs):
        # Hasheamos la contraseña si no ha sido hasheada todavía
        if not self.password.startswith(('pbkdf2_sha256$', 'bcrypt$')):
            self.password = make_password(self.password)
        super(BilleteraUser, self).save(*args, **kwargs)

# --------- BILLETERA ELECTRONICA ---------
class Billetera(models.Model):
    usuario = models.OneToOneField(BilleteraUser, on_delete=models.CASCADE, related_name="billetera")
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Billetera de {self.usuario.numero_telefono}"

# --------- TRANSFERENCIA DE BILLETERA A BANCO ---------
class TransferenciaBilleteraABanco(models.Model):
    billetera_origen = models.ForeignKey(Billetera, on_delete=models.CASCADE, related_name="transferencias_billetera_enviadas")
    cuenta_destino = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name="transferencias_billetera_recibidas")
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    comprobante = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"Transferencia de ₲{self.monto} a {self.cuenta_destino.numero_cuenta} ({self.comprobante})"
