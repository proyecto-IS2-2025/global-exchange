from django.contrib import admin
from .models import RegistroGanancia, ResumenGananciaDiaria, ResumenGananciaMensual


@admin.register(RegistroGanancia)
class RegistroGananciaAdmin(admin.ModelAdmin):
    list_display = ['transaccion', 'tipo_ganancia', 'monto_comision', 'monto_spread', 
                    'monto_total', 'divisa_referencia', 'fecha_transaccion']
    list_filter = ['tipo_ganancia', 'divisa_referencia', 'fecha_transaccion']
    search_fields = ['transaccion__numero_transaccion', 'notas']
    readonly_fields = ['fecha_registro', 'monto_total']
    date_hierarchy = 'fecha_transaccion'
    
    fieldsets = (
        ('Información de la Transacción', {
            'fields': ('transaccion', 'fecha_transaccion', 'divisa_referencia')
        }),
        ('Detalles de Ganancia', {
            'fields': ('tipo_ganancia', 'monto_comision', 'porcentaje_comision', 
                      'monto_spread', 'monto_total')
        }),
        ('Información Adicional', {
            'fields': ('notas', 'fecha_registro'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ResumenGananciaDiaria)
class ResumenGananciaDiariaAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'total_comisiones', 'total_spread', 'total_general', 
                    'cantidad_transacciones', 'ultima_actualizacion']
    list_filter = ['fecha']
    readonly_fields = ['ultima_actualizacion']
    date_hierarchy = 'fecha'
    
    def has_add_permission(self, request):
        return False


@admin.register(ResumenGananciaMensual)
class ResumenGananciaMensualAdmin(admin.ModelAdmin):
    list_display = ['get_periodo', 'total_comisiones', 'total_spread', 'total_general', 
                    'cantidad_transacciones', 'promedio_diario', 'ultima_actualizacion']
    list_filter = ['año', 'mes']
    readonly_fields = ['ultima_actualizacion']
    
    def get_periodo(self, obj):
        return f"{obj.mes:02d}/{obj.año}"
    get_periodo.short_description = 'Período'
    
    def has_add_permission(self, request):
        return False
