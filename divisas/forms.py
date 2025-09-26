#divisas
from django import forms
from .models import Divisa, TasaCambio
"""
Formularios para la gestión de divisas y tasas de cambio.

Este módulo define formularios basados en modelos que validan y procesan
los datos de divisas y tasas de cambio con reglas adicionales.
"""

class DivisaForm(forms.ModelForm):
    """
    Formulario para crear o actualizar divisas.

    Valida y normaliza el código de la divisa, asegurando que quede en
    mayúsculas y sin espacios.
    """
    class Meta:
        model = Divisa
        fields = ['nombre', 'code', 'simbolo', 'decimales']
        widgets = {
            'decimales': forms.NumberInput(attrs={'min': 0, 'max': 8}),
        }

    def clean_code(self):
        """
        Normaliza el código de la divisa.

        :return: Código en mayúsculas y sin espacios.
        :rtype: str
        """
        return (self.cleaned_data.get('code') or '').upper().strip()

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
    
from decimal import Decimal

class VentaDivisaForm(forms.Form):
    divisa = forms.ModelChoiceField(
        queryset=Divisa.objects.filter(is_active=True).exclude(code='PYG'),
        label="Divisa a vender",
        empty_label="-- Seleccione divisa --"
    )
    monto = forms.DecimalField(
        min_value=Decimal('0.00000001'),
        decimal_places=8,
        label="Monto (en la divisa seleccionada)"
    )