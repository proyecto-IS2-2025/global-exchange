# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Segmento(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_cambista = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class Cliente(models.Model):
    usuarios = models.ManyToManyField(
        CustomUser, 
        through='asociar_clientes_usuarios.AsignacionCliente'
    )
    cedula = models.CharField(max_length=20, unique=True, verbose_name="Cédula de Identidad")
    nombre_completo = models.CharField(max_length=255, verbose_name="Nombre Completo")
    email = models.EmailField(blank=True, null=True, unique=True, verbose_name="Correo Electrónico")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    segmento = models.ForeignKey(Segmento, on_delete=models.SET_NULL, null=True, verbose_name="Segmento")
    tipo_cliente = models.CharField(max_length=50, verbose_name="Tipo de Cliente", default='minorista')

    def __str__(self):
        return self.nombre_completo