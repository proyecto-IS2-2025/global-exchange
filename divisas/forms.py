from django import forms
from .models import Divisa, TasaCambio


class DivisaForm(forms.ModelForm):
    class Meta:
        model = Divisa
        fields = ['nombre', 'code', 'simbolo', 'decimales']
        widgets = {
            'decimales': forms.NumberInput(attrs={'min': 0, 'max': 8}),
        }

    def clean_code(self):
        return (self.cleaned_data.get('code') or '').upper().strip()

# forms.py
class TasaCambioForm(forms.ModelForm):
    class Meta:
        model = TasaCambio
        fields = ['precio_base', 'comision_compra', 'comision_venta']  # sin fecha
        widgets = {
            'precio_base': forms.NumberInput(attrs={'step': '0.00000001', 'min': '0'}),
            'comision_compra': forms.NumberInput(attrs={'step': '0.00000001', 'min': '0'}),
            'comision_venta': forms.NumberInput(attrs={'step': '0.00000001', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        self.divisa = kwargs.pop('divisa', None)
        super().__init__(*args, **kwargs)
        if self.divisa:
            self.instance.divisa = self.divisa

    # Reglas: valores numéricos absolutos > 0
    def clean_precio_base(self):
        v = self.cleaned_data.get('precio_base')
        if v is not None and v <= 0:
            raise forms.ValidationError('El precio base debe ser mayor a 0.')
        return v

    def clean_comision_compra(self):
        v = self.cleaned_data.get('comision_compra')
        if v is not None and v <= 0:
            raise forms.ValidationError('La comisión de compra debe ser mayor a 0.')
        return v

    def clean_comision_venta(self):
        v = self.cleaned_data.get('comision_venta')
        if v is not None and v <= 0:
            raise forms.ValidationError('La comisión de venta debe ser mayor a 0.')
        return v