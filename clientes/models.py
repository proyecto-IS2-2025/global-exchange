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
from django.core.validators import MinValueValidator, MaxValueValidator

from django.db import models
from users.models import CustomUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from medios_pago.models import MedioDePago, CampoMedioDePago  # ← Agregar esta línea
import json


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
    esta_activo = models.BooleanField(default=True, verbose_name="¿Activo?")
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

# Agregar al final de clientes/models.py si no están

# clientes/models.py - Método clean corregido para ClienteMedioDePago

class ClienteMedioDePago(models.Model):
    """
    Instancia específica de un medio de pago asociado a un cliente.
    Almacena los datos dinámicos según los campos definidos en MedioDePago.
    """
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.CASCADE,
        related_name='medios_pago'
    )
    medio_de_pago = models.ForeignKey(
        'medios_pago.MedioDePago',
        on_delete=models.CASCADE,
        limit_choices_to={'is_active': True}
    )
    datos_campos = models.JSONField(
        default=dict,
        help_text='Datos dinámicos según los campos del medio de pago'
    )
    es_activo = models.BooleanField(default=True)
    es_principal = models.BooleanField(
        default=False,
        help_text='Indica si es el medio de pago principal del cliente'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='medios_pago_creados'
    )

    class Meta:
        verbose_name = 'Medio de Pago del Cliente'
        verbose_name_plural = 'Medios de Pago de Clientes'
        # ELIMINAR: unique_together = ['cliente', 'medio_de_pago']
        ordering = ['-es_principal', '-fecha_actualizacion']


    def __str__(self):
        estado = "Principal" if self.es_principal else "Secundario"
        return f'{self.cliente.nombre_completo} - {self.medio_de_pago.nombre} ({estado})'

    def get_dato_campo(self, nombre_campo):
        """Obtener valor de un campo específico"""
        return self.datos_campos.get(nombre_campo, '')

    def set_dato_campo(self, nombre_campo, valor):
        """Establecer valor de un campo específico"""
        self.datos_campos[nombre_campo] = valor

    @property
    def campos_completos(self):
        """Verificar si todos los campos requeridos están completos"""
        try:
            self.clean()
            return True
        except ValidationError:
            return False

class HistorialClienteMedioDePago(models.Model):
    """
    Historial de cambios en los medios de pago de clientes
    """
    cliente_medio_pago = models.ForeignKey(
        ClienteMedioDePago,
        on_delete=models.CASCADE,
        related_name='historial'
    )
    accion = models.CharField(
        max_length=20,
        choices=[
            ('CREADO', 'Creado'),
            ('ACTUALIZADO', 'Actualizado'),
            ('DESACTIVADO', 'Desactivado'),
            ('ACTIVADO', 'Activado'),
        ]
    )
    datos_anteriores = models.JSONField(null=True, blank=True)
    datos_nuevos = models.JSONField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    modificado_por = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Historial de Medio de Pago'
        verbose_name_plural = 'Historial de Medios de Pago'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.cliente_medio_pago} - {self.accion} ({self.fecha.strftime("%Y-%m-%d %H:%M")})'



class LimiteDiario(models.Model):
    fecha = models.DateField(unique=True,help_text="Fecha a la que aplica el límite")
    monto = models.DecimalField(max_digits=20, decimal_places=2)
    inicio_vigencia = models.DateTimeField(help_text="Fecha y hora en que entra en vigencia el límite")

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Límite Diario {self.fecha}: {self.monto}"


class LimiteMensual(models.Model):
    mes = models.DateField( unique=True,help_text="Se guarda como el primer día del mes")
    monto = models.DecimalField(max_digits=15, decimal_places=2)
    inicio_vigencia = models.DateTimeField()
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-mes"]

    def __str__(self):
        return f"Límite Mensual {self.mes.strftime('%B %Y')}: {self.monto}"