# forms.py
from django import forms
from .models import EntidadBancaria, Cuenta

class TransferenciaForm(forms.Form):
    entidad_destino = forms.ModelChoiceField(
        queryset=EntidadBancaria.objects.all(),
        label="Banco destino",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    numero_cuenta_destino = forms.CharField(
        max_length=20,
        label="Número de cuenta destino",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label="Monto a transferir",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)  # 👈 guardamos el usuario en el form
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        entidad_destino = cleaned_data.get("entidad_destino")
        numero_cuenta_destino = cleaned_data.get("numero_cuenta_destino")

        if self.user and entidad_destino and numero_cuenta_destino:
            try:
                cuenta_destino = Cuenta.objects.get(
                    entidad=entidad_destino,
                    numero_cuenta=numero_cuenta_destino
                )
                # 🚨 Validación: no se puede transferir a tu propia cuenta
                if cuenta_destino.usuario == self.user:
                    raise forms.ValidationError("No podés transferir a tu propia cuenta.")
            except Cuenta.DoesNotExist:
                raise forms.ValidationError("La cuenta destino no existe.")

        return cleaned_data
