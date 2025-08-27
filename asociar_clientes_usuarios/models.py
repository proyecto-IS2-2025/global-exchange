# asociar_clientes_usuarios/models.py
from django.db import models
from users.models import CustomUser, Cliente

class AsignacionCliente(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'cliente')
        verbose_name = "Asignación de Cliente"
        verbose_name_plural = "Asignaciones de Clientes"

    def __str__(self):
        return f"{self.usuario.username} asignado a {self.cliente.nombre_completo}"