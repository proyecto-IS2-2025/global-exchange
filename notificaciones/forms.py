from django import forms
from .models import ConfiguracionGeneral, NotificacionTasa
from divisas.models import Divisa
from .models import NotificacionTasa, ConfiguracionGeneral, OPERACION_CHOICES, TIPO_ALERTA_CHOICES


# Formulario para la Configuración General
class ConfiguracionGeneralForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionGeneral
        fields = ['habilitar_notificaciones', 'canal_notificacion']


# Formulario para Agregar/Editar una Notificación Específica
class NotificacionTasaForm(forms.ModelForm):
    # 1. Definir el campo 'divisa' como ModelChoiceField
    divisa = forms.ModelChoiceField(
        # Filtramos por las divisas activas, ordenadas por código, excluyendo PYG (Guaraní)
        queryset=Divisa.objects.filter(is_active=True).exclude(code='PYG').order_by('code'),
        label="Divisa",
        empty_label="Seleccione una divisa",
        # IMPORTANTE: Aquí NO usamos to_field_name, dejamos que devuelva el objeto Divisa completo
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # 2. Sobreescribir el tipo de campo y establecer valores iniciales (Default)
    tipo_operacion = forms.ChoiceField(
        choices=OPERACION_CHOICES,
        initial='ambos',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # 3. Excluir 'transaccion_cancelada' de las opciones disponibles (es solo para uso interno)
    tipo_alerta = forms.ChoiceField(
        choices=[choice for choice in TIPO_ALERTA_CHOICES if choice[0] != 'transaccion_cancelada'],
        initial='general',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = NotificacionTasa
        fields = ['divisa', 'tipo_operacion', 'tipo_alerta', 'condicion_umbral', 'monto_umbral']
        widgets = {
            'condicion_umbral': forms.Select(attrs={'class': 'form-select'}),
            'monto_umbral': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001', 'placeholder': 'Ej: 1.1500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si estamos editando (instance existe), establecer el valor inicial de divisa
        if self.instance and self.instance.pk and self.instance.divisa:
            try:
                # El modelo guarda el código como string, necesitamos obtener el objeto Divisa
                divisa_obj = Divisa.objects.get(code=self.instance.divisa)
                # Para un ModelChoiceField, debemos establecer el objeto completo
                self.initial['divisa'] = divisa_obj
            except Divisa.DoesNotExist:
                pass

    # 3. CONVERSIÓN CRUCIAL: Convertir el objeto Divisa al string (code)
    def clean_divisa(self):
        """
        Toma el objeto Divisa seleccionado por el usuario y devuelve solo su 'code' (e.g., 'USD').
        Esto es lo que Django usará para asignarlo al CharField 'divisa' del modelo.
        """
        divisa_obj = self.cleaned_data.get('divisa')
        if divisa_obj:
            return divisa_obj.code
        # Si no hay objeto (ej. validación fallida), retorna el valor original o lanza un error si es necesario.
        return divisa_obj

    # 4. Validación condicional (para umbral)
    def clean(self):
        cleaned_data = super().clean()
        tipo_alerta = cleaned_data.get('tipo_alerta')
        tipo_operacion = cleaned_data.get('tipo_operacion')
        monto_umbral = cleaned_data.get('monto_umbral')
        condicion_umbral = cleaned_data.get('condicion_umbral')

        # Validar que umbral no tenga 'ambos'
        if tipo_alerta == 'umbral' and tipo_operacion == 'ambos':
            self.add_error('tipo_operacion', 'Para notificaciones de umbral debe seleccionar Compra o Venta, no ambos.')

        if tipo_alerta == 'umbral':
            if not monto_umbral:
                self.add_error('monto_umbral', 'Debe especificar un monto numérico para la alerta de umbral.')
            if not condicion_umbral:
                self.add_error('condicion_umbral', 'Debe seleccionar una condición (Mayor o Menor).')

        elif tipo_alerta == 'general':
            # Limpiar campos irrelevantes
            cleaned_data['monto_umbral'] = None
            cleaned_data['condicion_umbral'] = None

        return cleaned_data