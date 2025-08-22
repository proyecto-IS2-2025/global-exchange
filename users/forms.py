from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

# Obtén el modelo de usuario personalizado
CustomUser = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Aquí defines los campos que aparecerán en el formulario de creación.
        # Incluye los campos predeterminados de UserCreationForm
        # y tus campos personalizados.
        fields = UserCreationForm.Meta.fields + ('telefono','email','name')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        # Aquí defines los campos que se pueden editar.
        # Excluye la contraseña para evitar errores
        fields = ('telefono', 'is_cambista', 'is_active', 'email', 'name',)
