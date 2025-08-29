from django import forms
from django.contrib.auth.models import Group, Permission
from django.conf import settings

User = settings.AUTH_USER_MODEL

from django import forms
from django.contrib.auth.models import Group, Permission
from django.conf import settings

User = settings.AUTH_USER_MODEL

class GroupForm(forms.ModelForm):
    # Ya no se gestionan los permisos desde el formulario
    class Meta:
        model = Group
        fields = ['name']