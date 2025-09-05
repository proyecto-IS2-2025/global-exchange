# forms.py - Versión corregida para soft delete
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import MedioDePago, CampoMedioDePago


class MedioDePagoForm(forms.ModelForm):
    class Meta:
        model = MedioDePago
        fields = ['nombre', 'comision_porcentaje', 'is_active']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'comision_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
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
            raise forms.ValidationError('La comisión debe ser un valor entre 0 y 100.')
        return comision


class CampoMedioDePagoForm(forms.ModelForm):
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
            # Buscar campos existentes con el mismo nombre (excluyendo eliminados)
            existing = CampoMedioDePago.objects.filter(
                medio_de_pago=self.instance.medio_de_pago,
                nombre_campo__iexact=nombre_campo,
                deleted_at__isnull=True  # Solo considerar campos NO eliminados
            )
            
            # Excluir el objeto actual si está siendo editado
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError({
                    'nombre_campo': f'Ya existe un campo activo con el nombre "{nombre_campo}" en este medio de pago.'
                })
        
        return cleaned_data


# Formset personalizado que maneja soft delete correctamente
class CampoMedioDePagoFormSet(forms.BaseInlineFormSet):
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

    def save(self, commit=True):
        """Override save para manejar soft delete correctamente"""
        instances = super().save(commit=False)
        
        # Para formularios marcados como DELETE en edición, hacer soft delete
        for form in self.deleted_forms:
            if form.instance.pk:
                # En lugar de eliminar, hacer soft delete
                form.instance.soft_delete()
        
        if commit:
            for instance in instances:
                instance.save()
        
        return instances


# Crear el formset usando la clase personalizada
CampoMedioDePagoFormSet = inlineformset_factory(
    MedioDePago,
    CampoMedioDePago,
    form=CampoMedioDePagoForm,
    formset=CampoMedioDePagoFormSet,  # Usar nuestro formset personalizado
    fields=('nombre_campo', 'tipo_dato', 'is_required'),
    extra=0,
    can_delete=True,
    validate_max=True,
    max_num=10,
)