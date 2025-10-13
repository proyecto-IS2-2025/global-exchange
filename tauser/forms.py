from django import forms
from .models import Terminal, InventarioDivisaTerminal
from divisas.models import Divisa
from users.models import CustomUser


class TerminalForm(forms.ModelForm):
    """Formulario para crear/editar terminales"""
    
    class Meta:
        model = Terminal
        fields = ['nombre', 'codigo', 'ubicacion', 'usuario_responsable', 'is_activa']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Terminal Centro'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: TERM-001'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Av. España c/ Brasil'
            }),
            'usuario_responsable': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Terminal',
            'codigo': 'Código Único',
            'ubicacion': 'Ubicación',
            'usuario_responsable': 'Usuario Responsable',
            'is_activa': '¿Terminal Activa?',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo usuarios activos para el responsable
        self.fields['usuario_responsable'].queryset = CustomUser.objects.filter(is_active=True)
        self.fields['usuario_responsable'].required = False


class InventarioDivisaTerminalForm(forms.ModelForm):
    """Formulario para gestionar inventario de divisas en terminales"""
    
    class Meta:
        model = InventarioDivisaTerminal
        fields = ['divisa', 'cantidad', 'cantidad_minima']
        widgets = {
            'divisa': forms.Select(attrs={
                'class': 'form-select',
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
            }),
            'cantidad_minima': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
            }),
        }
        labels = {
            'divisa': 'Divisa',
            'cantidad': 'Cantidad Disponible',
            'cantidad_minima': 'Cantidad Mínima (Alerta)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar divisas activas
        self.fields['divisa'].queryset = Divisa.objects.filter(is_active=True)


# Formset para gestión masiva de inventario
from django.forms import inlineformset_factory

InventarioDivisaTerminalFormSet = inlineformset_factory(
    Terminal,
    InventarioDivisaTerminal,
    form=InventarioDivisaTerminalForm,
    extra=1,
    can_delete=True
)