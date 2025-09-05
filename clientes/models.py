from django.db import models
from users.models import CustomUser
from django.core.validators import MinValueValidator, MaxValueValidator

class Segmento(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Cliente(models.Model):
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
    permissions = [
        ("view_cliente", "Puede ver clientes"),
        ("add_cliente", "Puede agregar clientes"),
        ("change_cliente", "Puede editar clientes"),
        ("delete_cliente", "Puede eliminar clientes"),
    ]

class AsignacionCliente(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'cliente')
        verbose_name = "Asignación de Cliente"
        verbose_name_plural = "Asignaciones de Clientes"

    def __str__(self):
        return f"{self.usuario.username} asignado a {self.cliente.nombre_completo}"

# Nuevo modelo para las descuentos, relacionado con el Segmento
class Descuento(models.Model):
    segmento = models.OneToOneField(
        'Segmento',
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name="Segmento de Cliente"
    )
    porcentaje_descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)],
        verbose_name="Descuento aplicado (%)"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Modificación"
    )
    modificado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Modificado por"
    )

    class Meta:
        verbose_name = "Descuento"
        verbose_name_plural = "Descuentos"

    def __str__(self):
        return f"Descuento para {self.segmento.name}"
    
class HistorialDescuentos(models.Model):
    descuento = models.ForeignKey(Descuento, on_delete=models.CASCADE, verbose_name="Descuento")
    porcentaje_descuento_anterior = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Descuento anterior (%)")
    porcentaje_descuento_nuevo = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Nuevo descuento (%)")
    fecha_cambio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Cambio")
    modificado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Modificado por"
    )

    class Meta:
        verbose_name = "Historial de Descuento"
        verbose_name_plural = "Historial de Descuentos"
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"Cambio en descuento de {self.descuento.segmento.name} el {self.fecha_cambio.strftime('%Y-%m-%d')}"