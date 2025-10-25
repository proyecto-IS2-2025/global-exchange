"""
Formularios para la gestión de límites diarios y mensuales.
"""
from datetime import datetime, date, time

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import LimiteDiario, LimiteMensual


class LimiteDiarioForm(forms.ModelForm):
    """Formulario para gestionar límites diarios."""
    
    class Meta:
        model = LimiteDiario
        fields = ['fecha', 'monto']
        widgets = {
            'fecha': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0',
                'placeholder': '0.00'
            }),
        }
        labels = {
            'fecha': 'Fecha',
            'monto': 'Monto Límite',
        }

    def clean_fecha(self):
        """Validar que la fecha no sea pasada y no esté duplicada."""
        fecha = self.cleaned_data.get('fecha')
        
        if not fecha:
            raise ValidationError('La fecha es obligatoria.')
        
        hoy = timezone.localdate()
        
        # No permitir fechas pasadas
        if fecha < hoy:
            raise ValidationError(
                "No se pueden registrar límites en fechas pasadas."
            )

        # Verificar duplicados (excluir el objeto actual si estamos editando)
        qs = LimiteDiario.objects.filter(fecha=fecha)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError(
                f"Ya existe un límite configurado para el {fecha.strftime('%d/%m/%Y')}."
            )

        return fecha

    def clean_monto(self):
        """Validar que el monto sea positivo."""
        monto = self.cleaned_data.get('monto')
        
        if monto is None:
            raise ValidationError('El monto es obligatorio.')
        
        if monto <= 0:
            raise ValidationError('El monto debe ser mayor a cero.')
        
        return monto

    def save(self, commit=True):
        """Guardar con inicio_vigencia automático solo en creación."""
        instance = super().save(commit=False)
        
        # Solo establecer inicio_vigencia si es creación (no edición)
        if not instance.pk:
            fecha = instance.fecha
            hoy = timezone.localdate()
            
            if fecha == hoy:
                # Si es hoy, aplica de inmediato
                instance.inicio_vigencia = timezone.now()
            else:
                # Si es futuro, aplica a las 00:00 de ese día
                naive = datetime.combine(fecha, time.min)
                instance.inicio_vigencia = timezone.make_aware(naive)

        if commit:
            instance.save()
        
        return instance


class LimiteMensualForm(forms.ModelForm):
    """Formulario para gestionar límites mensuales."""
    
    mes = forms.DateField(
        input_formats=['%Y-%m'],
        widget=forms.DateInput(attrs={
            'type': 'month', 
            'class': 'form-control'
        }),
        label='Mes',
        help_text='Selecciona el mes (se guardará como el primer día del mes)'
    )

    class Meta:
        model = LimiteMensual
        fields = ['mes', 'monto']
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0',
                'placeholder': '0.00'
            }),
        }
        labels = {
            'monto': 'Monto Límite',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Establecer mes actual como inicial
        hoy = timezone.localdate()
        self.fields['mes'].initial = hoy.strftime('%Y-%m')

    def clean_mes(self):
        """Validar mes y normalizar al día 1."""
        fecha = self.cleaned_data.get('mes')
        
        if not fecha:
            raise ValidationError('El mes es obligatorio.')
        
        # Normalizar siempre al día 1 del mes
        fecha = date(fecha.year, fecha.month, 1)

        # No permitir meses pasados
        hoy = timezone.localdate()
        mes_actual = date(hoy.year, hoy.month, 1)
        
        if fecha < mes_actual:
            raise ValidationError(
                "No se pueden registrar límites en meses pasados."
            )

        # Verificar duplicados (excluir el objeto actual si estamos editando)
        qs = LimiteMensual.objects.filter(mes=fecha)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError(
                f"Ya existe un límite configurado para {fecha.strftime('%B %Y')}."
            )

        return fecha

    def clean_monto(self):
        """Validar que el monto sea positivo."""
        monto = self.cleaned_data.get('monto')
        
        if monto is None:
            raise ValidationError('El monto es obligatorio.')
        
        if monto <= 0:
            raise ValidationError('El monto debe ser mayor a cero.')
        
        return monto

    def save(self, commit=True):
        """Guardar con inicio_vigencia automático solo en creación."""
        instance = super().save(commit=False)
        
        # Solo establecer inicio_vigencia si es creación (no edición)
        if not instance.pk:
            fecha = instance.mes
            hoy = timezone.localdate()

            if fecha.year == hoy.year and fecha.month == hoy.month:
                # Si es el mes actual, aplica de inmediato
                instance.inicio_vigencia = timezone.now()
            else:
                # Si es mes futuro, aplica el día 1 a las 00:00
                naive = datetime(fecha.year, fecha.month, 1, 0, 0)
                instance.inicio_vigencia = timezone.make_aware(naive)

        if commit:
            instance.save()
        
        return instance