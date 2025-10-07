#operacion_divisas
from django import forms
from divisas.models import Divisa




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



from decimal import Decimal

class CompraDivisaForm(forms.Form):
    divisa = forms.ModelChoiceField(
        queryset=Divisa.objects.filter(is_active=True).exclude(code='PYG'),
        label="Divisa a comprar",
        empty_label="-- Seleccione divisa --",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'data-placeholder': 'Seleccione la divisa que desea comprar...'
        })
    )
    monto = forms.DecimalField(
        min_value=Decimal('0.00000001'),
        decimal_places=8,
        label="Monto en Guaraníes (Gs.)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingrese el monto en guaraníes que desea cambiar',
            'step': '1000',
            'min': '1000'
        }),
        help_text="Ingrese el monto en guaraníes que desea convertir a la divisa seleccionada"
    )