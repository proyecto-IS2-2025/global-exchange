from django import forms
from .models import Cliente, AsignacionCliente, Comision

class ClienteForm(forms.ModelForm):
    """
    Formulario para crear/editar clientes.
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
        self.fields['cliente'].queryset = (
            AsignacionCliente.objects.filter(usuario=user)
                                     .select_related('cliente')
        )
        self.fields['cliente'].label_from_instance = lambda obj: obj.cliente.nombre_completo

# Nuevo formulario para la gestión de comisiones
class ComisionForm(forms.ModelForm):
    class Meta:
        model = Comision
        fields = ['valor_compra', 'valor_venta']
        widgets = {
            'valor_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }