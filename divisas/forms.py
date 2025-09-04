from django import forms
from .models import Divisa, TasaCambio


class DivisaForm(forms.ModelForm):
    class Meta:
        model = Divisa
        fields = ['nombre', 'code', 'simbolo']  # is_active NO se expone al crear

    def clean_code(self):
        return (self.cleaned_data.get('code') or '').upper().strip()


class TasaCambioForm(forms.ModelForm):
    class Meta:
        model = TasaCambio
        fields = ['fecha', 'valor_compra', 'valor_venta']
        widgets = {
            'fecha': forms.DateInput(
                format='%d/%m/%Y',
                attrs={'type': 'text', 'placeholder': 'dd/mm/yyyy'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar formatos aceptados
        self.fields['fecha'].input_formats = ['%d/%m/%Y']