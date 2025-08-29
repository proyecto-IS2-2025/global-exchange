# clientes/forms.py
from django import forms
from .models import Cliente, AsignacionCliente

class ClienteForm(forms.ModelForm):
    """
    Formulario para crear/editar clientes.
    No incluye la asignación de usuario: eso se gestiona aparte.
    """
    class Meta:
        model = Cliente
        fields = ['cedula', 'nombre_completo', 'direccion', 'telefono', 'segmento']
        widgets = {
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese cédula'
            }),
            'nombre_completo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese nombre completo'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese dirección'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese teléfono'
            }),
            'segmento': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class SeleccionClienteForm(forms.Form):
    """
    Formulario para que un usuario seleccione entre sus clientes asignados.
    """
    cliente = forms.ModelChoiceField(
        queryset=None,
        empty_label="Seleccione un cliente",
        label="Cliente asignado"
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar los clientes asociados al usuario
        self.fields['cliente'].queryset = (
            AsignacionCliente.objects.filter(usuario=user)
                                     .select_related('cliente')
        )
        self.fields['cliente'].label_from_instance = lambda obj: obj.cliente.nombre_completo
