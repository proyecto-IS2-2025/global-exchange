from django.conf import settings
from django.db import models

class Cliente(models.Model):
    usuarios = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='AsignacionCliente',
        related_name='nueva_app_clientes'
    )
    cedula = models.CharField(max_length=20, unique=True, verbose_name="Cédula de Identidad")
    nombre_completo = models.CharField(max_length=255, verbose_name="Nombre Completo")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    tipo_cliente = models.CharField(max_length=50, verbose_name="Tipo de Cliente", default='minorista')

    def __str__(self):
        return self.nombre_completo


class AsignacionCliente(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='nueva_app_asignaciones'
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'cliente')
        verbose_name = "Asignación de Cliente"
        verbose_name_plural = "Asignaciones de Clientes"

    def __str__(self):
        return f"{self.usuario} asignado a {self.cliente.nombre_completo}"
