from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

try:
    # ⚙️ Datos del superusuario
    username = input("Ingrese el nombre de usuario para el superusuario: ") or 'superadmin'
    email = input("Ingrese el correo electrónico para el superusuario: ") or 'superadmin@tudominio.com'
    password = input("Ingrese la contraseña para el superusuario: ") or 'password_seguro'

    # Crea el superusuario
    if not User.objects.filter(username=username).exists():
        superuser = User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superusuario '{username}' creado exitosamente.")
        
        # Agrega el superusuario al grupo 'admin'
        admin_group, created = Group.objects.get_or_create(name='admin')
        superuser.groups.add(admin_group)
        print(f"Superusuario '{username}' agregado al grupo 'admin'.")
    else:
        print(f"El superusuario '{username}' ya existe.")

except Exception as e:
    print(f"Ocurrió un error: {e}")