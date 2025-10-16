"""
Formularios para el módulo de notificaciones.

Este módulo contiene los formularios necesarios para la configuración y gestión
de notificaciones de tasas de cambio. Incluye formularios para configuración
general del usuario y para crear/editar reglas de alerta individuales.

Formularios:
    - ConfiguracionGeneralForm: Preferencias globales de notificaciones
    - NotificacionTasaForm: Crear/editar reglas de alerta con validación condicional
"""

from django import forms
from .models import ConfiguracionGeneral, NotificacionTasa
from divisas.models import Divisa
from .models import NotificacionTasa, ConfiguracionGeneral, OPERACION_CHOICES, TIPO_ALERTA_CHOICES


class ConfiguracionGeneralForm(forms.ModelForm):
    """
    Formulario para configuración general de notificaciones del usuario.

    Permite al usuario activar/desactivar notificaciones y seleccionar
    el canal de notificación preferido (sistema, correo, o ambos).

    :Meta model: ConfiguracionGeneral
    :Meta fields: ['habilitar_notificaciones', 'canal_notificacion']
    """
    
    class Meta:
        model = ConfiguracionGeneral
        fields = ['habilitar_notificaciones', 'canal_notificacion']


class NotificacionTasaForm(forms.ModelForm):
    """
    Formulario para crear y editar reglas de alerta de tasas de cambio.

    Este formulario maneja la creación y edición de reglas de notificación
    con características especiales:
        - Convierte objetos Divisa a códigos string
        - Filtra divisas activas (excluye PYG/Guaraní)
        - Excluye tipo 'transaccion_cancelada' (uso interno)
        - Validaciones condicionales según tipo de alerta
        - Establece valores iniciales en modo edición

    :Meta model: NotificacionTasa
    :Meta fields: ['divisa', 'tipo_operacion', 'tipo_alerta', 'condicion_umbral', 'monto_umbral']
    """
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
        """
        Inicializa el formulario y establece valores iniciales en modo edición.

        Cuando se está editando una notificación existente, convierte el código
        de divisa almacenado como string en el modelo al objeto Divisa completo
        para que el ModelChoiceField lo muestre correctamente.

        :param args: Argumentos posicionales del formulario
        :param kwargs: Argumentos de palabra clave del formulario
        """
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

    def clean_divisa(self):
        """
        Convierte el objeto Divisa seleccionado en su código string.

        El formulario usa un ModelChoiceField que devuelve objetos Divisa,
        pero el modelo NotificacionTasa almacena el código como CharField.
        Este método realiza la conversión necesaria.

        :return: Código de la divisa seleccionada (ej: 'USD', 'EUR')
        :rtype: str or None
        """
        divisa_obj = self.cleaned_data.get('divisa')
        if divisa_obj:
            return divisa_obj.code
        return divisa_obj

    def clean(self):
        """
        Validación condicional de los datos del formulario.

        Aplica reglas de validación según el tipo de alerta:
            - Alertas de umbral: requiere monto_umbral y condicion_umbral,
              no permite tipo_operacion='ambos'
            - Alertas generales: limpia campos de umbral irrelevantes

        :return: Datos del formulario limpiados y validados
        :rtype: dict
        :raises ValidationError: Si alguna validación condicional falla
        """
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