# transactions/forms.py
from django import forms
from divisas.models import Divisa

class TransaccionForm(forms.Form):
    TIPO_OP_CHOICES = [
        ('compra', 'Comprar Divisa'),
        ('venta', 'Vender Divisa'),
    ]

    tipo_operacion = forms.ChoiceField(choices=TIPO_OP_CHOICES, label="Tipo de Operación")
    divisa_a_comprar = forms.ModelChoiceField(
        queryset=Divisa.objects.exclude(code='PYG').filter(is_active=True), # Excluir el Guaraní
        label="Divisa a Comprar/Vender"
    )
    monto_a_cambiar = forms.DecimalField(max_digits=15, decimal_places=2, label="Monto")

    def clean_monto_a_cambiar(self):
        monto = self.cleaned_data.get('monto_a_cambiar')
        if monto is not None:
            if monto <= 0:
                raise forms.ValidationError("El monto debe ser un número positivo.")
        return monto

