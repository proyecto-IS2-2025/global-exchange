from django import forms
from .models import Cliente, AsignacionCliente, Descuento

class ClienteForm(forms.ModelForm):
    """
    Formulario para crear/editar clientes.
    """
    class Meta:
        model = Cliente
        fields = ['cedula', 'nombre_completo', 'direccion', 'telefono', 'segmento', 'tipo_cliente', 'esta_activo']
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
            'segmento': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo_cliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ejemplo: minorista / mayorista'
            }),
            'esta_activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class SeleccionClienteForm(forms.Form):
    """
    Formulario para que un usuario seleccione entre sus clientes asignados.
    """
    cliente = forms.ModelChoiceField(
        queryset=None,
        empty_label="Seleccione un cliente",
        label="Cliente asignado"
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = (
            AsignacionCliente.objects.filter(usuario=user)
                                     .select_related('cliente')
        )
        self.fields['cliente'].label_from_instance = lambda obj: obj.cliente.nombre_completo

# Nuevo formulario para la gestión de descuentos
class DescuentoForm(forms.ModelForm):
    class Meta:
        model = Descuento
        fields = ['porcentaje_descuento']
        widgets = {
            'porcentaje_descuento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# clientes/forms.py - Formularios mejorados para medios de pago
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import HiddenInput
from medios_pago.models import MedioDePago, CampoMedioDePago
from .models import ClienteMedioDePago, Cliente
import re


class SelectMedioDePagoForm(forms.Form):
    """
    Formulario mejorado para seleccionar el tipo de medio de pago antes de completar los datos
    """
    medio_de_pago = forms.ModelChoiceField(
        queryset=MedioDePago.objects.none(),  # Se define en __init__
        empty_label="Seleccione un medio de pago",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'data-placeholder': 'Seleccione un tipo de medio de pago...'
        }),
        label="Tipo de medio de pago",
        help_text="Seleccione el tipo de medio de pago que desea configurar para este cliente."
    )

    def __init__(self, cliente=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if cliente:
            # Obtener medios ya asociados al cliente
            medios_asociados = ClienteMedioDePago.objects.filter(
                cliente=cliente
            ).values_list('medio_de_pago_id', flat=True)
            
            # Filtrar solo medios activos no asociados
            self.fields['medio_de_pago'].queryset = MedioDePago.objects.filter(
                is_active=True
            ).exclude(
                id__in=medios_asociados
            ).order_by('nombre')
            
            # Personalizar label si no hay opciones
            if not self.fields['medio_de_pago'].queryset.exists():
                self.fields['medio_de_pago'].empty_label = "No hay medios disponibles"
                self.fields['medio_de_pago'].help_text = (
                    "Todos los medios de pago disponibles ya están asociados a este cliente."
                )


class ClienteMedioDePagoCompleteForm(forms.ModelForm):
    """
    Formulario dinámico mejorado que incluye los campos específicos del medio de pago
    """
    class Meta:
        model = ClienteMedioDePago
        fields = ['medio_de_pago', 'es_principal']
        widgets = {
            'medio_de_pago': HiddenInput(),
            'es_principal': forms.CheckboxInput(attrs={
                'class': 'form-check-input form-check-input-lg'
            }),
        }

    def __init__(self, cliente=None, medio_de_pago=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.cliente = cliente
        self.medio_de_pago_obj = medio_de_pago
        
        # Si tenemos una instancia existente, obtener el medio de pago
        if self.instance and self.instance.pk:
            self.medio_de_pago_obj = self.instance.medio_de_pago
        
        # Configurar el campo medio_de_pago
        if self.medio_de_pago_obj:
            self.fields['medio_de_pago'].initial = self.medio_de_pago_obj
            self.fields['medio_de_pago'].queryset = MedioDePago.objects.filter(
                id=self.medio_de_pago_obj.id
            )
        
        # Personalizar el campo es_principal
        self.fields['es_principal'].label = "Medio de pago principal"
        self.fields['es_principal'].help_text = (
            "Marque esta opción si este será el medio de pago principal del cliente. "
            "Solo puede haber un medio principal por cliente."
        )
        
        # Generar campos dinámicos si hay medio de pago
        if self.medio_de_pago_obj:
            self._generate_dynamic_fields()

    def _generate_dynamic_fields(self):
        """Generar campos dinámicos basados en el medio de pago"""
        campos = self.medio_de_pago_obj.campos.filter(
            # Si tuviéramos soft delete: deleted_at__isnull=True
        ).order_by('orden', 'id')
        
        for campo in campos:
            field_name = f'campo_{campo.id}'
            field = self._create_field_by_type(campo)
            
            # Establecer valor inicial si existe
            if self.instance and self.instance.pk:
                initial_value = self.instance.get_dato_campo(campo.nombre_campo)
                if initial_value:
                    field.initial = initial_value
            
            self.fields[field_name] = field

    def _create_field_by_type(self, campo):
        """Crear campo del formulario según el tipo de dato con validaciones mejoradas"""
        base_attrs = {
            'class': 'form-control',
            'data-campo-tipo': campo.tipo_dato,
            'data-campo-id': campo.id
        }
        
        # Añadir placeholder personalizado
        placeholder = self._get_placeholder(campo)
        if placeholder:
            base_attrs['placeholder'] = placeholder
        
        if campo.tipo_dato == 'TEXTO':
            field = forms.CharField(
                label=campo.nombre_campo,
                required=campo.is_required,
                max_length=255,
                widget=forms.TextInput(attrs=base_attrs),
                help_text=self._get_help_text(campo)
            )
        
        elif campo.tipo_dato == 'NUMERO':
            field = forms.CharField(
                label=campo.nombre_campo,
                required=campo.is_required,
                widget=forms.TextInput(attrs={
                    **base_attrs,
                    'pattern': r'[0-9\-\.\s]*',
                    'inputmode': 'numeric'
                }),
                help_text=self._get_help_text(campo, "Solo números, guiones y puntos")
            )
            # Agregar validador personalizado
            field.validators.append(self._validate_numero)
        
        elif campo.tipo_dato == 'FECHA':
            field = forms.DateField(
                label=campo.nombre_campo,
                required=campo.is_required,
                widget=forms.DateInput(attrs={
                    **base_attrs,
                    'type': 'date',
                    'class': 'form-control'
                }),
                help_text=self._get_help_text(campo, "Seleccione una fecha")
            )
        
        elif campo.tipo_dato == 'EMAIL':
            field = forms.EmailField(
                label=campo.nombre_campo,
                required=campo.is_required,
                widget=forms.EmailInput(attrs={
                    **base_attrs,
                    'autocomplete': 'email',
                    'inputmode': 'email'
                }),
                help_text=self._get_help_text(campo, "ejemplo@correo.com")
            )
        
        elif campo.tipo_dato == 'TELEFONO':
            field = forms.CharField(
                label=campo.nombre_campo,
                required=campo.is_required,
                max_length=20,
                widget=forms.TextInput(attrs={
                    **base_attrs,
                    'type': 'tel',
                    'pattern': r'[\+]?[0-9\-\(\)\s]*',
                    'inputmode': 'tel',
                    'autocomplete': 'tel'
                }),
                help_text=self._get_help_text(campo, "+595 21 123456 o 021123456")
            )
            field.validators.append(self._validate_telefono)
        
        elif campo.tipo_dato == 'URL':
            field = forms.URLField(
                label=campo.nombre_campo,
                required=campo.is_required,
                widget=forms.URLInput(attrs={
                    **base_attrs,
                    'autocomplete': 'url',
                    'inputmode': 'url'
                }),
                help_text=self._get_help_text(campo, "https://ejemplo.com")
            )
        
        else:
            # Fallback a texto
            field = forms.CharField(
                label=campo.nombre_campo,
                required=campo.is_required,
                max_length=255,
                widget=forms.TextInput(attrs=base_attrs),
                help_text=self._get_help_text(campo)
            )
        
        return field

    def _get_placeholder(self, campo):
        """Generar placeholder contextual según el tipo y nombre del campo"""
        nombre_lower = campo.nombre_campo.lower()
        
        if campo.tipo_dato == 'EMAIL':
            return "ejemplo@correo.com"
        elif campo.tipo_dato == 'TELEFONO':
            return "+595 21 123456"
        elif campo.tipo_dato == 'URL':
            return "https://ejemplo.com"
        elif campo.tipo_dato == 'NUMERO':
            if 'cuenta' in nombre_lower or 'cbu' in nombre_lower:
                return "123456789012345678"
            elif 'tarjeta' in nombre_lower:
                return "1234 5678 9012 3456"
            elif 'dni' in nombre_lower or 'cedula' in nombre_lower:
                return "12345678"
            else:
                return "Ingrese un número"
        else:
            return f"Ingrese {campo.nombre_campo.lower()}"

    def _get_help_text(self, campo, extra_text=None):
        """Generar texto de ayuda contextual"""
        base_text = f"Campo para {campo.get_tipo_dato_display().lower()}"
        if extra_text:
            base_text += f" - {extra_text}"
        if not campo.is_required:
            base_text += " (Opcional)"
        return base_text

    def _validate_numero(self, value):
        """Validador personalizado para campos numéricos"""
        if not value.strip():
            return
        
        # Permitir números, guiones, puntos y espacios
        if not re.match(r'^[0-9\-\.\s]+$', value):
            raise ValidationError('Solo se permiten números, guiones, puntos y espacios.')
        
        # Verificar que tenga al menos un dígito
        if not re.search(r'\d', value):
            raise ValidationError('Debe contener al menos un número.')

    def _validate_telefono(self, value):
        """Validador personalizado para teléfonos"""
        if not value.strip():
            return
        
        # Limpiar el valor para validación
        clean_value = re.sub(r'[\s\-\(\)]', '', value)
        
        # Permitir + al inicio
        if clean_value.startswith('+'):
            clean_value = clean_value[1:]
        
        # Verificar que solo contenga dígitos después de limpiar
        if not clean_value.isdigit():
            raise ValidationError('Formato de teléfono inválido.')
        
        # Verificar longitud mínima y máxima
        if len(clean_value) < 6:
            raise ValidationError('El teléfono debe tener al menos 6 dígitos.')
        if len(clean_value) > 15:
            raise ValidationError('El teléfono no puede tener más de 15 dígitos.')

    def clean(self):
        """Validación a nivel de formulario"""
        cleaned_data = super().clean()
        
        # Validar que el cliente esté asignado
        if not self.cliente:
            raise ValidationError('No se ha especificado el cliente.')
        
        # Validar medio de pago
        if not self.medio_de_pago_obj:
            raise ValidationError('No se ha especificado el medio de pago.')
        
        # Validar campos dinámicos
        if self.medio_de_pago_obj:
            self._validate_dynamic_fields(cleaned_data)
        
        # Validar es_principal si es necesario
        es_principal = cleaned_data.get('es_principal', False)
        if es_principal and self.cliente:
            # Verificar si ya hay otro medio principal (solo en creación)
            if not self.instance.pk:
                existing_principal = ClienteMedioDePago.objects.filter(
                    cliente=self.cliente,
                    es_principal=True
                ).exists()
                
                if existing_principal:
                    # No es error, simplemente se cambiará el principal
                    pass
        
        return cleaned_data

    def _validate_dynamic_fields(self, cleaned_data):
        """Validar campos dinámicos específicos"""
        errors = {}
        campos = self.medio_de_pago_obj.campos.all()
        
        for campo in campos:
            field_name = f'campo_{campo.id}'
            valor = cleaned_data.get(field_name)
            
            # Validar campos requeridos
            if campo.is_required and (not valor or str(valor).strip() == ''):
                errors[field_name] = f'El campo {campo.nombre_campo} es requerido.'
                continue
            
            # Validaciones específicas por tipo (adicionales a las del campo)
            if valor and str(valor).strip():
                try:
                    self._validate_field_specific(campo, valor)
                except ValidationError as e:
                    errors[field_name] = str(e)
        
        if errors:
            raise ValidationError(errors)

    def _validate_field_specific(self, campo, valor):
        """Validaciones específicas adicionales por tipo de campo"""
        valor_str = str(valor).strip()
        
        if campo.tipo_dato == 'EMAIL':
            # Validación adicional de email
            if '@' not in valor_str or '.' not in valor_str.split('@')[-1]:
                raise ValidationError('Formato de email inválido.')
        
        elif campo.tipo_dato == 'URL':
            # Validación básica de URL
            if not (valor_str.startswith('http://') or valor_str.startswith('https://')):
                raise ValidationError('La URL debe comenzar con http:// o https://')

    def save(self, commit=True):
        """Guardar instancia con datos dinámicos"""
        instance = super().save(commit=False)
        
        # Establecer el cliente
        if self.cliente:
            instance.cliente = self.cliente
        
        # Guardar datos dinámicos
        if self.medio_de_pago_obj:
            datos_campos = {}
            campos = self.medio_de_pago_obj.campos.all()
            
            for campo in campos:
                field_name = f'campo_{campo.id}'
                valor = self.cleaned_data.get(field_name)
                if valor is not None and str(valor).strip():
                    # Limpiar el valor según el tipo
                    valor_limpio = self._clean_field_value(campo, valor)
                    datos_campos[campo.nombre_campo] = valor_limpio
            
            instance.datos_campos = datos_campos
        
        # Manejar el campo es_principal
        if instance.es_principal and self.cliente:
            # Desmarcar otros medios como principales
            ClienteMedioDePago.objects.filter(
                cliente=self.cliente,
                es_principal=True
            ).exclude(pk=instance.pk).update(es_principal=False)
        
        if commit:
            instance.save()
        
        return instance

    def _clean_field_value(self, campo, valor):
        """Limpiar valor según el tipo de campo"""
        valor_str = str(valor).strip()
        
        if campo.tipo_dato == 'NUMERO':
            # Mantener formato original pero limpiar espacios excesivos
            return re.sub(r'\s+', ' ', valor_str)
        elif campo.tipo_dato == 'TELEFONO':
            # Normalizar formato de teléfono
            return re.sub(r'\s+', ' ', valor_str)
        elif campo.tipo_dato == 'EMAIL':
            return valor_str.lower()
        elif campo.tipo_dato == 'URL':
            return valor_str.lower()
        else:
            return valor_str


class ClienteMedioDePagoBulkForm(forms.Form):
    """
    Formulario para operaciones en lote sobre medios de pago
    """
    ACCIONES = [
        ('', 'Seleccionar acción'),
        ('activar', 'Activar seleccionados'),
        ('desactivar', 'Desactivar seleccionados'),
        ('exportar', 'Exportar seleccionados'),
    ]
    
    accion = forms.ChoiceField(
        choices=ACCIONES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Acción a realizar"
    )
    
    medios_seleccionados = forms.ModelMultipleChoiceField(
        queryset=ClienteMedioDePago.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        label="Medios de pago"
    )
    
    def __init__(self, cliente=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if cliente:
            self.fields['medios_seleccionados'].queryset = ClienteMedioDePago.objects.filter(
                cliente=cliente
            ).select_related('medio_de_pago')