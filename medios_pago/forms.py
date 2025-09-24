# forms.py - VersiÃ³n con campos predefinidos
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import MedioDePago, CampoMedioDePago, PREDEFINED_FIELDS, PAYMENT_TEMPLATES


class MedioDePagoForm(forms.ModelForm):
    """
    Formulario para la creaciÃ³n y ediciÃ³n de un Medio de Pago.
    Ahora incluye la opciÃ³n de aplicar templates predefinidos.
    """
    aplicar_template = forms.ChoiceField(
        label='Usar template predefinido',
        choices=[('', '--- Personalizado ---')] + [(k, v['name']) for k, v in PAYMENT_TEMPLATES.items()],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_template_selector'
        }),
        help_text='Selecciona un template para autocompletar campos comunes'
    )
    
    class Meta:
        model = MedioDePago
        fields = ['nombre', 'comision_porcentaje', 'is_active']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'comision_porcentaje': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'max': '100'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            raise forms.ValidationError('El nombre del medio de pago es requerido.')
        return nombre

    def clean_comision_porcentaje(self):
        comision = self.cleaned_data.get('comision_porcentaje')
        if comision is None:
            return 0
        if comision < 0 or comision > 100:
            raise forms.ValidationError('La comisiÃ³n debe ser un valor entre 0 y 100.')
        return comision


class CampoMedioDePagoForm(forms.ModelForm):
    """
    Formulario para los campos predefinidos de un Medio de Pago.
    Ahora usa un selector de campos predefinidos en lugar de entrada libre.
    """
    class Meta:
        model = CampoMedioDePago
        fields = ['campo_api', 'is_required']
        widgets = {
            'campo_api': forms.Select(attrs={
                'class': 'form-select campo-api-select',
                'data-toggle': 'field-info'
            }),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar choices del campo_api
        self.fields['campo_api'].choices = [('', '--- Seleccionar campo ---')] + [
            (k, v['label']) for k, v in PREDEFINED_FIELDS.items()
        ]
        
        # Auto-completar si ya existe
        if self.instance.pk and self.instance.campo_api:
            self.fields['campo_api'].initial = self.instance.campo_api
    
    def clean_campo_api(self):
        campo_api = self.cleaned_data.get('campo_api')
        if not campo_api:
            raise forms.ValidationError('Debe seleccionar un campo de la lista.')
        
        if campo_api not in PREDEFINED_FIELDS:
            raise forms.ValidationError('El campo seleccionado no es vÃ¡lido.')
        
        return campo_api

    def clean(self):
        cleaned_data = super().clean()
        campo_api = cleaned_data.get('campo_api')
        
        # Validar duplicados en el mismo medio de pago
        if campo_api and hasattr(self, 'instance') and hasattr(self.instance, 'medio_de_pago') and self.instance.medio_de_pago:
            existing = CampoMedioDePago.objects.filter(
                medio_de_pago=self.instance.medio_de_pago,
                campo_api=campo_api
            )
            
            # Excluir el objeto actual si estÃ¡ siendo editado
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                campo_label = PREDEFINED_FIELDS[campo_api]['label']
                raise forms.ValidationError({
                    'campo_api': f'Ya existe el campo "{campo_label}" en este medio de pago.'
                })
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Auto-completar informaciÃ³n desde PREDEFINED_FIELDS
        if instance.campo_api in PREDEFINED_FIELDS:
            field_def = PREDEFINED_FIELDS[instance.campo_api]
            instance.nombre_campo = field_def['label']
            instance.tipo_dato = field_def['type']
            if not instance.descripcion:
                instance.descripcion = field_def['description']
        
        if commit:
            instance.save()
        return instance


class CampoMedioDePagoFormSet(forms.BaseInlineFormSet):
    """
    Formset personalizado para manejar campos predefinidos.
    """
    def clean(self):
        if any(self.errors):
            return
        
        campos_api = []
        for form in self.forms:
            if not form.cleaned_data:
                continue
                
            # Solo considerar formularios que no serÃ¡n eliminados
            if form.cleaned_data.get('DELETE', False):
                continue
                
            campo_api = form.cleaned_data.get('campo_api')
            if campo_api:
                if campo_api in campos_api:
                    campo_label = PREDEFINED_FIELDS[campo_api]['label']
                    raise forms.ValidationError(
                        f'No puede seleccionar el mismo campo "{campo_label}" mÃºltiples veces.'
                    )
                campos_api.append(campo_api)


def create_campo_formset(is_edit=False):
    """
    Factory para crear formsets con configuraciÃ³n especÃ­fica.
    """
    extra_forms = 0 if is_edit else 1
    
    return inlineformset_factory(
        MedioDePago,
        CampoMedioDePago,
        form=CampoMedioDePagoForm,
        formset=CampoMedioDePagoFormSet,
        fields=('campo_api', 'is_required'),
        extra=extra_forms,
        can_delete=True,
        validate_max=True,
        max_num=len(PREDEFINED_FIELDS),  # MÃ¡ximo: todos los campos disponibles
    )


class TemplateApplicationForm(forms.Form):
    """
    Formulario auxiliar para aplicar templates a medios existentes.
    """
    template = forms.ChoiceField(
        label='Template a aplicar',
        choices=[(k, v['name']) for k, v in PAYMENT_TEMPLATES.items()],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sobrescribir_existentes = forms.BooleanField(
        label='Sobrescribir campos existentes',
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Si estÃ¡ marcado, eliminarÃ¡ los campos actuales y aplicarÃ¡ solo los del template'
    )


# Mantener compatibilidad
CampoMedioDePagoFormSet = create_campo_formset(is_edit=False)