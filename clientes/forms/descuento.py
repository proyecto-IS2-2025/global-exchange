"""
Formularios para la gestión de descuentos por segmento.
"""
from django import forms
from django.core.exceptions import ValidationError

from ..models import Descuento


class DescuentoForm(forms.ModelForm):
    """Formulario para gestionar descuentos por segmento."""
    
    class Meta:
        model = Descuento
        fields = ['porcentaje_descuento']
        widgets = {
            'porcentaje_descuento': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
        }
        labels = {
            'porcentaje_descuento': 'Porcentaje de Descuento (%)',
        }

    def clean_porcentaje_descuento(self):
        """Validar que el porcentaje esté en rango válido."""
        porcentaje = self.cleaned_data.get('porcentaje_descuento')
        
        if porcentaje is None:
            raise ValidationError('El porcentaje de descuento es obligatorio.')
        
        if porcentaje < 0:
            raise ValidationError('El porcentaje no puede ser negativo.')
        
        if porcentaje > 100:
            raise ValidationError('El porcentaje no puede ser mayor a 100%.')
        
        return porcentaje