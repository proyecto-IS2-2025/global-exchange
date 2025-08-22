from django import forms
from .models import AsignacionCliente

class SeleccionClienteForm(forms.Form):
    cliente = forms.ModelChoiceField(queryset=None, empty_label="Seleccione un cliente")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar los clientes asociados al usuario
        self.fields['cliente'].queryset = AsignacionCliente.objects.filter(usuario=user).select_related('cliente')
        self.fields['cliente'].label_from_instance = lambda obj: obj.cliente.nombre_completo
