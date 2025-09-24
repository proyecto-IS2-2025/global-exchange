# billetera/forms.py
from django import forms
from decimal import Decimal, InvalidOperation
from banco.models import EntidadBancaria, Cuenta

# --------- FORMULARIO DE RECARGA DESDE BANCO (MEJORADO) ---------
class RecargaForm(forms.Form):
    cuenta_origen = forms.ModelChoiceField(
        queryset=Cuenta.objects.none(),
        label="Selecciona la cuenta de origen",
        widget=forms.Select(attrs={"class": "form-control"}),
        empty_label="-- Selecciona una cuenta --"
    )
    monto = forms.DecimalField(
        label="Monto a recargar",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        max_value=Decimal('1000000.00'),
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.01",
            "placeholder": "Ejemplo: 10000.00"
        })
    )

    def clean_monto(self):
        monto = self.cleaned_data.get("monto")
        if not monto:
            raise forms.ValidationError("El monto es requerido.")
        
        # ✅ Validación adicional con Decimal
        try:
            monto_decimal = Decimal(str(monto))
            if monto_decimal <= 0:
                raise forms.ValidationError("El monto debe ser mayor a cero.")
            if monto_decimal > Decimal('1000000'):
                raise forms.ValidationError("El monto máximo es ₲1,000,000.")
            return monto_decimal
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Ingrese un monto válido.")

# --------- FORMULARIO DE TRANSFERENCIA DESDE BILLETERA A OTRO USUARIO (MEJORADO) ---------
class BilleteraTransferenciaForm(forms.Form):
    destinatario_telefono = forms.CharField(
        label="Número de teléfono del destinatario",
        max_length=20,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ejemplo: 595981123456"
        })
    )
    monto = forms.DecimalField(
        label="Monto a transferir",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        max_value=Decimal('500000.00'),
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.01"
        })
    )

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        return monto

    def clean_destinatario_telefono(self):
        telefono = self.cleaned_data["destinatario_telefono"]
        # Validación básica del formato de teléfono
        if not telefono.isdigit() or len(telefono) < 8:
            raise forms.ValidationError("Ingrese un número de teléfono válido.")
        return telefono

# --------- FORMULARIO DE TRANSFERENCIA DESDE BILLETERA A CUENTA BANCARIA (MEJORADO) ---------
class BilleteraABancoForm(forms.Form):
    entidad_destino = forms.ModelChoiceField(
        queryset=EntidadBancaria.objects.all(),
        label="Entidad bancaria destino",
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label="-- Selecciona un banco --"
    )
    numero_cuenta_destino = forms.CharField(
        label="Número de cuenta destino",
        max_length=20,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ejemplo: CUENTA001"
        })
    )
    monto = forms.DecimalField(
        label="Monto a transferir",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        max_value=Decimal('500000.00'),
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.01"
        })
    )

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        return monto

    def clean_numero_cuenta_destino(self):
        numero_cuenta = self.cleaned_data["numero_cuenta_destino"]
        if not numero_cuenta.strip():
            raise forms.ValidationError("El número de cuenta es requerido.")
        return numero_cuenta.strip().upper()