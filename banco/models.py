# models.py
from django.db import models
import uuid
from django.core.exceptions import ValidationError

# --------- ENTIDAD BANCARIA ---------
class EntidadBancaria(models.Model):
    """
    Representa una entidad bancaria (banco) dentro del sistema.

    Esta clase almacena información de identificación y branding.

    :ivar nombre: Nombre comercial de la entidad.
    :vartype nombre: str
    :ivar codigo: Código corto de identificación de la entidad.
    :vartype codigo: str
    :ivar color_principal: Código hexadecimal para el color primario de la marca.
    :vartype color_principal: str
    :ivar color_secundario: Código hexadecimal para el color secundario de la marca.
    :vartype color_secundario: str
    :ivar logo_url: URL opcional del logo de la entidad.
    :vartype logo_url: str
    :ivar usuarios: Relación inversa (ForeignKey) desde :class:`~banco.models.BancoUser`.
    """
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=10, unique=True)
    color_principal = models.CharField(max_length=7, default="#1d3557")
    color_secundario = models.CharField(max_length=7, default="#457b9d")
    logo_url = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.nombre


# --------- USUARIO BANCARIO ---------
class BancoUser(models.Model):
    """
    Representa un usuario registrado en el sistema bancario.

    Este modelo actúa como el perfil de usuario bancario, vinculado a una :class:`~banco.models.EntidadBancaria`.

    :ivar entidad: La entidad bancaria a la que pertenece el usuario.
    :vartype entidad: :class:`~banco.models.EntidadBancaria`
    :ivar email: Correo electrónico único del usuario, usado para login.
    :vartype email: str
    :ivar password: Contraseña del usuario.
    :vartype password: str
    :ivar cuentas: Relación inversa (ForeignKey) desde :class:`~banco.models.Cuenta`.
    :ivar tarjetas_debito: Relación inversa (ForeignKey) desde :class:`~banco.models.TarjetaDebito`.
    :ivar tarjetas_credito: Relación inversa (ForeignKey) desde :class:`~banco.models.TarjetaCredito`.
    """
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
    """
    Modelo de cuenta corriente o de ahorros.

    Esta es la cuenta principal para transacciones y pagos.

    :ivar usuario: El usuario titular de la cuenta.
    :vartype usuario: :class:`~banco.models.BancoUser`
    :ivar numero_cuenta: Número de identificación único de la cuenta.
    :vartype numero_cuenta: str
    :ivar entidad: La entidad bancaria propietaria de la cuenta.
    :vartype entidad: :class:`~banco.models.EntidadBancaria`
    :ivar saldo: Monto actual disponible en la cuenta.
    :vartype saldo: :class:`django.db.models.DecimalField`
    :ivar transferencias_enviadas: Relación inversa (ForeignKey) desde :class:`~banco.models.Transferencia` (origen).
    :ivar transferencias_recibidas: Relación inversa (ForeignKey) desde :class:`~banco.models.Transferencia` (destino).
    :ivar tarjeta_debito: Relación inversa (OneToOneField) desde :class:`~banco.models.TarjetaDebito`.
    """
    usuario = models.ForeignKey(
        BancoUser,
        on_delete=models.CASCADE,
        related_name="cuentas"
    )
    numero_cuenta = models.CharField(max_length=20, unique=True)
    entidad = models.ForeignKey(EntidadBancaria, on_delete=models.CASCADE)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        """Retorna el número de cuenta y el código de la entidad."""
        return f"{self.numero_cuenta} - {self.entidad.codigo}"


# --------- TRANSFERENCIA ---------
class Transferencia(models.Model):
    """
    Registra una transferencia de fondos entre dos cuentas bancarias.

    :ivar cuenta_origen: La cuenta desde donde se envían los fondos.
    :vartype cuenta_origen: :class:`~banco.models.Cuenta`
    :ivar cuenta_destino: La cuenta que recibe los fondos.
    :vartype cuenta_destino: :class:`~banco.models.Cuenta`
    :ivar monto: Cantidad transferida.
    :vartype monto: :class:`django.db.models.DecimalField`
    :ivar comprobante: Identificador UUID único para el comprobante.
    :vartype comprobante: :class:`uuid.UUID`
    :ivar fecha: Fecha y hora en que se registró la transferencia.
    :vartype fecha: :class:`datetime.datetime`
    """
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
        """Retorna el monto y el comprobante de la transferencia."""
        return f"Transferencia ₲{self.monto} - {self.comprobante}"


# --------- TARJETA DE DÉBITO ---------
class TarjetaDebito(models.Model):
    """
    Representa una tarjeta de débito asociada a una cuenta.

    :ivar usuario: El usuario titular de la tarjeta.
    :vartype usuario: :class:`~banco.models.BancoUser`
    :ivar entidad: La entidad emisora.
    :vartype entidad: :class:`~banco.models.EntidadBancaria`
    :ivar cuenta: La cuenta a la que está vinculada la tarjeta (relación 1:1).
    :vartype cuenta: :class:`~banco.models.Cuenta`
    :ivar numero: Número de 16 dígitos de la tarjeta.
    :vartype numero: str
    :ivar mes_vencimiento: Mes de vencimiento (1-12).
    :vartype mes_vencimiento: int
    :ivar anho_vencimiento: Año de vencimiento.
    :vartype anho_vencimiento: int
    :ivar cvv: Código de seguridad de 3 dígitos.
    :vartype cvv: str
    """
    usuario = models.ForeignKey(BancoUser, on_delete=models.CASCADE, related_name="tarjetas_debito", null = True, blank = True)
    entidad = models.ForeignKey(EntidadBancaria, on_delete=models.CASCADE)
    cuenta = models.OneToOneField(Cuenta, on_delete=models.CASCADE, related_name="tarjeta_debito", null = True, blank = True)  
    numero = models.CharField(max_length=16, unique=True)
    mes_vencimiento = models.PositiveSmallIntegerField()
    anho_vencimiento = models.PositiveSmallIntegerField()
    cvv = models.CharField(max_length=3)

    def __str__(self):
        """Retorna los últimos 4 dígitos del número y el código de la entidad."""
        return f"Débito {self.numero[-4:]} ({self.entidad.codigo})"


# --------- TARJETA DE CRÉDITO ---------
class TarjetaCredito(models.Model):
    """
    Representa una tarjeta de crédito.

    :ivar usuario: El usuario titular de la tarjeta.
    :vartype usuario: :class:`~banco.models.BancoUser`
    :ivar entidad: La entidad emisora.
    :vartype entidad: :class:`~banco.models.EntidadBancaria`
    :ivar numero: Número de 16 dígitos de la tarjeta.
    :vartype numero: str
    :ivar mes_vencimiento: Mes de vencimiento (1-12).
    :vartype mes_vencimiento: int
    :ivar anho_vencimiento: Año de vencimiento.
    :vartype anho_vencimiento: int
    :ivar cvv: Código de seguridad de 3 dígitos.
    :vartype cvv: str
    :ivar limite_credito: Límite máximo de crédito.
    :vartype limite_credito: :class:`django.db.models.DecimalField`
    :ivar saldo_usado: Monto de crédito utilizado actualmente.
    :vartype saldo_usado: :class:`django.db.models.DecimalField`
    """
    usuario = models.ForeignKey(BancoUser, on_delete=models.CASCADE, related_name="tarjetas_credito", null = True, blank = True)
    entidad = models.ForeignKey(EntidadBancaria, on_delete=models.CASCADE)
    numero = models.CharField(max_length=16, unique=True)
    mes_vencimiento = models.PositiveSmallIntegerField()
    anho_vencimiento = models.PositiveSmallIntegerField()
    cvv = models.CharField(max_length=3)
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, default=2000000)
    saldo_usado = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def disponible(self):
        """
        Calcula el monto de crédito disponible (Límite - Saldo Usado).

        :returns: El crédito restante.
        :rtype: :class:`decimal.Decimal`
        """
        return self.limite_credito - self.saldo_usado

    def __str__(self):
        """Retorna los últimos 4 dígitos del número de tarjeta y el código de la entidad."""
        return f"Crédito {self.numero[-4:]} ({self.entidad.codigo})"

# --------- PAGOS ---------
from django.core.exceptions import ValidationError

class PagoTarjeta(models.Model):
    """
    Registra un pago realizado con tarjeta, que puede ser de débito o crédito.

    Este modelo implementa la lógica de verificación de saldo/límite y la actualización
    de saldos en el método :meth:`~banco.models.PagoTarjeta.save`.

    :ivar tarjeta_debito: Tarjeta de débito usada para el pago (excluyente con :attr:`tarjeta_credito`).
    :vartype tarjeta_debito: :class:`~banco.models.TarjetaDebito`
    :ivar tarjeta_credito: Tarjeta de crédito usada para el pago (excluyente con :attr:`tarjeta_debito`).
    :vartype tarjeta_credito: :class:`~banco.models.TarjetaCredito`
    :ivar monto: Monto del pago.
    :vartype monto: :class:`django.db.models.DecimalField`
    :ivar comprobante: Identificador UUID único para el comprobante.
    :vartype comprobante: :class:`uuid.UUID`
    :ivar fecha: Fecha y hora en que se registró el pago.
    :vartype fecha: :class:`datetime.datetime`
    """
    tarjeta_debito = models.ForeignKey("TarjetaDebito", on_delete=models.SET_NULL, null=True, blank=True)
    tarjeta_credito = models.ForeignKey("TarjetaCredito", on_delete=models.SET_NULL, null=True, blank=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    comprobante = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Sobreescribe el método save para ejecutar la lógica de pago.

        Realiza las siguientes validaciones y acciones antes de guardar:

        1.  Valida que se use una sola tarjeta (débito O crédito).
        2.  Si es débito: verifica saldo de la cuenta vinculada y lo decrementa.
        3.  Si es crédito: verifica el límite disponible y aumenta el saldo usado.

        :raises ValidationError: Si la selección de tarjeta es incorrecta, hay saldo insuficiente 
                                 o el límite de crédito es excedido.
        """
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
        """Retorna el tipo de pago (débito/crédito) y el monto."""
        if self.tarjeta_debito:
            return f"Pago Débito ₲{self.monto} ({self.tarjeta_debito.numero[-4:]})"
        elif self.tarjeta_credito:
            return f"Pago Crédito ₲{self.monto} ({self.tarjeta_credito.numero[-4:]})"
        return f"Pago ₲{self.monto}"
