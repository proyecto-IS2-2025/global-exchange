"""
Formularios para la gestión de medios de pago de clientes.
"""
import logging

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Count

from ..models import ClienteMedioDePago
from medios_pago.models import MedioDePago, CampoMedioDePago

logger = logging.getLogger(__name__)


class SelectMedioDePagoForm(forms.Form):
    """
    Formulario para seleccionar el tipo de medio de pago antes de agregar.
    FILTRO: Solo muestra medios de pago con campos configurados y activos.
    """
    medio_de_pago = forms.ModelChoiceField(
        queryset=None,
        label='Tipo de Medio de Pago',
        empty_label='Seleccione un medio de pago',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        help_text='Seleccione el tipo de medio de pago que desea agregar'
    )

    def __init__(self, cliente=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if cliente:
            # Obtener medios de pago ya asociados al cliente
            medios_existentes = ClienteMedioDePago.objects.filter(
                cliente=cliente
            ).values_list('medio_de_pago_id', flat=True)

            # Filtrar solo medios activos que NO estén ya asociados al cliente
            # Y que tengan al menos un campo configurado
            self.fields['medio_de_pago'].queryset = MedioDePago.objects.filter(
                is_active=True
            ).exclude(
                id__in=medios_existentes
            ).annotate(
                total_campos=Count('campos', distinct=True)
            ).filter(
                total_campos__gt=0  # Solo medios con al menos 1 campo
            ).order_by('nombre')


class ClienteMedioDePagoCompleteForm(forms.ModelForm):
    """
    Formulario mejorado para crear/editar medios de pago de clientes.
    Genera campos dinámicos basados en la configuración del medio de pago.
    """
    
    class Meta:
        model = ClienteMedioDePago
        fields = ['es_principal', 'es_activo']
        widgets = {
            'es_principal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'es_activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, cliente=None, medio_de_pago=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.cliente = cliente
        self.medio_de_pago = medio_de_pago

        logger.debug(f"__init__: cliente={cliente}, medio_de_pago={medio_de_pago}")

        if not medio_de_pago:
            if self.instance and self.instance.pk:
                self.medio_de_pago = self.instance.medio_de_pago
            else:
                raise ValueError("Se debe proporcionar medio_de_pago")

        # Generar campos dinámicos
        self._generar_campos_dinamicos()

        # Si estamos editando, pre-llenar los campos
        if self.instance and self.instance.pk:
            self._prellenar_campos_dinamicos()

    def _generar_campos_dinamicos(self):
        """Genera campos del formulario basados en CampoMedioDePago."""
        if not self.medio_de_pago:
            return

        campos = self.medio_de_pago.campos.all().order_by('orden', 'id')
        logger.debug(f"Generando {campos.count()} campos para {self.medio_de_pago.nombre}")

        for campo in campos:
            field_name = f'campo_{campo.id}'
            
            # Determinar widget según tipo de dato
            widget_attrs = {
                'class': 'form-control',
                'placeholder': campo.descripcion or f'Ingrese {campo.nombre_campo}'
            }

            if campo.tipo_dato == 'NUMERO':
                field = forms.CharField(
                    label=campo.nombre_campo,
                    required=campo.is_required,
                    widget=forms.TextInput(attrs=widget_attrs),
                    help_text=campo.descripcion
                )
            elif campo.tipo_dato == 'TEXTO':
                field = forms.CharField(
                    label=campo.nombre_campo,
                    required=campo.is_required,
                    widget=forms.TextInput(attrs=widget_attrs),
                    help_text=campo.descripcion
                )
            elif campo.tipo_dato == 'EMAIL':
                field = forms.EmailField(
                    label=campo.nombre_campo,
                    required=campo.is_required,
                    widget=forms.EmailInput(attrs=widget_attrs),
                    help_text=campo.descripcion
                )
            elif campo.tipo_dato == 'TELEFONO':
                field = forms.CharField(
                    label=campo.nombre_campo,
                    required=campo.is_required,
                    widget=forms.TextInput(attrs=widget_attrs),
                    help_text=campo.descripcion
                )
            elif campo.tipo_dato == 'FECHA':
                widget_attrs['type'] = 'date'
                field = forms.DateField(
                    label=campo.nombre_campo,
                    required=campo.is_required,
                    widget=forms.DateInput(attrs=widget_attrs),
                    help_text=campo.descripcion
                )
            else:
                field = forms.CharField(
                    label=campo.nombre_campo,
                    required=campo.is_required,
                    widget=forms.TextInput(attrs=widget_attrs),
                    help_text=campo.descripcion
                )

            self.fields[field_name] = field

    def _prellenar_campos_dinamicos(self):
        """Pre-llena los campos dinámicos con datos existentes."""
        if not self.instance.datos_campos:
            return

        logger.debug(f"Pre-llenando campos con: {self.instance.datos_campos}")

        for campo in self.medio_de_pago.campos.all():
            field_name = f'campo_{campo.id}'
            valor = self.instance.datos_campos.get(campo.nombre_campo)
            
            if valor and field_name in self.fields:
                self.fields[field_name].initial = valor
                logger.debug(f"Campo {field_name} pre-llenado con: {valor}")

    def clean(self):
        """Validación general del formulario."""
        cleaned_data = super().clean()
        
        # Construir datos_campos desde los campos dinámicos
        datos_campos = {}
        
        for campo in self.medio_de_pago.campos.all():
            field_name = f'campo_{campo.id}'
            valor = cleaned_data.get(field_name)
            
            if valor:
                # Limpiar espacios
                if isinstance(valor, str):
                    valor = valor.strip()
                
                datos_campos[campo.nombre_campo] = valor
            elif campo.is_required:
                self.add_error(
                    field_name,
                    f'El campo {campo.nombre_campo} es obligatorio.'
                )

        logger.debug(f"clean() - datos_campos construidos: {datos_campos}")
        
        # Guardar temporalmente para usarlo en save()
        self._datos_campos_temp = datos_campos
        
        return cleaned_data

    def save(self, commit=True):
        """Guardar el medio de pago con los datos de campos dinámicos."""
        instance = super().save(commit=False)
        
        # Asignar cliente y medio de pago
        if self.cliente:
            instance.cliente = self.cliente
        if self.medio_de_pago:
            instance.medio_de_pago = self.medio_de_pago

        # Asignar datos de campos dinámicos
        if hasattr(self, '_datos_campos_temp'):
            instance.datos_campos = self._datos_campos_temp
            logger.debug(f"save() - Asignando datos_campos: {instance.datos_campos}")

        # Verificar si debe ser principal automáticamente
        if not instance.pk and not instance.es_principal:
            otros_medios = ClienteMedioDePago.objects.filter(
                cliente=instance.cliente
            ).exists()
            
            if not otros_medios:
                instance.es_principal = True

        if commit:
            instance.save()
            logger.debug(f"save() - Guardado con ID: {instance.pk}")

        return instance



class ClienteMedioDePagoBulkForm(forms.Form):
    """
    Formulario para crear múltiples medios de pago de una vez.
    Útil para importación masiva.
    """
    medio_de_pago = forms.ModelChoiceField(
        queryset=MedioDePago.objects.filter(is_active=True),
        label='Tipo de Medio de Pago',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    datos_csv = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Pegue los datos en formato CSV...'
        }),
        label='Datos CSV',
        help_text='Formato: campo1,campo2,campo3 (una línea por registro)'
    )

    def __init__(self, cliente=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cliente = cliente

    def clean_datos_csv(self):
        """Validar formato CSV."""
        datos = self.cleaned_data.get('datos_csv', '').strip()
        
        if not datos:
            raise ValidationError('Debe proporcionar datos CSV.')
        
        lineas = [l.strip() for l in datos.split('\n') if l.strip()]
        
        if len(lineas) < 1:
            raise ValidationError('Debe proporcionar al menos una línea de datos.')
        
        return lineas

    def save(self):
        """Procesar y guardar múltiples medios de pago."""
        medio_de_pago = self.cleaned_data['medio_de_pago']
        lineas = self.cleaned_data['datos_csv']
        campos = list(medio_de_pago.campos.all().order_by('orden', 'id'))
        
        creados = []
        errores = []
        
        for i, linea in enumerate(lineas, 1):
            try:
                valores = [v.strip() for v in linea.split(',')]
                
                if len(valores) != len(campos):
                    errores.append(f'Línea {i}: Número de campos incorrecto')
                    continue
                
                datos_campos = {
                    campo.nombre_campo: valor
                    for campo, valor in zip(campos, valores)
                }
                
                medio = ClienteMedioDePago.objects.create(
                    cliente=self.cliente,
                    medio_de_pago=medio_de_pago,
                    datos_campos=datos_campos,
                    es_activo=True,
                    es_principal=False
                )
                
                creados.append(medio)
                
            except Exception as e:
                errores.append(f'Línea {i}: {str(e)}')
        
        return {
            'creados': creados,
            'errores': errores,
            'total': len(lineas)
        }