from .models import Cliente, AsignacionCliente, Descuento, LimiteDiario, LimiteMensual
from django import forms
from datetime import datetime, date, time
from django.utils import timezone
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
    Formulario para seleccionar el tipo de medio de pago - PERMITIR DUPLICADOS
    """
    medio_de_pago = forms.ModelChoiceField(
        queryset=MedioDePago.objects.none(),
        empty_label="Seleccione un medio de pago",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'data-placeholder': 'Seleccione un tipo de medio de pago...'
        }),
        label="Tipo de medio de pago",
        help_text="Puede agregar múltiples medios del mismo tipo (ej: varias tarjetas de crédito)."
    )

    def __init__(self, cliente=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if cliente:
            # PERMITIR TODOS LOS MEDIOS ACTIVOS - NO FILTRAR POR YA ASOCIADOS
            self.fields['medio_de_pago'].queryset = MedioDePago.objects.filter(
                is_active=True
            ).order_by('nombre')

            # Mensaje actualizado
            total_medios = self.fields['medio_de_pago'].queryset.count()
            if total_medios > 0:
                self.fields['medio_de_pago'].help_text = (
                    f"Seleccione el tipo de medio de pago que desea configurar. "
                    f"Puede agregar múltiples medios del mismo tipo."
                )


class ClienteMedioDePagoCompleteForm(forms.ModelForm):
    """
    Formulario con validación estricta que BLOQUEA duplicados
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
            self.fields['medio_de_pago'].initial = self.medio_de_pago_obj.id
            self.fields['medio_de_pago'].queryset = MedioDePago.objects.filter(
                id=self.medio_de_pago_obj.id
            )
            self.initial['medio_de_pago'] = self.medio_de_pago_obj.id
        else:
            self.fields['medio_de_pago'].required = False

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
        try:
            campos = self.medio_de_pago_obj.campos.all().order_by('orden', 'id')

            for campo in campos:
                field_name = f'campo_{campo.id}'
                field = self._create_field_by_type(campo)

                # Establecer valor inicial si existe
                if self.instance and self.instance.pk:
                    initial_value = self.instance.get_dato_campo(campo.nombre_campo)
                    if initial_value:
                        field.initial = initial_value

                self.fields[field_name] = field
        except Exception as e:
            print(f"Error generando campos dinámicos: {e}")

    def _create_field_by_type(self, campo):
        """Crear campo del formulario según el tipo de dato"""
        base_attrs = {
            'class': 'form-control',
            'data-campo-tipo': campo.tipo_dato,
            'data-campo-id': campo.id
        }

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

    def clean(self):
        """Validación ESTRICTA que BLOQUEA duplicados automáticamente"""
        cleaned_data = super().clean()

        print("=== DEBUG VALIDACIÓN DUPLICADOS ===")
        print(f"Cliente: {self.cliente}")
        print(f"Medio de pago: {self.medio_de_pago_obj}")
        print(f"Cleaned data: {cleaned_data}")

        # Validaciones básicas
        if not self.cliente:
            raise ValidationError('No se ha especificado el cliente.')

        if not self.medio_de_pago_obj:
            raise ValidationError('No se ha especificado el medio de pago.')

        # Asegurar que el medio de pago esté en cleaned_data
        if not cleaned_data.get('medio_de_pago'):
            cleaned_data['medio_de_pago'] = self.medio_de_pago_obj

        # VALIDACIÓN ESTRICTA DE DUPLICADOS
        duplicado_encontrado = self._check_strict_duplicates()
        if duplicado_encontrado:
            raise ValidationError({
                '__all__': f'Ya existe un medio de pago idéntico: {duplicado_encontrado["mensaje"]}'
            })

        # Validar campos dinámicos
        self._validate_dynamic_fields(cleaned_data)

        return cleaned_data

    def _check_strict_duplicates(self):
        """
        Verificación ESTRICTA de duplicados - BLOQUEA si encuentra exactamente lo mismo
        """
        if not self.cliente or not self.medio_de_pago_obj:
            return None

        # Obtener medios existentes del mismo tipo
        existing_medios = ClienteMedioDePago.objects.filter(
            cliente=self.cliente,
            medio_de_pago=self.medio_de_pago_obj
        )

        # Excluir el objeto actual si estamos editando
        if self.instance.pk:
            existing_medios = existing_medios.exclude(pk=self.instance.pk)

        if not existing_medios.exists():
            return None

        # Recopilar datos actuales del formulario
        current_data = {}
        for campo in self.medio_de_pago_obj.campos.all():
            field_name = f'campo_{campo.id}'
            valor = self.cleaned_data.get(field_name)
            if valor is not None:
                valor_normalizado = self._normalize_for_comparison(str(valor).strip(), campo.tipo_dato)
                if valor_normalizado:  # Solo incluir si no está vacío
                    current_data[campo.nombre_campo] = valor_normalizado

        print(f"Datos actuales normalizados: {current_data}")

        # Comparar con medios existentes
        for existing in existing_medios:
            if self._is_exact_duplicate(current_data, existing):
                return {
                    'mensaje': f'"{existing.medio_de_pago.nombre}" con los mismos datos ya existe',
                    'existing_id': existing.id
                }

        return None

    def _is_exact_duplicate(self, current_data, existing_medio):
        """
        Determinar si es un duplicado EXACTO comparando todos los campos importantes
        """
        existing_data = existing_medio.datos_campos or {}

        print(f"Comparando actual: {current_data}")
        print(f"Con existente: {existing_data}")

        # Si no hay datos en ninguno de los dos, no es duplicado
        if not current_data and not existing_data:
            return False

        # Obtener campos críticos que deben coincidir
        critical_fields = self._get_critical_fields()

        critical_matches = 0
        total_critical = 0

        # Verificar campos críticos
        for campo_name, current_value in current_data.items():
            if self._is_critical_field(campo_name, critical_fields):
                total_critical += 1
                existing_value = existing_data.get(campo_name)

                if existing_value:
                    # Normalizar valor existente para comparación
                    campo_obj = self._get_campo_by_name(campo_name)
                    if campo_obj:
                        existing_normalized = self._normalize_for_comparison(
                            str(existing_value),
                            campo_obj.tipo_dato
                        )

                        print(f"Campo crítico '{campo_name}': '{current_value}' vs '{existing_normalized}'")

                        if current_value == existing_normalized:
                            critical_matches += 1

        # Es duplicado si coinciden TODOS los campos críticos y hay al menos uno
        if total_critical > 0 and critical_matches == total_critical:
            print(f"DUPLICADO DETECTADO: {critical_matches}/{total_critical} campos críticos coinciden")
            return True

        # Verificación adicional: si tienen exactamente los mismos datos
        if self._have_identical_data(current_data, existing_data):
            print("DUPLICADO DETECTADO: datos idénticos")
            return True

        return False

    def _get_critical_fields(self):
        """
        Definir campos críticos que no deberían duplicarse
        """
        return {
            'numero', 'cuenta', 'tarjeta', 'cbu', 'numero_cuenta',
            'numero_tarjeta', 'email', 'correo', 'usuario'
        }

    def _is_critical_field(self, field_name, critical_fields):
        """
        Verificar si un campo es crítico comparando con palabras clave
        """
        field_lower = field_name.lower()
        return any(critical in field_lower for critical in critical_fields)

    def _get_campo_by_name(self, campo_name):
        """
        Obtener objeto Campo por su nombre
        """
        try:
            return self.medio_de_pago_obj.campos.filter(nombre_campo=campo_name).first()
        except:
            return None

    def _have_identical_data(self, current_data, existing_data):
        """
        Verificar si dos conjuntos de datos son idénticos
        """
        # Normalizar ambos conjuntos
        current_normalized = {k: v for k, v in current_data.items() if v}
        existing_normalized = {}

        for k, v in existing_data.items():
            if v:
                campo_obj = self._get_campo_by_name(k)
                if campo_obj:
                    normalized_val = self._normalize_for_comparison(str(v), campo_obj.tipo_dato)
                    if normalized_val:
                        existing_normalized[k] = normalized_val

        # Comparar si son exactamente iguales
        return current_normalized == existing_normalized

    def _normalize_for_comparison(self, value, tipo_dato):
        """
        Normalizar valor para comparación estricta
        """
        if not value:
            return ''

        value_str = str(value).strip()

        if tipo_dato in ['NUMERO', 'TELEFONO']:
            # Remover todos los espacios, guiones, puntos y paréntesis
            normalized = re.sub(r'[\s\-\.\(\)]', '', value_str)
            return normalized.upper()
        elif tipo_dato == 'EMAIL':
            return value_str.lower()
        elif tipo_dato == 'URL':
            return value_str.lower().rstrip('/')
        else:
            return value_str.upper()

    def _validate_dynamic_fields(self, cleaned_data):
        """Validar formato de campos dinámicos"""
        if not self.medio_de_pago_obj:
            return

        errors = {}

        for campo in self.medio_de_pago_obj.campos.all():
            field_name = f'campo_{campo.id}'
            valor = cleaned_data.get(field_name, '').strip() if cleaned_data.get(field_name) else ''

            # Validar campos requeridos
            if campo.is_required and not valor:
                errors[field_name] = f'El campo {campo.nombre_campo} es requerido.'
                continue

            # Validar formato si hay valor
            if valor:
                try:
                    self._validate_field_format(campo, valor)
                except ValidationError as e:
                    errors[field_name] = str(e)

        if errors:
            raise ValidationError(errors)

    def _validate_field_format(self, campo, valor):
        """Validar formato de campo específico"""
        valor_str = str(valor).strip()

        if campo.tipo_dato == 'NUMERO':
            if not re.match(r'^[0-9\-\.\s]+$', valor_str):
                raise ValidationError('Solo se permiten números, guiones, puntos y espacios.')
            if not re.search(r'\d', valor_str):
                raise ValidationError('Debe contener al menos un número.')

        elif campo.tipo_dato == 'TELEFONO':
            clean_value = re.sub(r'[\s\-\(\)]', '', valor_str)
            if clean_value.startswith('+'):
                clean_value = clean_value[1:]

            if not clean_value.isdigit():
                raise ValidationError('Formato de teléfono inválido.')
            if len(clean_value) < 6:
                raise ValidationError('El teléfono debe tener al menos 6 dígitos.')
            if len(clean_value) > 15:
                raise ValidationError('El teléfono no puede tener más de 15 dígitos.')

        elif campo.tipo_dato == 'EMAIL':
            if '@' not in valor_str or '.' not in valor_str.split('@')[-1]:
                raise ValidationError('Formato de email inválido.')

        elif campo.tipo_dato == 'URL':
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
                if valor is not None:
                    valor_str = str(valor).strip()
                    if valor_str:  # Solo guardar si no está vacío
                        valor_limpio = self._clean_field_value(campo, valor_str)
                        datos_campos[campo.nombre_campo] = valor_limpio

            instance.datos_campos = datos_campos

        # Manejar el campo es_principal
        if instance.es_principal and self.cliente:
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
            return re.sub(r'\s+', ' ', valor_str)
        elif campo.tipo_dato == 'TELEFONO':
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


class LimiteDiarioForm(forms.ModelForm):
    class Meta:
        model = LimiteDiario
        fields = ["fecha", "monto"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "monto": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
        }

    class Meta:
        model = LimiteDiario
        fields = ['fecha', 'monto']

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        hoy = timezone.localdate()
        if fecha < hoy:
            raise forms.ValidationError("No se pueden registrar límites en fechas pasadas.")

        # --- Lógica de exclusión de duplicados (está correcta) ---
        qs = LimiteDiario.objects.filter(fecha=fecha)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise forms.ValidationError("Ya existe un límite configurado para esta fecha.")

        return fecha

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # -------------------------------------------------------------------
        # CAMBIO CRUCIAL: Solo establecer inicio_vigencia si es una creación.
        # En la edición, usamos la fecha del modelo para calcular el inicio del día/mes.
        # -------------------------------------------------------------------
        if not instance.pk: # Si es un objeto nuevo
            fecha = instance.fecha
            hoy = timezone.localdate()
            
            # Si la fecha es hoy, aplica de inmediato. Si es futuro, aplica a las 00:00.
            if fecha == hoy:
                instance.inicio_vigencia = timezone.now()
            else:
                naive = datetime.combine(fecha, time.min)
                instance.inicio_vigencia = timezone.make_aware(naive)

        if commit:
            instance.save()
        return instance

class LimiteMensualForm(forms.ModelForm):
    # ... (clase Meta, widgets, clean_mes) ...
    class Meta:
        model = LimiteMensual
        fields = ['mes', 'monto']
        widgets = {
            'mes': forms.DateInput(attrs={'type': 'month'}, format='%Y-%m'),
        }

    # ... (clean_mes está correcto) ...
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # -------------------------------------------------------------------
        # CAMBIO CRUCIAL: Solo establecer inicio_vigencia si es una creación.
        # -------------------------------------------------------------------
        if not instance.pk: # Si es un objeto nuevo
            fecha = instance.mes
            hoy = timezone.localdate()

            if fecha.year == hoy.year and fecha.month == hoy.month:
                instance.inicio_vigencia = timezone.now()
            else:
                naive = datetime(fecha.year, fecha.month, 1, 0, 0)
                instance.inicio_vigencia = timezone.make_aware(naive)

        if commit:
            instance.save()
        return instance



class LimiteMensualForm(forms.ModelForm):
    mes = forms.DateField(
        input_formats=["%Y-%m"],
        widget=forms.DateInput(attrs={"type": "month", "class": "form-control"}),
        help_text="Selecciona el mes (se guardará como el primer día del mes)"
    )

    class Meta:
        model = LimiteMensual
        fields = ["mes", "monto"]
        widgets = {
            "monto": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
        }

    def clean_mes(self):
        fecha = self.cleaned_data["mes"]
        # Normalizar siempre al día 1 (esta parte está correcta)
        fecha = date(fecha.year, fecha.month, 1)

        # No permitir meses pasados (esta parte está correcta)
        hoy = timezone.localdate()
        if fecha < date(hoy.year, hoy.month, 1):
            raise forms.ValidationError("No se pueden registrar límites en meses pasados.")

        # --- NUEVA LÓGICA: Excluir el objeto que se está editando de la búsqueda de duplicados ---
        qs = LimiteMensual.objects.filter(mes=fecha)

        if self.instance.pk:
            # Si self.instance.pk existe, estamos editando. Excluimos ese registro.
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise forms.ValidationError("Ya existe un límite configurado para este mes.")

        return fecha

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = timezone.localdate()
        self.fields["mes"].initial = hoy.strftime("%Y-%m")
    def save(self, commit=True):
        instance = super().save(commit=False)
        print(">>> SAVE.instance.mes antes:", instance.mes, type(instance.mes))
        fecha = instance.mes
        hoy = timezone.localdate()

        if fecha.year == hoy.year and fecha.month == hoy.month:
            instance.inicio_vigencia = timezone.now()
        else:
            naive = datetime(fecha.year, fecha.month, 1, 0, 0)
            instance.inicio_vigencia = timezone.make_aware(naive)

        if commit:
            instance.save()
            print(">>> GUARDADO OK con ID:", instance.id)
        return instance
