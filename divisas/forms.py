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

class TasaCambioForm(forms.ModelForm):
    class Meta:
        model = TasaCambio
        fields = ['fecha', 'precio_base']
        widgets = {
            'fecha': forms.DateInput(
                format='%d/%m/%Y',
                attrs={'type': 'text', 'placeholder': 'dd/mm/yyyy'}
            ),
        }

    def __init__(self, *args, **kwargs):
        # recibimos la divisa desde la vista
        self.divisa = kwargs.pop('divisa', None)
        super().__init__(*args, **kwargs)
        self.fields['fecha'].input_formats = ['%d/%m/%Y']
        if self.divisa:
            self.instance.divisa = self.divisa  # para que Django sepa la relación

    def clean(self):
        cleaned = super().clean()
        fecha = cleaned.get('fecha')
        if self.divisa and fecha:
            existe = TasaCambio.objects.filter(divisa=self.divisa, fecha=fecha)\
                                       .exclude(pk=self.instance.pk).exists()
            if existe:
                self.add_error('fecha', 'Ya existe una tasa para esta divisa en esa fecha.')
        return cleaned