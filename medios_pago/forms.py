# forms.py - Versión simplificada sin soft delete
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import MedioDePago, CampoMedioDePago


class MedioDePagoForm(forms.ModelForm):
    """
    Formulario para la creación y edición de un Medio de Pago.

    Incluye validación personalizada para el nombre y la comisión.
    """
    class Meta:
        model = MedioDePago
        fields = ['nombre', 'comision_porcentaje', 'is_active']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'comision_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_nombre(self):
        """
        Valida que el nombre del medio de pago no esté vacío.

        :raises ValidationError: Si el nombre está vacío.
        :returns: El nombre limpio y sin espacios.
        :rtype: str
        """
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            raise forms.ValidationError('El nombre del medio de pago es requerido.')
        return nombre

    def clean_comision_porcentaje(self):
        """
        Valida que el porcentaje de comisión esté en el rango de 0 a 100.

        :raises ValidationError: Si la comisión está fuera del rango.
        :returns: El valor de la comisión.
        :rtype: float
        """
        comision = self.cleaned_data.get('comision_porcentaje')
        if comision is None:
            return 0
        if comision < 0 or comision > 100:
            raise forms.ValidationError('La comisión debe ser un valor entre 0 y 100.')
        return comision


class CampoMedioDePagoForm(forms.ModelForm):
    """
    Formulario para los campos dinámicos de un Medio de Pago.
    """
    class Meta:
        model = CampoMedioDePago
        fields = ['nombre_campo', 'tipo_dato', 'is_required']
        widgets = {
            'nombre_campo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_dato': forms.Select(attrs={'class': 'form-select'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_nombre_campo(self):
        nombre = (self.cleaned_data.get('nombre_campo') or '').strip()
        if not nombre:
            raise forms.ValidationError('El nombre del campo es requerido.')
        return nombre

    def clean(self):
        cleaned_data = super().clean()
        nombre_campo = cleaned_data.get('nombre_campo')
        
        # Solo validar si tenemos un nombre de campo y una instancia padre
        if nombre_campo and hasattr(self, 'instance') and hasattr(self.instance, 'medio_de_pago') and self.instance.medio_de_pago:
            # Buscar campos existentes con el mismo nombre
            existing = CampoMedioDePago.objects.filter(
                medio_de_pago=self.instance.medio_de_pago,
                nombre_campo__iexact=nombre_campo
            )
            
            # Excluir el objeto actual si está siendo editado
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError({
                    'nombre_campo': f'Ya existe un campo con el nombre "{nombre_campo}" en este medio de pago.'
                })
        
        return cleaned_data


# Formset personalizado simplificado
class CampoMedioDePagoFormSet(forms.BaseInlineFormSet):
    """
    Formset base para manejar la validación de los campos de Medio de Pago.
    
    Asegura que no haya nombres de campo duplicados en el mismo formulario.
    """
    def clean(self):
        """Validación a nivel de formset"""
        if any(self.errors):
            return
        
        nombres_campos = []
        for form in self.forms:
            if not form.cleaned_data:
                continue
                
            # Solo considerar formularios que no serán eliminados
            if form.cleaned_data.get('DELETE', False):
                continue
                
            nombre = form.cleaned_data.get('nombre_campo')
            if nombre:
                nombre_lower = nombre.lower().strip()
                if nombre_lower in nombres_campos:
                    raise forms.ValidationError(f'No puede haber campos duplicados con el nombre "{nombre}".')
                nombres_campos.append(nombre_lower)


# Función factory para crear formsets con configuración específica según el contexto
def create_campo_formset(is_edit=False):
    """
    Factory para crear formsets con configuración específica:
    - Creación: extra=1 (un campo por defecto)
    - Edición: extra=0 (sin campos por defecto)

    :param is_edit: Indica si se está en modo de edición.
    :type is_edit: bool
    :returns: El formset de `CampoMedioDePago`.
    :rtype: inlineformset_factory
    """
    extra_forms = 0 if is_edit else 1
    
    return inlineformset_factory(
        MedioDePago,
        CampoMedioDePago,
        form=CampoMedioDePagoForm,
        formset=CampoMedioDePagoFormSet,
        fields=('nombre_campo', 'tipo_dato', 'is_required'),
        extra=extra_forms,  # Dinámico según el contexto
        can_delete=True,
        validate_max=True,
        max_num=10,
    )


# Mantener compatibilidad con el código existente
CampoMedioDePagoFormSet = create_campo_formset(is_edit=False)