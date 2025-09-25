from .models import Cliente, AsignacionCliente, Descuento, LimiteDiario, LimiteMensual
from django import forms
from datetime import datetime, date
from django.utils import timezone


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


class LimiteDiarioForm(forms.ModelForm):
    class Meta:
        model = LimiteDiario
        fields = ["fecha", "monto"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "monto": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        hoy = datetime.today().date()

        if instance.fecha == hoy:
            instance.inicio_vigencia = timezone.now()
        else:
            naive = datetime(instance.fecha.year, instance.fecha.month, instance.fecha.day, 0, 0)
            instance.inicio_vigencia = timezone.make_aware(naive)  # ✅ convierte a aware según tu settings

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
        print(">>> CLEAN_MES recibido:", fecha, type(fecha))
        # Normalizar siempre al día 1
        fecha = date(fecha.year, fecha.month, 1)

        # No permitir meses pasados
        hoy = timezone.localdate()
        if fecha < date(hoy.year, hoy.month, 1):
            raise forms.ValidationError("No se pueden registrar límites en meses pasados.")

        # Evitar duplicados
        if LimiteMensual.objects.filter(mes=fecha).exists():
            raise forms.ValidationError("Ya existe un límite configurado para este mes.")

        return fecha

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
