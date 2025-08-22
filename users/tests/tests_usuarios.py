# users/tests/test_users.py
from django.contrib.auth.models import Permission
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import Role

CustomUser = get_user_model()

# Pruebas unitarias de modelos de usuario y roles
class CustomUserModelTest(TestCase):

    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'is_active': True,
            'is_cambista': True
        }

    def test_create_custom_user(self):
        user = CustomUser.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_cambista)
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin_user = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_active)

class RoleModelTest(TestCase):

    def test_create_role(self):
        role = Role.objects.create(name='Administrador', description='Administrador de sistema')
        self.assertEqual(role.name, 'Administrador')
        self.assertEqual(role.description, 'Administrador de sistema')
        self.assertEqual(str(role), 'Administrador')


# Pruebas unitarias de vistas de usuario
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
        self.admin_user.user_permissions.add(
            Permission.objects.get(codename='add_customuser'),
            Permission.objects.get(codename='change_customuser'),
            Permission.objects.get(codename='delete_customuser')
        )

    def test_user_list_view(self):
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/user_list.html')
        self.assertContains(response, 'user1')

    def test_user_create_view(self):
        response = self.client.get(reverse('user_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/user_form.html')

    def test_user_update_view(self):
        response = self.client.get(reverse('user_update', args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/user_form.html')
        self.assertContains(response, 'user1')

    def test_user_delete_view(self):
        response = self.client.get(reverse('user_delete', args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/user_confirm_delete.html')