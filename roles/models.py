from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType

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

class PermissionMetadata(models.Model):
    """
    Metadata adicional para permisos, permite categorizar y documentar.
    """
    
    MODULOS_CHOICES = [
        ('clientes', 'Gestión de Clientes'),
        ('divisas', 'Operaciones de Divisas'),
        ('medios_pago', 'Medios de Pago'),
        ('transacciones', 'Transacciones'),
        ('usuarios', 'Gestión de Usuarios'),
        ('reportes', 'Reportes y Exportaciones'),
        ('configuracion', 'Configuración del Sistema'),
    ]
    
    RIESGO_CHOICES = [
        ('bajo', 'Bajo - Solo lectura'),
        ('medio', 'Medio - Modificación de datos'),
        ('alto', 'Alto - Operaciones críticas'),
        ('critico', 'Crítico - Administración del sistema'),
    ]
    
    permission = models.OneToOneField(
        Permission,
        on_delete=models.CASCADE,
        related_name='metadata',
        help_text='Permiso de Django asociado'
    )
    
    modulo = models.CharField(
        max_length=50,
        choices=MODULOS_CHOICES,
        help_text='Módulo funcional al que pertenece'
    )
    
    descripcion_detallada = models.TextField(
        help_text='Explicación clara de qué permite hacer este permiso'
    )
    
    ejemplo_uso = models.TextField(
        blank=True,
        help_text='Ejemplo concreto de uso del permiso'
    )
    
    nivel_riesgo = models.CharField(
        max_length=20,
        choices=RIESGO_CHOICES,
        default='medio',
        help_text='Nivel de riesgo de seguridad'
    )
    
    orden = models.IntegerField(
        default=0,
        help_text='Orden para mostrar en interfaz'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['modulo', 'orden', 'permission__name']
        verbose_name = 'Metadata de Permiso'
        verbose_name_plural = 'Metadata de Permisos'
    
    def __str__(self):
        return f"{self.permission.name} ({self.get_modulo_display()})"


class PermissionChangeLog(models.Model):
    """
    Registro de auditoría de cambios en permisos de grupos.
    """
    grupo = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='permission_changes'
    )
    
    usuario = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        help_text='Usuario que realizó el cambio'
    )
    
    accion = models.CharField(
        max_length=20,
        choices=[
            ('add', 'Permiso agregado'),
            ('remove', 'Permiso removido'),
            ('update', 'Actualización masiva'),
        ]
    )
    
    permisos_modificados = models.JSONField(
        help_text='Lista de IDs de permisos modificados',
        default=list
    )
    
    fecha = models.DateTimeField(auto_now_add=True)
    
    observaciones = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Log de Cambio de Permisos'
        verbose_name_plural = 'Logs de Cambios de Permisos'
    
    def __str__(self):
        return f"{self.grupo.name} - {self.accion} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"