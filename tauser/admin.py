from django.contrib import admin
from .models import (
    Terminal, RegistroTransaccionTerminal,
    InventarioDenominacionTerminal, DesgloseDenominacionOperacion
)

@admin.register(InventarioDenominacionTerminal)
class InventarioDenominacionTerminalAdmin(admin.ModelAdmin):
    list_display = [
        'terminal', 'denominacion', 'cantidad', 
        'cantidad_minima', 'necesita_reposicion', 
        'ultima_reposicion', 'actualizado'
    ]
    list_filter = [
        'terminal', 'denominacion__divisa', 
        'actualizado', 'ultima_reposicion'
    ]
    search_fields = [
        'terminal__nombre', 'terminal__codigo',
        'denominacion__nombre'
    ]
    readonly_fields = ['actualizado', 'creado', 'valor_total']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('terminal', 'denominacion')
        }),
        ('Inventario', {
            'fields': ('cantidad', 'cantidad_minima', 'valor_total')
        }),
        ('Reposición', {
            'fields': ('ultima_reposicion', 'actualizado_por')
        }),
        ('Auditoría', {
            'fields': ('creado', 'actualizado'),
            'classes': ('collapse',)
        }),
    )
    
    def necesita_reposicion(self, obj):
        return obj.necesita_reposicion
    necesita_reposicion.boolean = True
    necesita_reposicion.short_description = 'Requiere Reposición'


@admin.register(DesgloseDenominacionOperacion)
class DesgloseDenominacionOperacionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'registro_operacion', 'denominacion',
        'cantidad', 'tipo_movimiento', 'subtotal', 'creado'
    ]
    list_filter = [
        'tipo_movimiento', 'denominacion__divisa',
        'creado'
    ]
    search_fields = [
        'registro_operacion__id',
        'denominacion__nombre'
    ]
    readonly_fields = ['creado', 'subtotal']
    
    fieldsets = (
        ('Operación', {
            'fields': ('registro_operacion', 'tipo_movimiento')
        }),
        ('Denominación', {
            'fields': ('denominacion', 'cantidad', 'subtotal')
        }),
        ('Auditoría', {
            'fields': ('creado',),
            'classes': ('collapse',)
        }),
    )


# Actualizar el admin de RegistroTransaccionTerminal
class DesgloseDenominacionInline(admin.TabularInline):
    model = DesgloseDenominacionOperacion
    extra = 0
    readonly_fields = ['subtotal', 'creado']
    fields = ['denominacion', 'cantidad', 'tipo_movimiento', 'subtotal']


@admin.register(RegistroTransaccionTerminal)
class RegistroTransaccionTerminalAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'terminal', 'tipo_operacion', 'cliente',
        'divisa', 'monto_operacion', 'fue_exitoso'
    ]
    list_filter = [
        'tipo_operacion', 'fue_exitoso', 'terminal',
        'divisa'
    ]
    search_fields = [
        'cliente__nombre', 'cliente__apellido',
        'transaccion_original__id'
    ]
    inlines = [DesgloseDenominacionInline]
    
    fieldsets = (
        ('Información de la Operación', {
            'fields': (
                'terminal', 'tipo_operacion', 'cliente',
                'transaccion_original', 'pin_usado'
            )
        }),
        ('Detalles Financieros', {
            'fields': ('divisa', 'monto_operacion')
        }),
        ('Resultado', {
            'fields': ('fue_exitoso', 'mensaje_error')
        }),
        ('Auditoría', {
            'fields': ('fecha_operacion',),
            'classes': ('collapse',)
        }),
    )