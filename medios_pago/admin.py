"""from django.contrib import admin
from .models import MedioDePago

@admin.register(MedioDePago)
class MedioDePagoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'comision_porcentaje', 'is_active', 'actualizado')
    list_filter = ('is_active', 'tipo')
    search_fields = ('nombre', 'tipo')
"""