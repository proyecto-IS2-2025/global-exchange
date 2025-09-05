# forms.py - REEMPLAZA TODO EL CONTENIDO
from django import forms
from django.forms import inlineformset_factory
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


# UN SOLO FORMSET - sin can_delete dinámico
CampoMedioDePagoFormSet = inlineformset_factory(
    MedioDePago,
    CampoMedioDePago,
    form=CampoMedioDePagoForm,
    fields=('nombre_campo', 'tipo_dato', 'is_required'),
    extra=1,  # Un campo extra
    can_delete=True,  # Siempre True, pero lo controlamos en el template
    validate_max=True,
    max_num=10,
)