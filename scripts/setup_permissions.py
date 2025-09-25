from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

CustomUser = get_user_model()

# 1. Crea el grupo de "Administradores de Usuarios"
group_admin_users, created = Group.objects.get_or_create(name='Administradores de Usuarios')

# 2. Obtén los permisos
permiso_add_user = Permission.objects.get(codename='add_customuser')
permiso_change_user = Permission.objects.get(codename='change_customuser')
permiso_delete_user = Permission.objects.get(codename='delete_customuser')

# 3. Asigna los permisos al grupo
group_admin_users.permissions.add(permiso_add_user, permiso_change_user, permiso_delete_user)

# 4. Asigna un usuario existente a este grupo
try:
    admin_user = CustomUser.objects.get(username='admin')
    admin_user.groups.add(group_admin_users)
    print("Permisos asignados al usuario 'admin' a través del grupo 'Administradores de Usuarios'")
except CustomUser.DoesNotExist:
    print("El usuario 'admin' no existe.")