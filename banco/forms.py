from django import forms
from .models import Transferencia

class TransferenciaForm(forms.ModelForm):
    class Meta:
        model = Transferencia
        fields = ["cuenta_destino", "monto"]

    def __init__(self, *args, **kwargs):
        cuenta_emisor = kwargs.pop("cuenta_emisor", None)
        super().__init__(*args, **kwargs)
        if cuenta_emisor:
            self.fields["cuenta_destino"].queryset = self.fields["cuenta_destino"].queryset.exclude(id=cuenta_emisor.id)
