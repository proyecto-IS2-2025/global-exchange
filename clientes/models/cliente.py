"""
Modelos principales de clientes y segmentos.
"""
from django.db import models
from users.models import CustomUser


class Segmento(models.Model):
    """Modelo que representa un segmento de clientes."""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Cliente(models.Model):
    """Modelo que representa a un cliente."""
    usuarios = models.ManyToManyField(
        CustomUser, 
        through='clientes.AsignacionCliente'
    )
    cedula = models.CharField(max_length=20, unique=True, verbose_name="Cédula de Identidad")
    nombre_completo = models.CharField(max_length=255, verbose_name="Nombre Completo")
    email = models.EmailField(blank=True, null=True, unique=True, verbose_name="Correo Electrónico")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    segmento = models.ForeignKey(Segmento, on_delete=models.SET_NULL, null=True, verbose_name="Segmento")
    tipo_cliente = models.CharField(max_length=50, verbose_name="Tipo de Cliente", default='minorista')
    esta_activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    def __str__(self):
        return self.nombre_completo

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class AsignacionCliente(models.Model):
    """Modelo intermedio para la asignación cliente-usuario."""
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'cliente')
        verbose_name = "Asignación de Cliente"
        verbose_name_plural = "Asignaciones de Clientes"

    def __str__(self):
        return f"{self.usuario.username} asignado a {self.cliente.nombre_completo}"