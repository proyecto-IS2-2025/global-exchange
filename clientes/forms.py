"""
VIEJO
# clientes/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['cedula', 'nombre_completo', 'direccion', 'telefono', 'segmento']
"""
#NUEVO
# clientes/forms.py
from django import forms
from .models import Cliente
from users.models import CustomUser 
from asociar_clientes_usuarios.models import AsignacionCliente

class ClienteForm(forms.ModelForm):
    usuario = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        required=True,
        label="Usuario asociado"
    )

    class Meta:
        model = Cliente
        fields = ['cedula', 'nombre_completo', 'direccion', 'telefono', 'segmento', 'usuario']

    def save(self, commit=True):
        cliente = super().save(commit=False)
        if commit:
            cliente.save()
            AsignacionCliente.objects.create(
                cliente=cliente,
                usuario=self.cleaned_data['usuario']
            )
        return cliente
