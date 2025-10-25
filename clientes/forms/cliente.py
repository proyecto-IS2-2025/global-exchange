"""
Formularios para la gestión de clientes.
"""
from django import forms
from django.core.exceptions import ValidationError

from ..models import Cliente, AsignacionCliente


class ClienteForm(forms.ModelForm):
    """Formulario para crear/editar clientes."""
    
    class Meta:
        model = Cliente
        fields = [
            'cedula', 
            'nombre_completo', 
            'direccion', 
            'telefono', 
            'email',
            'segmento', 
            'tipo_cliente', 
            'esta_activo'
        ]
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
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'segmento': forms.Select(attrs={'class': 'form-select'}),
            'tipo_cliente': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ejemplo: minorista / mayorista'
            }),
            'esta_activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'cedula': 'Cédula',
            'nombre_completo': 'Nombre Completo',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'email': 'Correo Electrónico',
            'segmento': 'Segmento',
            'tipo_cliente': 'Tipo de Cliente',
            'esta_activo': 'Activo',
        }

    def clean_cedula(self):
        """Validar formato de cédula."""
        cedula = self.cleaned_data.get('cedula', '').strip()
        
        if not cedula:
            raise ValidationError('La cédula es obligatoria.')
        
        if not cedula.isdigit():
            raise ValidationError('La cédula solo debe contener números.')
        
        if len(cedula) < 6:
            raise ValidationError('La cédula debe tener al menos 6 dígitos.')
        
        # Verificar duplicados (excluir el objeto actual si estamos editando)
        qs = Cliente.objects.filter(cedula=cedula)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('Ya existe un cliente con esta cédula.')
        
        return cedula

    def clean_email(self):
        """Validar formato de email."""
        email = self.cleaned_data.get('email', '').strip()
        
        if email:
            # Verificar duplicados (excluir el objeto actual si estamos editando)
            qs = Cliente.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError('Ya existe un cliente con este correo electrónico.')
        
        return email


class SeleccionClienteForm(forms.Form):
    """Formulario para que un usuario seleccione entre sus clientes asignados."""
    
    cliente = forms.ModelChoiceField(
        queryset=None,
        empty_label="Seleccione un cliente",
        label="Cliente asignado",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener clientes asignados al usuario
        asignaciones = AsignacionCliente.objects.filter(
            usuario=user
        ).select_related('cliente', 'cliente__segmento')
        
        self.fields['cliente'].queryset = Cliente.objects.filter(
            id__in=asignaciones.values_list('cliente_id', flat=True),
            esta_activo=True
        )
        
        # Personalizar la visualización del select
        self.fields['cliente'].label_from_instance = lambda obj: (
            f"{obj.nombre_completo} - {obj.cedula} ({obj.segmento.name})"
        )