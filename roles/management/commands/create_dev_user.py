from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea usuario de desarrollo con permisos de superusuario'

    def handle(self, *args, **options):
        username = 'dev'
        email = 'dev@test.com'
        password = 'dev123'
        
        # Verificar si existe
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.WARNING(f'⚠️  Usuario {username} ya existe')
            )
        else:
            # Crear superusuario
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name='Developer',
                last_name='Test'
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Usuario {username} creado')
            )
        
        # Mostrar credenciales
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🔑 CREDENCIALES DE DESARROLLO'))
        self.stdout.write('='*60)
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Email: {email}')
        self.stdout.write('Tipo: Superusuario (todos los permisos)')
        self.stdout.write('='*60 + '\n')