from django.contrib import admin
from .models import Divisa

@admin.register(Divisa)
class DivisaAdmin(admin.ModelAdmin):
    list_display = ('code', 'nombre', 'simbolo', 'is_active', 'actualizado')
    list_filter = ('is_active',)
    search_fields = ('code', 'nombre')
    ordering = ('code',)
