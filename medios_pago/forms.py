from django import forms
from django.forms import modelformset_factory
from .models import MedioDePago, CampoMedioDePago


class MedioDePagoForm(forms.ModelForm):
    class Meta:
        model = MedioDePago
        fields = ['nombre', 'comision_porcentaje', 'is_active']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'comision_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            raise forms.ValidationError('El nombre del medio de pago es requerido.')
        return nombre

    def clean_comision_porcentaje(self):
        comision = self.cleaned_data.get('comision_porcentaje')
        if comision is None:
            return 0
        if comision < 0 or comision > 100:
            raise forms.ValidationError('La comisión debe ser un valor entre 0 y 100.')
        return comision


class CampoMedioDePagoForm(forms.ModelForm):
    class Meta:
        model = CampoMedioDePago
        fields = ['nombre_campo', 'tipo_dato', 'is_required']
        widgets = {
            'nombre_campo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_dato': forms.Select(attrs={'class': 'form-select'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_nombre_campo(self):
        nombre = (self.cleaned_data.get('nombre_campo') or '').strip()
        if not nombre:
            raise forms.ValidationError('El nombre del campo es requerido.')
        return nombre
    
    def clean(self):
        cleaned_data = super().clean()
        # Solo validar si no está marcado para eliminación
        if not cleaned_data.get('DELETE', False):
            if not cleaned_data.get('nombre_campo'):
                raise forms.ValidationError('El nombre del campo es requerido.')
            if not cleaned_data.get('tipo_dato'):
                raise forms.ValidationError('El tipo de dato es requerido.')
        return cleaned_data


CampoMedioDePagoFormSet = modelformset_factory(
    CampoMedioDePago,
    form=CampoMedioDePagoForm,
    fields=('nombre_campo', 'tipo_dato', 'is_required'),
    extra=1,
    can_delete=True,
    validate_max=True,
    max_num=10,  # Limitar a máximo 10 campos por medio de pago
)