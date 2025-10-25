# autenticacion/models.py

from django.db import models
from django.conf import settings

class PerfilUsuario(models.Model):
    # ¡CAMBIO CLAVE! Esto resuelve el conflicto de nombres.
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='perfil_auth'  # <--- Nombre único para la app 'autenticacion'
    ) 
    nombre_completo = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)

    def __str__(self):
        return self.usuario.get_username()