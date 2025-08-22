# users/models.py
from django.db import models
from django.contrib.auth.models import User, Permission, Group
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    # Aquí puedes añadir campos adicionales
    is_cambista = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    email = models.EmailField(unique=True)



# El modelo Cliente representa a un cliente de tu negocio.
class Cliente(models.Model):
    # La relación ManyToManyField vincula a un cliente con múltiples usuarios.
    # El parámetro `through` indica que se utilizará el modelo 'AsignacionCliente'
    # para gestionar esta relación.

    usuarios = models.ManyToManyField(CustomUser, through='AsignacionCliente')

    cedula = models.CharField(max_length=20, unique=True, verbose_name="Cédula de Identidad")
    nombre_completo = models.CharField(max_length=255, verbose_name="Nombre Completo")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")


    tipo_cliente = models.CharField(max_length=50, verbose_name="Tipo de Cliente", default='minorista')

    def __str__(self):
        return self.nombre_completo


# El modelo AsignacionCliente es la tabla intermedia que gestiona la
# relación N:M entre User y Cliente.
# Aquí puedes añadir información adicional sobre la asignación.
class AsignacionCliente(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Esto asegura que una combinación de usuario y cliente solo pueda existir una vez.
        unique_together = ('usuario', 'cliente')
        verbose_name = "Asignación de Cliente"
        verbose_name_plural = "Asignaciones de Clientes"

    def __str__(self):
        return f"{self.usuario.username} asignado a {self.cliente.nombre_completo}"


