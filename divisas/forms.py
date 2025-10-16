#divisas
from decimal import Decimal, InvalidOperation, InvalidOperation
from django import forms
from .models import Divisa, TasaCambio, Denominacion, DesgloseDenominacion
# Formset para crear múltiples denominaciones a la vez
from django.forms import formset_factory, inlineformset_factory

"""
Formularios para la gestión de divisas y tasas de cambio.

Este módulo define formularios basados en modelos que validan y procesan
los datos de divisas y tasas de cambio con reglas adicionales.
"""

class DivisaForm(forms.ModelForm):
    class Meta:
        model = Divisa
        fields = ['nombre', 'code', 'simbolo', 'decimales']
        widgets = {
            'decimales': forms.NumberInput(attrs={'min': 0, 'max': 8}),
        }

    def clean_code(self):
        code = (self.cleaned_data.get('code') or '').upper().strip()
        
        # Bloquear creación con código PYG
        if code == 'PYG' and not self.instance.pk:
            raise forms.ValidationError(
                'El código PYG está reservado para la moneda base del sistema.'
            )
        
        # Bloquear cambio de código en PYG existente
        if self.instance.pk and self.instance.code == 'PYG' and code != 'PYG':
            raise forms.ValidationError(
                'No se puede cambiar el código de la moneda base.'
            )
        
        return code
# forms.py
class TasaCambioForm(forms.ModelForm):
    """
    Formulario para crear o actualizar tasas de cambio.

    Aplica reglas de validación para garantizar que los valores sean positivos
    y asocia la tasa a una divisa.
    """
    class Meta:
        model = TasaCambio
        fields = ['precio_base', 'comision_compra', 'comision_venta']  # sin fecha
        widgets = {
            'precio_base': forms.NumberInput(attrs={'step': '0.00000001', 'min': '0'}),
            'comision_compra': forms.NumberInput(attrs={'step': '0.00000001', 'min': '0'}),
            'comision_venta': forms.NumberInput(attrs={'step': '0.00000001', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario con la divisa proporcionada.

        :param divisa: La divisa asociada al formulario.
        :type divisa: Divisa
        """
        self.divisa = kwargs.pop('divisa', None)
        super().__init__(*args, **kwargs)
        if self.divisa:
            self.instance.divisa = self.divisa

    # Reglas: valores numéricos absolutos > 0
    def clean_precio_base(self):
        """
        Valida que el precio base sea mayor que 0.
        """
        v = self.cleaned_data.get('precio_base')
        if v is not None and v <= 0:
            raise forms.ValidationError('El precio base debe ser mayor a 0.')
        return v

    def clean_comision_compra(self):
        """
        Valida que la comisión de compra sea mayor que 0.
        """
        v = self.cleaned_data.get('comision_compra')
        if v is not None and v <= 0:
            raise forms.ValidationError('La comisión de compra debe ser mayor a 0.')
        return v

    def clean_comision_venta(self):
        """
        Valida que la comisión de venta sea mayor que 0.
        """
        v = self.cleaned_data.get('comision_venta')
        if v is not None and v <= 0:
            raise forms.ValidationError('La comisión de venta debe ser mayor a 0.')
        return v
    


"""""""""
# divisas/migrations/0004_crear_moneda_base_pyg.py
from django.db import migrations

def crear_pyg(apps, schema_editor):
    
    Crea o actualiza la moneda base PYG.
    Divisa = apps.get_model('divisas', 'Divisa')
    
    try:
        pyg = Divisa.objects.get(code='PYG')
        pyg.nombre = 'Guaraní'
        pyg.simbolo = '₲'
        pyg.is_active = True
        pyg.decimales = 0
        pyg.es_moneda_base = True
        pyg.save()
    except Divisa.DoesNotExist:
        Divisa.objects.create(
            code='PYG',
            nombre='Guaraní',
            simbolo='₲',
            is_active=True,
            decimales=0,
            es_moneda_base=True,
        )

def revertir_pyg(apps, schema_editor):
    Eliminar PYG (solo para desarrollo)
    Divisa = apps.get_model('divisas', 'Divisa')
    Divisa.objects.filter(code='PYG').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('divisas', '0003_divisa_es_moneda_base_and_more'),  # ⭐ Cambiar aquí
    ]

    operations = [
        migrations.RunPython(crear_pyg, revertir_pyg),
    ]''''"""

class DenominacionForm(forms.ModelForm):
    """Formulario para crear/editar una denominación individual"""
    
    class Meta:
        model = Denominacion
        fields = ['divisa', 'valor', 'is_active', 'orden', 'notas']
        widgets = {
            'divisa': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Ej: 100.00',
                'required': True
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Dejar en blanco para calcular automáticamente'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Información adicional (opcional)'
            }),
        }
        labels = {
            'divisa': 'Divisa',
            'valor': 'Valor Nominal',
            'is_active': '¿Disponible?',
            'orden': 'Orden',
            'notas': 'Notas',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo divisas activas
        self.fields['divisa'].queryset = Divisa.objects.filter(is_active=True).order_by('code')
        
        # Hacer campos opcionales
        self.fields['orden'].required = False
        self.fields['notas'].required = False
    
    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor and valor <= 0:
            raise forms.ValidationError('El valor debe ser mayor a cero.')
        return valor

# BaseFormSet para denominaciones nuevas (sin instancia de Divisa)
DenominacionBaseFormSet = formset_factory(
    DenominacionForm,
    extra=5,  # 5 formularios vacíos por defecto
    can_delete=True,
    max_num=20,  # Máximo 20 denominaciones a la vez
    validate_max=True
)

# InlineFormSet para editar denominaciones existentes de una divisa
DenominacionFormSet = inlineformset_factory(
    Divisa,
    Denominacion,
    form=DenominacionForm,
    extra=3,
    can_delete=True,
    fields=['valor','is_active', 'orden', 'notas']
)


# Formulario simplificado para creación rápida masiva
class DenominacionQuickForm(forms.Form):
    """Formulario para crear múltiples denominaciones rápidamente"""
    
    divisa = forms.ModelChoiceField(
        queryset=Divisa.objects.filter(is_active=True).order_by('code'),
        label='Divisa',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        empty_label='Seleccione una divisa'
    )
    
    valores = forms.CharField(
        label='Valores de billetes',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Ingrese los valores separados por comas.\nEjemplo: 100, 50, 20, 10, 5, 1',
            'required': True
        }),
        help_text='Separe múltiples valores con comas. Ejemplo: 100, 50, 20, 10'
    )
    
    is_active = forms.BooleanField(
        label='Activar denominaciones',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_valores(self):
        """Valida y convierte los valores ingresados"""
        valores_str = self.cleaned_data.get('valores', '')
        
        if not valores_str.strip():
            raise forms.ValidationError('Debe ingresar al menos un valor.')
        
        # Dividir por comas y limpiar
        valores_lista = [v.strip() for v in valores_str.split(',') if v.strip()]
        
        if not valores_lista:
            raise forms.ValidationError('Debe ingresar al menos un valor válido.')
        
        # Convertir a Decimal y validar
        valores_decimales = []
        errores = []
        
        for valor_str in valores_lista:
            try:
                valor_decimal = Decimal(valor_str)
                if valor_decimal <= 0:
                    errores.append(f'"{valor_str}" debe ser mayor a cero')
                else:
                    valores_decimales.append(valor_decimal)
            except (InvalidOperation, ValueError):
                errores.append(f'"{valor_str}" no es un número válido')

        if errores:
            raise forms.ValidationError(errores)
        
        if not valores_decimales:
            raise forms.ValidationError('No se encontraron valores válidos.')
        
        # Eliminar duplicados
        valores_decimales = list(set(valores_decimales))
        
        return valores_decimales

class DesgloseDenominacionForm(forms.ModelForm):
    """Formulario para registrar desglose de denominaciones en una transacción"""
    
    class Meta:
        model = DesgloseDenominacion
        fields = ['denominacion', 'cantidad']
        widgets = {
            'denominacion': forms.Select(attrs={
                'class': 'form-select',
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1',
            }),
        }
    
    def __init__(self, *args, divisa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if divisa:
            # Filtrar denominaciones por divisa y activas
            self.fields['denominacion'].queryset = Denominacion.objects.filter(
                divisa=divisa,
                is_active=True
            ).order_by('-valor')


# Formset para gestión masiva de denominaciones
from django.forms import inlineformset_factory

DenominacionFormSet = inlineformset_factory(
    Divisa,
    Denominacion,
    form=DenominacionForm,
    extra=1,
    can_delete=True,
    fields=['valor', 'is_active', 'orden', 'notas']
)


# IMPORTANTE: NO crear el DesgloseDenominacionFormSet aquí
# porque causaría importación circular.
# En su lugar, créalo dinámicamente cuando lo necesites en las vistas:
#
# from django.forms import inlineformset_factory
# from transacciones.models import Transaccion
# from divisas.models import DesgloseDenominacion
# 
# DesgloseDenominacionFormSet = inlineformset_factory(
#     Transaccion,
#     DesgloseDenominacion,
#     form=DesgloseDenominacionForm,
#     extra=3,
#     can_delete=True,
#     fields=['denominacion', 'cantidad']
# )