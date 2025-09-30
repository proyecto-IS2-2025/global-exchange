"""
Modelos para gestión de medios de pago de clientes.
"""
from django.db import models


class ClienteMedioDePago(models.Model):
    """Instancia específica de un medio de pago asociado a un cliente."""
    cliente = models.ForeignKey(
        'clientes.Cliente',
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
        """Verifica si todos los campos requeridos están completos."""
        if not self.medio_de_pago:
            return False
            
        campos_requeridos = self.medio_de_pago.campos.filter(
            is_required=True
        ).values_list('nombre_campo', flat=True)
        
        if not campos_requeridos:
            return True

        for nombre_campo in campos_requeridos:
            valor = self.datos_campos.get(nombre_campo)
            if not valor: 
                return False

        return True


class HistorialClienteMedioDePago(models.Model):
    """Historial de cambios en los medios de pago de clientes."""
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