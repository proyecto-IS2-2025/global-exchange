from django.contrib import admin
from .models import (
    Terminal, 
    InventarioDivisaTerminal, 
    PINTerminalCliente, 
    RegistroTransaccionTerminal
)

@admin.register(Terminal)
class TerminalAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'ubicacion', 'is_activa', 'usuario_responsable']
    list_filter = ['is_activa', 'ubicacion']
    search_fields = ['nombre', 'codigo', 'ubicacion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']

@admin.register(InventarioDivisaTerminal)
class InventarioDivisaTerminalAdmin(admin.ModelAdmin):
    list_display = ['terminal', 'divisa', 'cantidad', 'cantidad_minima', 'necesita_reposicion', 'ultima_actualizacion']
    list_filter = ['terminal', 'divisa']
    search_fields = ['terminal__nombre', 'divisa__code']
    readonly_fields = ['ultima_actualizacion']

@admin.register(PINTerminalCliente)
class PINTerminalClienteAdmin(admin.ModelAdmin):
    list_display = ['pin', 'cliente', 'fecha_generacion', 'fecha_expiracion', 'usado', 'esta_vigente']
    list_filter = ['usado', 'fecha_generacion', 'terminal_usada']
    search_fields = ['pin', 'cliente__nombre_completo', 'cliente__cedula']
    readonly_fields = ['fecha_generacion', 'fecha_uso']

@admin.register(RegistroTransaccionTerminal)
class RegistroTransaccionTerminalAdmin(admin.ModelAdmin):
    list_display = ['terminal', 'cliente', 'tipo_operacion', 'divisa', 'monto_operacion', 'fue_exitoso', 'fecha_operacion']
    list_filter = ['fue_exitoso', 'tipo_operacion', 'terminal', 'fecha_operacion']
    search_fields = ['cliente__nombre_completo', 'transaccion_original__numero_transaccion']
    readonly_fields = ['fecha_operacion']