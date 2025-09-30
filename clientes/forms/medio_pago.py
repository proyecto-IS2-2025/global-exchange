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
        print("\n" + "="*80)
        print("🔍 INICIO __init__ de ClienteMedioDePagoCompleteForm")
        print("="*80)
        
        # 🐛 DEBUG: Verificar argumentos recibidos
        print(f"📥 Args recibidos:")
        print(f"   - cliente: {cliente}")
        print(f"   - medio_de_pago: {medio_de_pago}")
        print(f"   - instance en kwargs: {kwargs.get('instance')}")
        
        if 'instance' in kwargs and kwargs['instance']:
            instance = kwargs['instance']
            print(f"\n📦 MODO EDICIÓN detectado")
            print(f"   - instance.pk: {instance.pk}")
            print(f"   - instance.es_activo: {instance.es_activo}")
            print(f"   - instance.es_principal: {instance.es_principal}")
            print(f"   - type(instance.es_activo): {type(instance.es_activo)}")
        else:
            print(f"\n✨ MODO CREACIÓN detectado (instance es None o sin PK)")
        
        super().__init__(*args, **kwargs)
        
        print(f"\n✅ Después de super().__init__()")
        print(f"   - self.instance.pk: {self.instance.pk}")
        
        if self.instance.pk:
            print(f"   - self.instance.es_activo: {self.instance.es_activo}")
            print(f"   - self.instance.es_principal: {self.instance.es_principal}")
            print(f"   - self.fields['es_activo'].initial: {self.fields['es_activo'].initial}")
            print(f"   - self.fields['es_principal'].initial: {self.fields['es_principal'].initial}")
        
        self.cliente = cliente
        self.medio_de_pago = medio_de_pago

        logger.debug(f"__init__: cliente={cliente}, medio_de_pago={medio_de_pago}")

        if not medio_de_pago:
            if self.instance and self.instance.pk:
                self.medio_de_pago = self.instance.medio_de_pago
                print(f"   - medio_de_pago obtenido de instance: {self.medio_de_pago}")
            else:
                raise ValueError("Se debe proporcionar medio_de_pago")

        # 🔥 DEBUG: Verificar estado de fields ANTES de manipularlos
        print(f"\n🔎 Estado de fields ANTES de modificación:")
        print(f"   - es_activo.initial: {self.fields['es_activo'].initial}")
        print(f"   - es_principal.initial: {self.fields['es_principal'].initial}")
        print(f"   - es_activo.widget: {self.fields['es_activo'].widget}")
        print(f"   - es_activo.widget.attrs: {self.fields['es_activo'].widget.attrs}")
        
        # Solo establecer valores por defecto en CREACIÓN
        if not self.instance.pk:
            self.fields['es_activo'].initial = True
            self.fields['es_principal'].initial = False
            print(f"\n✨ Modo CREACIÓN - Estableciendo valores por defecto")
            print(f"   - es_activo.initial = True")
            print(f"   - es_principal.initial = False")
        else:
            print(f"\n📝 Modo EDICIÓN - Django maneja initial automáticamente")
            print(f"   - NO modificando initial, confiando en Django")
            
            # 🐛 DEBUG ADICIONAL: Forzar verificación
            print(f"\n🔬 Verificación adicional en EDICIÓN:")
            print(f"   - instance.es_activo == True: {self.instance.es_activo == True}")
            print(f"   - instance.es_activo is True: {self.instance.es_activo is True}")
            print(f"   - bool(instance.es_activo): {bool(self.instance.es_activo)}")

        # 🔥 DEBUG: Estado DESPUÉS de modificación
        print(f"\n🔎 Estado de fields DESPUÉS de modificación:")
        print(f"   - es_activo.initial: {self.fields['es_activo'].initial}")
        print(f"   - es_principal.initial: {self.fields['es_principal'].initial}")

        # Generar campos dinámicos
        print(f"\n🔧 Generando campos dinámicos...")
        self._generar_campos_dinamicos()

        # Si estamos editando, pre-llenar los campos
        if self.instance and self.instance.pk:
            print(f"\n📋 Pre-llenando campos dinámicos...")
            self._prellenar_campos_dinamicos()

        print("\n" + "="*80)
        print("✅ FIN __init__ de ClienteMedioDePagoCompleteForm")
        print("="*80 + "\n")

    def _generar_campos_dinamicos(self):
        """Genera campos del formulario basados en CampoMedioDePago."""
        if not self.medio_de_pago:
            print("⚠️ No hay medio_de_pago, saltando generación de campos")
            return

        campos = self.medio_de_pago.campos.all().order_by('orden', 'id')
        print(f"   Generando {campos.count()} campos para {self.medio_de_pago.nombre}")

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
            print(f"   ✓ Campo generado: {field_name}")

    def _prellenar_campos_dinamicos(self):
        """Pre-llena los campos dinámicos con datos existentes."""
        if not self.instance.datos_campos:
            print("   ℹ️ No hay datos_campos, saltando pre-llenado")
            return

        print(f"   Pre-llenando con datos: {self.instance.datos_campos}")

        for campo in self.medio_de_pago.campos.all():
            field_name = f'campo_{campo.id}'
            valor = self.instance.datos_campos.get(campo.nombre_campo)
            
            if valor and field_name in self.fields:
                self.fields[field_name].initial = valor
                print(f"   ✓ Campo {field_name} = {valor}")

    def clean(self):
        """Validación general del formulario."""
        print("\n" + "="*80)
        print("🔍 INICIO clean() de ClienteMedioDePagoCompleteForm")
        print("="*80)
        
        cleaned_data = super().clean()
        
        print(f"\n📥 cleaned_data recibido:")
        print(f"   - es_activo: {cleaned_data.get('es_activo')}")
        print(f"   - es_principal: {cleaned_data.get('es_principal')}")
        print(f"   - type(es_activo): {type(cleaned_data.get('es_activo'))}")
        
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

        print(f"\n📦 datos_campos construidos: {datos_campos}")
        
        # Guardar temporalmente para usarlo en save()
        self._datos_campos_temp = datos_campos
        
        print("\n" + "="*80)
        print("✅ FIN clean()")
        print("="*80 + "\n")
        
        return cleaned_data

    def save(self, commit=True):
        """Guardar el medio de pago con los datos de campos dinámicos."""
        print("\n" + "="*80)
        print("🔍 INICIO save() de ClienteMedioDePagoCompleteForm")
        print("="*80)
        
        instance = super().save(commit=False)
        
        print(f"\n📦 Instance después de super().save(commit=False):")
        print(f"   - instance.pk: {instance.pk}")
        print(f"   - instance.es_activo: {instance.es_activo}")
        print(f"   - instance.es_principal: {instance.es_principal}")
        print(f"   - type(instance.es_activo): {type(instance.es_activo)}")
        
        # Asignar cliente y medio de pago
        if self.cliente:
            instance.cliente = self.cliente
            print(f"   ✓ Cliente asignado: {self.cliente}")
            
        if self.medio_de_pago:
            instance.medio_de_pago = self.medio_de_pago
            print(f"   ✓ Medio de pago asignado: {self.medio_de_pago}")

        # Asignar datos de campos dinámicos
        if hasattr(self, '_datos_campos_temp'):
            instance.datos_campos = self._datos_campos_temp
            print(f"   ✓ datos_campos asignados: {instance.datos_campos}")

        # Verificar si debe ser principal automáticamente
        if not instance.pk and not instance.es_principal:
            otros_medios = ClienteMedioDePago.objects.filter(
                cliente=instance.cliente
            ).exists()
            
            if not otros_medios:
                instance.es_principal = True
                print(f"   ✓ Marcado como principal (primer medio)")

        print(f"\n💾 Antes de guardar en BD:")
        print(f"   - es_activo: {instance.es_activo}")
        print(f"   - es_principal: {instance.es_principal}")

        if commit:
            instance.save()
            print(f"\n✅ Guardado en BD con ID: {instance.pk}")
            
            # 🐛 VERIFICACIÓN POST-GUARDADO
            instance.refresh_from_db()
            print(f"\n🔬 Verificación POST-guardado (refresh_from_db):")
            print(f"   - es_activo en BD: {instance.es_activo}")
            print(f"   - es_principal en BD: {instance.es_principal}")

        print("\n" + "="*80)
        print("✅ FIN save()")
        print("="*80 + "\n")

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