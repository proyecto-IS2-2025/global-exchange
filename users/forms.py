# users/forms.py

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

# Obtén el modelo de usuario personalizado
CustomUser = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Elimina 'telefono' y 'name' a menos que existan en tu modelo
        fields = ('username', 'email')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        # Elimina 'telefono' y 'name' si no existen en tu modelo
        fields = ('is_cambista', 'is_active', 'email')