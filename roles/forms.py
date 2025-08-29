from django import forms
from django.contrib.auth.models import Group, Permission
from django.conf import settings

User = settings.AUTH_USER_MODEL

class GroupForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos"
    )
    users = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Usuarios"
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.apps import apps
        UserModel = apps.get_model(*User.split('.'))
        self.fields['users'].queryset = UserModel.objects.all()
        if self.instance.pk:
            self.fields['users'].initial = self.instance.user_set.all()