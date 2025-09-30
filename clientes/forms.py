"""
Formularios para la gestión de clientes y sus datos relacionados.
"""
# Imports estándar de Python
from datetime import datetime, date, time
import re
import logging

# Imports de Django
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import HiddenInput
from django.utils import timezone

# Imports de modelos propios
from .models import (
    Cliente, 
    Segmento, 
    AsignacionCliente, 
    Descuento, 
    LimiteDiario, 
    LimiteMensual,
    ClienteMedioDePago
)

# Imports de otras apps
from medios_pago.models import MedioDePago, CampoMedioDePago

logger = logging.getLogger(__name__)


# ============================================================================
# FORMULARIOS DE CLIENTE
# ============================================================================

class ClienteForm(forms.ModelForm):
    """Formulario para crear/editar clientes."""
    
    class Meta:
        model = Cliente
        fields = [
            'cedula', 
            'nombre_completo', 
            'direccion', 
            'telefono', 
            'email',
            'segmento', 
            'tipo_cliente', 
            'esta_activo'
        ]
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
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'segmento': forms.Select(attrs={'class': 'form-select'}),
            'tipo_cliente': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ejemplo: minorista / mayorista'
            }),
            'esta_activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'cedula': 'Cédula',
            'nombre_completo': 'Nombre Completo',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'email': 'Correo Electrónico',
            'segmento': 'Segmento',
            'tipo_cliente': 'Tipo de Cliente',
            'esta_activo': 'Activo',
        }

    def clean_cedula(self):
        """Validar formato de cédula."""
        cedula = self.cleaned_data.get('cedula', '').strip()
        
        if not cedula:
            raise ValidationError('La cédula es obligatoria.')
        
        if not cedula.isdigit():
            raise ValidationError('La cédula solo debe contener números.')
        
        if len(cedula) < 6:
            raise ValidationError('La cédula debe tener al menos 6 dígitos.')
        
        # Verificar duplicados (excluir el objeto actual si estamos editando)
        qs = Cliente.objects.filter(cedula=cedula)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('Ya existe un cliente con esta cédula.')
        
        return cedula

    def clean_email(self):
        """Validar formato de email."""
        email = self.cleaned_data.get('email', '').strip()
        
        if email:
            # Verificar duplicados (excluir el objeto actual si estamos editando)
            qs = Cliente.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError('Ya existe un cliente con este correo electrónico.')
        
        return email


class SeleccionClienteForm(forms.Form):
    """Formulario para que un usuario seleccione entre sus clientes asignados."""
    
    cliente = forms.ModelChoiceField(
        queryset=None,
        empty_label="Seleccione un cliente",
        label="Cliente asignado",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener clientes asignados al usuario
        asignaciones = AsignacionCliente.objects.filter(
            usuario=user
        ).select_related('cliente', 'cliente__segmento')
        
        self.fields['cliente'].queryset = Cliente.objects.filter(
            id__in=asignaciones.values_list('cliente_id', flat=True),
            esta_activo=True
        )
        
        # Personalizar la visualización del select
        self.fields['cliente'].label_from_instance = lambda obj: (
            f"{obj.nombre_completo} - {obj.cedula} ({obj.segmento.name})"
        )


# ============================================================================
# FORMULARIOS DE DESCUENTO
# ============================================================================

class DescuentoForm(forms.ModelForm):
    """Formulario para gestionar descuentos por segmento."""
    
    class Meta:
        model = Descuento
        fields = ['porcentaje_descuento']
        widgets = {
            'porcentaje_descuento': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
        }
        labels = {
            'porcentaje_descuento': 'Porcentaje de Descuento (%)',
        }

    def clean_porcentaje_descuento(self):
        """Validar que el porcentaje esté en rango válido."""
        porcentaje = self.cleaned_data.get('porcentaje_descuento')
        
        if porcentaje is None:
            raise ValidationError('El porcentaje de descuento es obligatorio.')
        
        if porcentaje < 0:
            raise ValidationError('El porcentaje no puede ser negativo.')
        
        if porcentaje > 100:
            raise ValidationError('El porcentaje no puede ser mayor a 100%.')
        
        return porcentaje


# ============================================================================
# FORMULARIOS DE LÍMITES
# ============================================================================

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


# ============================================================================
# FORMULARIOS DE MEDIOS DE PAGO
# ============================================================================

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
            from django.db.models import Count
            
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
