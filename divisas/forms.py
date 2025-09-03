from django import forms
from .models import Divisa

class DivisaForm(forms.ModelForm):
    class Meta:
        model = Divisa
        fields = ['nombre', 'code', 'simbolo']  # is_active NO se expone al crear

    def clean_code(self):
        return (self.cleaned_data.get('code') or '').upper().strip()
