"""
Módulos de modelos para la gestión de clientes y usuarios.

Este módulo define las estructuras de datos principales para la aplicación de
gestión de clientes, incluyendo modelos para Segmento, Cliente y AsignacionCliente.
Estos modelos establecen las relaciones y campos necesarios para almacenar la
información de los clientes, sus asignaciones a usuarios del sistema y la
categorización por segmentos.
"""

from django.db import models
from users.models import CustomUser

class Segmento(models.Model):
    """
    Modelo que representa un segmento de clientes.

    Un segmento es una categoría utilizada para agrupar clientes con características
    similares. Por ejemplo, "Minorista", "Mayorista", "Corporativo", etc.

    :param name: Nombre único del segmento.
    :type name: str
    """
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        """
        Representación en cadena del objeto Segmento.

        :return: El nombre del segmento.
        :rtype: str
        """
        return self.name

class Cliente(models.Model):
    """
    Modelo que representa a un cliente.

    Define los atributos principales de un cliente, como su información personal,
    contacto y la relación con los usuarios del sistema a través del modelo
    `AsignacionCliente`. También incluye la relación con el modelo `Segmento`
    para categorización.

    :param usuarios: Relación Many-to-Many con el modelo `CustomUser`.
    :type usuarios: django.db.models.ManyToManyField
    :param cedula: Cédula de identidad del cliente (única).
    :type cedula: str
    :param nombre_completo: Nombre completo del cliente.
    :type nombre_completo: str
    :param email: Correo electrónico del cliente (opcional y único).
    :type email: str
    :param direccion: Dirección del cliente (opcional).
    :type direccion: str
    :param telefono: Número de teléfono del cliente (opcional).
    :type telefono: str
    :param segmento: Segmento al que pertenece el cliente.
    :type segmento: django.db.models.ForeignKey
    :param tipo_cliente: Tipo de cliente (por defecto 'minorista').
    :type tipo_cliente: str
    """
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

    def __str__(self):
        """
        Representación en cadena del objeto Cliente.

        :return: El nombre completo del cliente.
        :rtype: str
        """
        return self.nombre_completo

    class Meta:
        """
        Metaclase para opciones adicionales del modelo Cliente.
        """
        #permissions = [
        #    ("view_cliente", "Puede ver clientes"),
        #    ("add_cliente", "Puede agregar clientes"),
        #    ("change_cliente", "Puede editar clientes"),
        #    ("delete_cliente", "Puede eliminar clientes"),
        #]


class AsignacionCliente(models.Model):
    """
    Modelo intermedio que gestiona la asignación de un cliente a un usuario.

    Este modelo se utiliza en la relación Many-to-Many entre `CustomUser` y `Cliente`.
    Almacena la fecha en que se realizó la asignación.

    :param usuario: El usuario al que se le asigna el cliente.
    :type usuario: django.db.models.ForeignKey
    :param cliente: El cliente asignado.
    :type cliente: django.db.models.ForeignKey
    :param fecha_asignacion: La fecha y hora de la asignación. Se establece automáticamente al crear.
    :type fecha_asignacion: datetime.datetime
    """
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        Metaclase para opciones adicionales del modelo AsignacionCliente.
        """
        unique_together = ('usuario', 'cliente')
        verbose_name = "Asignación de Cliente"
        verbose_name_plural = "Asignaciones de Clientes"

    def __str__(self):
        """
        Representación en cadena del objeto AsignacionCliente.

        :return: Una cadena que describe la asignación.
        :rtype: str
        """
        return f"{self.usuario.username} asignado a {self.cliente.nombre_completo}"
