from django import forms
from .models import EntidadBancaria

class TransferenciaForm(forms.Form):
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
        label="Monto a transferir",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        return monto
