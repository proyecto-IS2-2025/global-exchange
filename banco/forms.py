# forms.py
from django import forms
from .models import EntidadBancaria, Cuenta

class TransferenciaForm(forms.Form):
    """
    Formulario utilizado para ingresar los datos de una transferencia bancaria.

    Realiza validaciones en :meth:`~banco.forms.TransferenciaForm.clean` para asegurar 
    la existencia de la cuenta destino y prevenir transferencias a la cuenta propia.

    :ivar entidad_destino: Campo de selección de la entidad bancaria de destino.
    :vartype entidad_destino: :class:`django.forms.ModelChoiceField`
    :ivar numero_cuenta_destino: Campo de texto para el número de cuenta de destino.
    :vartype numero_cuenta_destino: :class:`django.forms.CharField`
    :ivar monto: Campo numérico para el monto a transferir.
    :vartype monto: :class:`django.forms.DecimalField`
    """
    entidad_destino = forms.ModelChoiceField(
        queryset=EntidadBancaria.objects.all(),
        label="Banco destino",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    numero_cuenta_destino = forms.CharField(
        max_length=20,
        label="Número de cuenta destino",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label="Monto a transferir",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario, extrayendo el usuario logueado (:attr:`user`) para validaciones.

        :param user: El objeto BancoUser que está realizando la transferencia.
        :type user: :class:`~banco.models.BancoUser`
        """
        self.user = kwargs.pop("user", None)  # 👈 guardamos el usuario en el form
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Validación a nivel de formulario para la cuenta destino.

        Asegura que la cuenta destino exista y que no sea la cuenta propia del usuario logueado.

        :raises forms.ValidationError: Si la cuenta destino no existe o si el usuario intenta transferir a sí mismo.
        :returns: Los datos limpios del formulario.
        :rtype: dict
        """
        cleaned_data = super().clean()
        entidad_destino = cleaned_data.get("entidad_destino")
        numero_cuenta_destino = cleaned_data.get("numero_cuenta_destino")

        if self.user and entidad_destino and numero_cuenta_destino:
            try:
                cuenta_destino = Cuenta.objects.get(
                    entidad=entidad_destino,
                    numero_cuenta=numero_cuenta_destino
                )
                # 🚨 Validación: no se puede transferir a tu propia cuenta
                if cuenta_destino.usuario == self.user:
                    raise forms.ValidationError("No podés transferir a tu propia cuenta.")
            except Cuenta.DoesNotExist:
                raise forms.ValidationError("La cuenta destino no existe.")

        return cleaned_data
