#email no sea editable por ciertos roles
"""
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('is_cambista', 'is_active', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.is_staff:
            self.fields['email'].disabled = True
"""


#Que el formulario se adapte dinámicamente según el grupo del usuario (por ejemplo, mostrar más campos si es admin)
"""
def __init__(self, *args, **kwargs):
    user = kwargs.get('instance')
    super().__init__(*args, **kwargs)

    if not user.is_staff:
        self.fields['is_active'].disabled = True
"""