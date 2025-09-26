# billetera/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import UsuarioBilletera, Billetera, RecargaBilletera, TransferenciaBilletera
from banco.models import EntidadBancaria, TarjetaDebito
from decimal import Decimal


class RegistroUsuarioForm(forms.ModelForm):
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmar contraseña"
    )
    
    class Meta:
        model = UsuarioBilletera
        fields = ['numero_celular', 'nombre', 'apellido', 'password']
        widgets = {
            'numero_celular': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+595981234567'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Las contraseñas no coinciden.")
        
        return cleaned_data


class CrearBilleteraForm(forms.ModelForm):
    class Meta:
        model = Billetera
        fields = ['entidad']
        widgets = {
            'entidad': forms.Select(attrs={'class': 'form-control'})
        }


class LoginForm(forms.Form):
    numero_celular = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+595981234567'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class RecargaBilleteraForm(forms.Form):
    numero_tarjeta = forms.CharField(
        max_length=16,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '1234567890123456',
            'maxlength': '16'
        }),
        label="Número de tarjeta"
    )
    mes_vencimiento = forms.IntegerField(
        min_value=1, 
        max_value=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '12'}),
        label="Mes de vencimiento"
    )
    anho_vencimiento = forms.IntegerField(
        min_value=2024,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2025'}),
        label="Año de vencimiento"
    )
    cvv = forms.CharField(
        max_length=3,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '123',
            'maxlength': '3'
        }),
        label="CVV"
    )
    monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('1000.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50000.00'}),
        label="Monto a recargar"
    )

    def clean(self):
        cleaned_data = super().clean()
        numero_tarjeta = cleaned_data.get('numero_tarjeta')
        mes_vencimiento = cleaned_data.get('mes_vencimiento')
        anho_vencimiento = cleaned_data.get('anho_vencimiento')
        cvv = cleaned_data.get('cvv')
        monto = cleaned_data.get('monto')

        if numero_tarjeta and mes_vencimiento and anho_vencimiento and cvv:
            try:
                tarjeta = TarjetaDebito.objects.get(
                    numero=numero_tarjeta,
                    mes_vencimiento=mes_vencimiento,
                    anho_vencimiento=anho_vencimiento,
                    cvv=cvv
                )
                
                if not tarjeta.cuenta:
                    raise ValidationError("La tarjeta no tiene cuenta asociada.")
                
                if monto and tarjeta.cuenta.saldo < monto:
                    raise ValidationError(f"Saldo insuficiente. Saldo disponible: ₲{tarjeta.cuenta.saldo}")
                
                cleaned_data['tarjeta_debito'] = tarjeta
                
            except TarjetaDebito.DoesNotExist:
                raise ValidationError("Los datos de la tarjeta no son válidos.")
        
        return cleaned_data


class TransferirFondosForm(forms.Form):
    entidad_destino = forms.ModelChoiceField(
        queryset=EntidadBancaria.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Entidad de destino"
    )
    numero_celular_destino = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+595981234567'}),
        label="Número de celular de destino"
    )
    monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('1000.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50000.00'}),
        label="Monto a enviar"
    )

    def __init__(self, billetera_origen=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.billetera_origen = billetera_origen

    def clean(self):
        cleaned_data = super().clean()
        entidad_destino = cleaned_data.get('entidad_destino')
        numero_celular_destino = cleaned_data.get('numero_celular_destino')
        monto = cleaned_data.get('monto')

        if numero_celular_destino and entidad_destino:
            try:
                usuario_destino = UsuarioBilletera.objects.get(numero_celular=numero_celular_destino)
                billetera_destino = Billetera.objects.get(
                    usuario=usuario_destino,
                    entidad=entidad_destino,
                    activa=True
                )
                cleaned_data['billetera_destino'] = billetera_destino
                
                if self.billetera_origen and billetera_destino == self.billetera_origen:
                    raise ValidationError("No puedes enviarte dinero a ti mismo.")
                
            except UsuarioBilletera.DoesNotExist:
                raise ValidationError("No existe un usuario con ese número de celular.")
            except Billetera.DoesNotExist:
                raise ValidationError("El usuario no tiene billetera en la entidad seleccionada.")

        if self.billetera_origen and monto and self.billetera_origen.saldo < monto:
            raise ValidationError(f"Saldo insuficiente. Saldo disponible: ₲{self.billetera_origen.saldo}")
        
        return cleaned_data