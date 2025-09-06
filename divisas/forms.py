from django import forms
from .models import Divisa, TasaCambio


class DivisaForm(forms.ModelForm):
    """
    Formulario para la creación y edición de divisas.
    
    Este formulario se basa en el modelo :class:`~divisas.models.Divisa`.
    """
    class Meta:
        model = Divisa
        fields = ['nombre', 'code', 'simbolo']  # is_active NO se expone al crear

    def clean_code(self):
        """
        Limpia y formatea el campo de código de la divisa.

        Convierte el código a mayúsculas y elimina los espacios en blanco.
        
        :return: El código de la divisa formateado.
        :rtype: str
        """
        return (self.cleaned_data.get('code') or '').upper().strip()


class TasaCambioForm(forms.ModelForm):
    """
    Formulario para la creación y edición de tasas de cambio.

    Este formulario se basa en el modelo :class:`~divisas.models.TasaCambio` y
    personaliza el widget para el campo de fecha.
    """
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
        """
        Inicializa el formulario y define los formatos de entrada para la fecha.
        """
        super().__init__(*args, **kwargs)
        # Configurar formatos aceptados
        self.fields['fecha'].input_formats = ['%d/%m/%Y']