# users/models.py
from django.db import models
from django.contrib.auth.models import User

# El modelo Cliente representa a un cliente de tu negocio.
class Cliente(models.Model):
    # La relación ManyToManyField vincula a un cliente con múltiples usuarios.
    # El parámetro `through` indica que se utilizará el modelo 'AsignacionCliente'
    # para gestionar esta relación.
    usuarios = models.ManyToManyField(User, through='AsignacionCliente')

    cedula = models.CharField(max_length=20, unique=True, verbose_name="Cédula de Identidad")
    nombre_completo = models.CharField(max_length=255, verbose_name="Nombre Completo")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")

    def __str__(self):
        return self.nombre_completo

# El modelo AsignacionCliente es la tabla intermedia que gestiona la
# relación N:M entre User y Cliente.
# Aquí puedes añadir información adicional sobre la asignación.
class AsignacionCliente(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Esto asegura que una combinación de usuario y cliente solo pueda existir una vez.
        unique_together = ('usuario', 'cliente')
        verbose_name = "Asignación de Cliente"
        verbose_name_plural = "Asignaciones de Clientes"

    def __str__(self):
        return f"{self.usuario.username} asignado a {self.cliente.nombre_completo}"