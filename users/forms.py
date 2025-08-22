# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from .models import Cliente

# Get the custom user model
CustomUser = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('is_cambista', 'is_active', 'email')

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['cedula', 'nombre_completo', 'direccion', 'telefono', 'segmento']