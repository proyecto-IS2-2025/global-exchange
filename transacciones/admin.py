from django.contrib import admin
from .models import Transaccion, HistorialTransaccion, ConfiguracionTransaccion


@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ('numero_transaccion', 'tipo_operacion', 'cliente', 'estado', 'tauser_code', 'tauser_terminal', 'monto_origen', 'monto_destino', 'fecha_creacion')
    list_filter = ('tipo_operacion', 'estado', 'fecha_creacion')
    search_fields = ('numero_transaccion', 'tauser_code', 'cliente__nombre', 'cliente__apellido')
    readonly_fields = ('numero_transaccion', 'tauser_code', 'fecha_creacion', 'fecha_actualizacion')
    list_select_related = ('cliente', 'tauser_terminal', 'divisa_origen', 'divisa_destino')
    
    def get_fieldsets(self, request, obj=None):
        """
        Retorna fieldsets dinámicos según si el usuario es staff/admin
        """
        fieldsets = [
            ('Información Básica', {
                'fields': ('numero_transaccion', 'tipo_operacion', 'estado', 'cliente')
            }),
            ('Divisas y Montos', {
                'fields': ('divisa_origen', 'monto_origen', 'divisa_destino', 'monto_destino', 'tasa_de_cambio_aplicada')
            }),
            ('TAUSER', {
                'fields': ('tauser_code', 'tauser_terminal'),
                'description': 'Información del terminal TAUSER asignado para el retiro (solo compras)'
            }),
            ('Medio de Pago', {
                'fields': ('medio_pago_datos',)
            }),
            ('Información Adicional', {
                'fields': ('observaciones', 'observacion', 'procesado_por', 'fecha_creacion', 'fecha_actualizacion')
            }),
        ]
        
        # Solo mostrar análisis de ganancias a administradores y superusuarios
        if request.user.is_superuser or request.user.groups.filter(name='admin').exists():
            fieldsets.insert(3, (
                'Análisis de Ganancias (Solo Administradores)', {
                    'fields': ('tasa_base', 'margen_spread', 'porcentaje_comision', 'comision_aplicada'),
                    'classes': ('collapse',),
                    'description': 'Información detallada de costos y márgenes para análisis de rentabilidad'
                }
            ))
        
        return fieldsets


@admin.register(HistorialTransaccion)
class HistorialTransaccionAdmin(admin.ModelAdmin):
    list_display = ('transaccion', 'estado_anterior', 'estado_nuevo', 'fecha_cambio', 'modificado_por')
    list_filter = ('estado_nuevo', 'fecha_cambio')
    search_fields = ('transaccion__numero_transaccion',)
    readonly_fields = ('fecha_cambio',)


@admin.register(ConfiguracionTransaccion)
class ConfiguracionTransaccionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'valor', 'fecha_modificacion', 'modificado_por')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_modificacion',)
