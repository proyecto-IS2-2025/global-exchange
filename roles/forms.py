from django import forms
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

User = settings.AUTH_USER_MODEL

class GroupForm(forms.ModelForm):
    # Ya no se gestionan los permisos desde el formulario
    class Meta:
        model = Group
        fields = ['name']

class PermissionForm(forms.Form):
    content_type = forms.ModelChoiceField(
        queryset= ContentType.objects.all(),
        label="Tipo de Contenido",
        help_text="Selecciona el modelo al que se aplicará el permiso."
    )
    name = forms.CharField(
        max_length=255,
        label="Nombre del Permiso",
        help_text="Un nombre legible para el permiso (e.g., 'Can view posts')."
    )
    codename = forms.CharField(
        max_length=100,
        label="Codename",
        help_text="Un nombre técnico y único para el permiso (e.g., 'view_post')."
    )