from django.db import models
from django.contrib.auth.models import AbstractUser, Group

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class RoleStatus(models.Model):
    """
    Modelo para gestionar el estado de los roles (Grupos).
    """
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='status')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Estado de {self.group.name}: {'Activo' if self.is_active else 'Inactivo'}"

