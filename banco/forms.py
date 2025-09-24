# forms.py
from django import forms
from .models import EntidadBancaria, Cuenta

class TransferenciaForm(forms.Form):
    TIPO_PAGO_CHOICES = [
        ('TRANSFERENCIA', 'Transferencia bancaria'),
        ('PAGO_DEBITO', 'Pago con tarjeta de débito'),
        ('PAGO_CREDITO', 'Pago con tarjeta de crédito'),
    ]

    tipo_pago = forms.ChoiceField(
        choices=TIPO_PAGO_CHOICES,
        label="Tipo de Pago",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    
    # Campo eliminado: cuenta_origen ya no es necesario
    # El tipo de cuenta se determina por el tipo_pago seleccionado
    
    entidad_destino = forms.ModelChoiceField(
        queryset=EntidadBancaria.objects.all(),
        label="Entidad bancaria destino",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    numero_cuenta_destino = forms.CharField(
        label="Número de cuenta destino",
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "Ej: CUENTA002", "class": "form-control"})
    )
    monto = forms.DecimalField(
        label="Monto",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        return monto