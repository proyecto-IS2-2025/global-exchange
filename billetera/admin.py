# billetera/admin.py
from django.contrib import admin
from .models import (
    UsuarioBilletera, Billetera, MovimientoBilletera, 
    RecargaBilletera, TransferenciaBilletera
)


@admin.register(UsuarioBilletera)
class UsuarioBilleteraAdmin(admin.ModelAdmin):
    list_display = ['numero_celular', 'nombre', 'apellido', 'fecha_registro']
    search_fields = ['numero_celular', 'nombre', 'apellido']
    list_filter = ['fecha_registro']
    readonly_fields = ['fecha_registro']

    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'numero_celular')
        }),
        ('Acceso', {
            'fields': ('password',)
        }),
        ('Metadata', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Billetera)
class BilleteraAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'entidad', 'saldo', 'activa', 'fecha_creacion']
    search_fields = ['usuario__numero_celular', 'usuario__nombre', 'entidad__nombre']
    list_filter = ['entidad', 'activa', 'fecha_creacion']
    readonly_fields = ['fecha_creacion']

    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'entidad')
        }),
        ('Saldo', {
            'fields': ('saldo',)
        }),
        ('Estado', {
            'fields': ('activa',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['usuario', 'entidad']
        return self.readonly_fields


@admin.register(MovimientoBilletera)
class MovimientoBilleteraAdmin(admin.ModelAdmin):
    list_display = ['billetera', 'tipo', 'monto', 'fecha', 'comprobante']
    search_fields = ['billetera__usuario__numero_celular', 'comprobante', 'descripcion']
    list_filter = ['tipo', 'fecha', 'billetera__entidad']
    readonly_fields = ['comprobante', 'fecha']

    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('billetera', 'tipo', 'monto', 'descripcion')
        }),
        ('Transferencia', {
            'fields': ('billetera_destino',),
            'description': 'Solo para movimientos de transferencia'
        }),
        ('Metadata', {
            'fields': ('comprobante', 'fecha'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False  # No permitir crear movimientos manualmente

    def has_change_permission(self, request, obj=None):
        return False  # No permitir editar movimientos

    def has_delete_permission(self, request, obj=None):
        return False  # No permitir eliminar movimientos


@admin.register(RecargaBilletera)
class RecargaBilleteraAdmin(admin.ModelAdmin):
    list_display = ['billetera', 'monto', 'exitosa', 'fecha', 'comprobante']
    search_fields = ['billetera__usuario__numero_celular', 'comprobante']
    list_filter = ['exitosa', 'fecha', 'billetera__entidad']
    readonly_fields = ['comprobante', 'fecha', 'exitosa']

    fieldsets = (
        ('Información de la Recarga', {
            'fields': ('billetera', 'tarjeta_debito', 'monto')
        }),
        ('Estado', {
            'fields': ('exitosa',)
        }),
        ('Metadata', {
            'fields': ('comprobante', 'fecha'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False  # Las recargas se crean desde la interfaz web

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TransferenciaBilletera)
class TransferenciaBilleteraAdmin(admin.ModelAdmin):
    list_display = ['billetera_origen', 'billetera_destino', 'monto', 'exitosa', 'fecha']
    search_fields = [
        'billetera_origen__usuario__numero_celular',
        'billetera_destino__usuario__numero_celular',
        'comprobante'
    ]
    list_filter = ['exitosa', 'fecha']
    readonly_fields = ['comprobante', 'fecha', 'exitosa']

    fieldsets = (
        ('Información de la Transferencia', {
            'fields': ('billetera_origen', 'billetera_destino', 'monto')
        }),
        ('Estado', {
            'fields': ('exitosa',)
        }),
        ('Metadata', {
            'fields': ('comprobante', 'fecha'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False  # Las transferencias se crean desde la interfaz web

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False