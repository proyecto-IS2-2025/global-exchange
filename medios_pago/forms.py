from django import forms
from .models import MedioDePago


class MedioDePagoForm(forms.ModelForm):
    class Meta:
        model = MedioDePago
        fields = ['nombre', 'tipo', 'comision_porcentaje']

    def clean_nombre(self):
        return (self.cleaned_data.get('nombre') or '').strip()

    def clean_comision_porcentaje(self):
        comision = self.cleaned_data.get('comision_porcentaje')
        if comision < 0 or comision > 100:
            raise forms.ValidationError('La comisión debe ser un valor entre 0 y 100.')
        return comision