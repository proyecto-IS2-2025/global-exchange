"""
Formularios para gestión de inventario por denominaciones en terminales.
Autor: Sistema TAUSER
Fecha: 2024
"""

from django import forms
from .models import InventarioDenominacionTerminal
from divisas.models import Denominacion


class InventarioDenominacionTerminalForm(forms.ModelForm):
    """
    Formulario para gestionar inventario de denominaciones en terminal.
    Reemplaza InventarioDivisaTerminalForm para gestión granular de billetes.
    """
    class Meta:
        model = InventarioDenominacionTerminal
        fields = ['denominacion', 'cantidad', 'cantidad_minima']
        widgets = {
            'denominacion': forms.Select(
                attrs={
                    'class': 'form-select',
                    'required': True
                }
            ),
            'cantidad': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'value': '0',
                    'required': True
                }
            ),
            'cantidad_minima': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'value': '10',
                    'required': True
                }
            ),
        }
        labels = {
            'denominacion': 'Denominación (Billete/Moneda)',
            'cantidad': 'Cantidad Inicial',
            'cantidad_minima': 'Cantidad Mínima (Alerta)',
        }
        help_texts = {
            'cantidad': 'Número de billetes o monedas disponibles',
            'cantidad_minima': 'Se activará una alerta cuando la cantidad sea menor a este valor',
        }
    
    def __init__(self, *args, **kwargs):
        self.terminal = kwargs.pop('terminal', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar solo denominaciones activas
        self.fields['denominacion'].queryset = Denominacion.objects.filter(
            is_active=True
        ).select_related('divisa').order_by('divisa__code', '-valor')
        
        # Mejorar la visualización del dropdown
        self.fields['denominacion'].label_from_instance = lambda obj: (
            f"{obj.divisa.code} - {obj.get_tipo_display()} {obj.valor} "
            f"({obj.divisa.symbol}{obj.valor})"
        )
    
    def clean_denominacion(self):
        """Validar que no exista duplicado para este terminal"""
        denominacion = self.cleaned_data.get('denominacion')
        
        if self.terminal and denominacion:
            # Verificar si ya existe esta denominación para el terminal
            existing = InventarioDenominacionTerminal.objects.filter(
                terminal=self.terminal,
                denominacion=denominacion
            )
            
            # Si estamos editando, excluir el registro actual
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f'Ya existe inventario para la denominación {denominacion} en este terminal.'
                )
        
        return denominacion
    
    def clean_cantidad(self):
        """Validar que la cantidad sea positiva"""
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is not None and cantidad < 0:
            raise forms.ValidationError('La cantidad no puede ser negativa.')
        return cantidad
    
    def clean_cantidad_minima(self):
        """Validar que la cantidad mínima sea positiva"""
        cantidad_minima = self.cleaned_data.get('cantidad_minima')
        if cantidad_minima is not None and cantidad_minima < 0:
            raise forms.ValidationError('La cantidad mínima no puede ser negativa.')
        return cantidad_minima


class AjusteInventarioDenominacionForm(forms.Form):
    """
    Formulario para ajustar la cantidad de una denominación específica.
    Usado en vista rápida de ajuste.
    """
    cantidad = forms.IntegerField(
        label='Nueva Cantidad',
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'required': True
        }),
        help_text='Ingrese la nueva cantidad de billetes/monedas'
    )
    
    motivo = forms.CharField(
        label='Motivo del Ajuste',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Reposición, Ajuste por inventario físico, etc.'
        }),
        help_text='Opcional: Indique el motivo del ajuste para auditoría'
    )
