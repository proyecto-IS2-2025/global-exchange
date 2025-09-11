# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

# Get the custom user model
CustomUser = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
        }
        help_texts = {
            'username': 'Este será tu identificador visible en la plataforma.',
            'email': 'Usado para iniciar sesión y recibir notificaciones.',
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. nico.arza'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. nico@correo.com'
            }),
        }


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'is_active', 'is_cambista')
        labels = {
            'email': 'Correo electrónico',
            'is_active': '¿Está activo?',
            'is_cambista': '¿Es cambista?',
        }
        help_texts = {
            'email': 'Dirección de correo asociada a tu cuenta.',
            'is_active': 'Indica si el usuario puede acceder al sistema.',
            'is_cambista': 'Permite operar como cambista en la plataforma.',
        }
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. usuario@dominio.com'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_cambista': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ocultar el campo de contraseña si aparece
        if 'password' in self.fields:
            self.fields['password'].widget = forms.HiddenInput()

