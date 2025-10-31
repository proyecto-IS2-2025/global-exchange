#divisas
from django.contrib import admin
from .models import Divisa, Denominacion, DesgloseDenominacion

@admin.register(Divisa)
class DivisaAdmin(admin.ModelAdmin):
    list_display = ('code', 'nombre', 'simbolo', 'is_active', 'actualizado')
    list_filter = ('is_active',)
    search_fields = ('code', 'nombre')
    ordering = ('code',)

@admin.register(Denominacion)
class DenominacionAdmin(admin.ModelAdmin):
    list_display = ['divisa', 'valor_sin_decimales', 'is_active', 'creado']
    list_filter = ['divisa', 'is_active']
    search_fields = ['divisa__code', 'valor']
    ordering = ['divisa', '-valor']
    
    def valor_sin_decimales(self, obj):
        """Muestra el valor sin decimales"""
        return obj.valor_formateado
    valor_sin_decimales.short_description = 'Valor'

@admin.register(DesgloseDenominacion)
class DesgloseDenominacionAdmin(admin.ModelAdmin):
    list_display = ['transaccion', 'denominacion', 'cantidad', 'subtotal']
    list_filter = ['denominacion__divisa']
    search_fields = ['transaccion__numero_transaccion']