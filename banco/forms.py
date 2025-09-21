from django import forms
from .models import Transferencia

class TransferenciaForm(forms.Form):
    numero_cuenta_destino = forms.CharField(
        label="Número de cuenta destino",
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "Ej: CUENTA002", "class": "form-control"})
    )
    monto = forms.DecimalField(
        label="Monto a transferir",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
