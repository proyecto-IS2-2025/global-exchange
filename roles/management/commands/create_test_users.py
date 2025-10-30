# roles/management/commands/create_test_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea usuarios de prueba con diferentes roles'

    def handle(self, *args, **options):
        # Password común para testing
        test_password = 'test1234'
        
        users_data = [
            {
                'username': 'test_admin',
                'email': 'test_admin@test.com',
                'first_name': 'Test',
                'last_name': 'Admin',
                'is_staff': True,
                'group': 'admin'
            },
            {
                'username': 'test_operador',
                'email': 'test_operador@test.com',
                'first_name': 'Test',
                'last_name': 'Operador',
                'is_staff': True,
                'group': 'operador'
            },
            {
                'username': 'test_cliente',
                'email': 'test_cliente@test.com',
                'first_name': 'Test',
                'last_name': 'Cliente',
                'is_staff': False,
                'group': 'cliente'
            },
        ]
        
        for user_data in users_data:
            group_name = user_data.pop('group')
            
            # Crear usuario si no existe
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            
            if created:
                user.set_password(test_password)
                user.is_active = True  # Activar sin verificación de email
                user.save()
                
                # Asignar grupo
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Usuario creado: {user.username} '
                            f'(Grupo: {group_name}, Password: {test_password})'
                        )
                    )
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Grupo "{group_name}" no existe. '
                            f'Ejecute: python manage.py setup_test_roles'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Usuario {user.username} ya existe'
                    )
                )