# users/tests.py

from django.contrib.auth.models import Permission
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import Role

CustomUser = get_user_model()

#Pruebas unitarias de usuarios
class CustomUserModelTest(TestCase):

    def setUp(self):
        # Esta función se ejecuta antes de cada prueba
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'is_active': True, # <-- Cambiado de 'is-active' a 'is_active'
            'is_cambista': True
        }

    def test_create_custom_user(self):
        # Prueba que se puede crear un usuario correctamente
        user = CustomUser.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_cambista)
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        # Prueba que se puede crear un superusuario
        admin_user = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_active)

#prueba unitaria de roles
class RoleModelTest(TestCase):

    def test_create_role(self):
        # Prueba que se puede crear un rol
        role = Role.objects.create(name='Administrador', description='Administrador de sistema')
        self.assertEqual(role.name, 'Administrador')
        self.assertEqual(role.description, 'Administrador de sistema')
        self.assertEqual(str(role), 'Administrador')


#Prueba unitaria de vistas
class UserViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        self.client.login(username='admin', password='password')
        self.user = CustomUser.objects.create_user(
            username='user1',
            password='password',
            email='user1@example.com'
        )
        # Asigna el permiso para el CRUD de usuarios
        self.admin_user.user_permissions.add(
            Permission.objects.get(codename='add_customuser'),
            Permission.objects.get(codename='change_customuser'),
            Permission.objects.get(codename='delete_customuser')
        )

    def test_user_list_view(self):
        # Prueba que la vista de lista de usuarios funciona
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/user_list.html')
        self.assertContains(response, 'user1')

    def test_user_create_view(self):
        # Prueba que la vista de creación de usuario funciona
        response = self.client.get(reverse('user_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/user_form.html')

    def test_user_update_view(self):
        # Prueba que la vista de edición de usuario funciona
        response = self.client.get(reverse('user_update', args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/user_form.html')
        self.assertContains(response, 'user1')

    def test_user_delete_view(self):
        # Prueba que la vista de eliminación de usuario funciona
        response = self.client.get(reverse('user_delete', args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/user_confirm_delete.html')