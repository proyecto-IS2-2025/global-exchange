#divisas
from django import forms
from .models import Divisa, TasaCambio
"""
Formularios para la gestión de divisas y tasas de cambio.

Este módulo define formularios basados en modelos que validan y procesan
los datos de divisas y tasas de cambio con reglas adicionales.
"""

class DivisaForm(forms.ModelForm):
    class Meta:
        model = Divisa
        fields = ['nombre', 'code', 'simbolo', 'decimales']
        widgets = {
            'decimales': forms.NumberInput(attrs={'min': 0, 'max': 8}),
        }

    def clean_code(self):
        code = (self.cleaned_data.get('code') or '').upper().strip()
        
        # Bloquear creación con código PYG
        if code == 'PYG' and not self.instance.pk:
            raise forms.ValidationError(
                'El código PYG está reservado para la moneda base del sistema.'
            )
        
        # Bloquear cambio de código en PYG existente
        if self.instance.pk and self.instance.code == 'PYG' and code != 'PYG':
            raise forms.ValidationError(
                'No se puede cambiar el código de la moneda base.'
            )
        
        return code
# forms.py
class TasaCambioForm(forms.ModelForm):
    """
    Formulario para crear o actualizar tasas de cambio.

    Aplica reglas de validación para garantizar que los valores sean positivos
    y asocia la tasa a una divisa.
    """
    class Meta:
        model = TasaCambio
        fields = ['precio_base', 'comision_compra', 'comision_venta']  # sin fecha
        widgets = {
            'precio_base': forms.NumberInput(attrs={'step': '0.00000001', 'min': '0'}),
            'comision_compra': forms.NumberInput(attrs={'step': '0.00000001', 'min': '0'}),
            'comision_venta': forms.NumberInput(attrs={'step': '0.00000001', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario con la divisa proporcionada.

        :param divisa: La divisa asociada al formulario.
        :type divisa: Divisa
        """
        self.divisa = kwargs.pop('divisa', None)
        super().__init__(*args, **kwargs)
        if self.divisa:
            self.instance.divisa = self.divisa

    # Reglas: valores numéricos absolutos > 0
    def clean_precio_base(self):
        """
        Valida que el precio base sea mayor que 0.
        """
        v = self.cleaned_data.get('precio_base')
        if v is not None and v <= 0:
            raise forms.ValidationError('El precio base debe ser mayor a 0.')
        return v

    def clean_comision_compra(self):
        """
        Valida que la comisión de compra sea mayor que 0.
        """
        v = self.cleaned_data.get('comision_compra')
        if v is not None and v <= 0:
            raise forms.ValidationError('La comisión de compra debe ser mayor a 0.')
        return v

    def clean_comision_venta(self):
        """
        Valida que la comisión de venta sea mayor que 0.
        """
        v = self.cleaned_data.get('comision_venta')
        if v is not None and v <= 0:
            raise forms.ValidationError('La comisión de venta debe ser mayor a 0.')
        return v
    


"""""""""
# divisas/migrations/0004_crear_moneda_base_pyg.py
from django.db import migrations

def crear_pyg(apps, schema_editor):
    
    Crea o actualiza la moneda base PYG.
    Divisa = apps.get_model('divisas', 'Divisa')
    
    try:
        pyg = Divisa.objects.get(code='PYG')
        pyg.nombre = 'Guaraní'
        pyg.simbolo = '₲'
        pyg.is_active = True
        pyg.decimales = 0
        pyg.es_moneda_base = True
        pyg.save()
    except Divisa.DoesNotExist:
        Divisa.objects.create(
            code='PYG',
            nombre='Guaraní',
            simbolo='₲',
            is_active=True,
            decimales=0,
            es_moneda_base=True,
        )

def revertir_pyg(apps, schema_editor):
    Eliminar PYG (solo para desarrollo)
    Divisa = apps.get_model('divisas', 'Divisa')
    Divisa.objects.filter(code='PYG').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('divisas', '0003_divisa_es_moneda_base_and_more'),  # ⭐ Cambiar aquí
    ]

    operations = [
        migrations.RunPython(crear_pyg, revertir_pyg),
    ]''''"""