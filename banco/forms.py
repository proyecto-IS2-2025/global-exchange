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
    
    entidad_destino = forms.ModelChoiceField(
        queryset=EntidadBancaria.objects.all(),
        label="Entidad bancaria destino",
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False  # ✅ AHORA ES OPCIONAL
    )
    numero_cuenta_destino = forms.CharField(
        label="Número de cuenta destino",
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "Ej: CUENTA002", "class": "form-control"}),
        required=False  # ✅ AHORA ES OPCIONAL
    )
    monto = forms.DecimalField(
        label="Monto",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )

    # ✅ Agrega este método de limpieza para validar condicionalmente
    def clean(self):
        cleaned_data = super().clean()
        tipo_pago = cleaned_data.get("tipo_pago")

        if tipo_pago == 'TRANSFERENCIA':
            # Si el tipo de pago es transferencia, los campos de destino son obligatorios
            entidad_destino = cleaned_data.get("entidad_destino")
            numero_cuenta_destino = cleaned_data.get("numero_cuenta_destino")

            if not entidad_destino:
                self.add_error('entidad_destino', 'Este campo es obligatorio para transferencias.')
            if not numero_cuenta_destino:
                self.add_error('numero_cuenta_destino', 'Este campo es obligatorio para transferencias.')

        # Si el tipo de pago es débito o crédito, no se requiere validación de los campos de destino.
        return cleaned_data