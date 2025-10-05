from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission, ContentType
from roles.views import (
    is_admin,
    permission_create,
    group_detail_users,
    search_users,
)
from roles.forms import PermissionForm

CustomUser = get_user_model()

class AdminAccessTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.normal_user = CustomUser.objects.create_user(
            email='user@test.com',
            username='user',
            password='testpassword'
        )
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='testpassword'
        )

    def test_is_admin_function(self):
        """Prueba la función auxiliar is_admin."""
        self.assertTrue(is_admin(self.admin_user))
        self.assertFalse(is_admin(self.normal_user))
        
    def test_permission_create_view_admin_access(self):
        """Prueba que solo el admin puede acceder a la vista de creación de permisos."""
        # Usuario normal no tiene acceso
        request = self.factory.get(reverse('permission_create'))
        request.user = self.normal_user
        response = permission_create(request)
        self.assertEqual(response.status_code, 403) # Acceso denegado

        # Admin sí tiene acceso
        request = self.factory.get(reverse('permission_create'))
        request.user = self.admin_user
        response = permission_create(request)
        self.assertEqual(response.status_code, 200) # Acceso permitido

    def test_group_detail_users_view_admin_access(self):
        """Prueba que solo el admin puede acceder a la vista de detalle de usuarios del grupo."""
        group = Group.objects.create(name='Test Group')
        
        # Usuario normal no tiene acceso
        request = self.factory.get(reverse('group_detail_users', kwargs={'pk': group.pk}))
        request.user = self.normal_user
        response = group_detail_users(request, group.pk)
        self.assertEqual(response.status_code, 403) # Acceso denegado

        # Admin sí tiene acceso
        request = self.factory.get(reverse('group_detail_users', kwargs={'pk': group.pk}))
        request.user = self.admin_user
        response = group_detail_users(request, group.pk)
        self.assertEqual(response.status_code, 200) # Acceso permitido
        
class PermissionCreateTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='testpassword'
        )
        self.content_type = ContentType.objects.create(app_label='users', model='customuser')

    def test_permission_create_get(self):
        """Prueba que la vista GET renderiza el formulario correctamente."""
        request = self.factory.get(reverse('permission_create'))
        request.user = self.admin_user
        response = permission_create(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Crear Nuevo Permiso', response.content)
        
    def test_permission_create_post_success(self):
        """Prueba que un permiso se crea exitosamente con un POST válido."""
        data = {
            'content_type': self.content_type.id,
            'name': 'Can view my cool model',
            'codename': 'view_cool_model',
        }
        
        request = self.factory.post(reverse('permission_create'), data)
        request.user = self.admin_user
        
        self.assertEqual(Permission.objects.count(), 0) # No hay permisos creados inicialmente

        response = permission_create(request)
        
        self.assertEqual(response.status_code, 302) # Redirige después de la creación
        self.assertEqual(Permission.objects.count(), 1) # Un permiso fue creado
        
        new_permission = Permission.objects.get(codename='view_cool_model')
        self.assertEqual(new_permission.name, 'Can view my cool model')

class GroupUserManagementTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='testpassword'
        )
        self.group = Group.objects.create(name='Test Group')
        self.user1 = CustomUser.objects.create_user(email='user1@test.com', username='user1', password='test')
        self.user2 = CustomUser.objects.create_user(email='user2@test.com', username='user2', password='test')
        
    def test_group_detail_users_get_context(self):
        """Prueba que la vista GET carga el contexto correcto."""
        self.group.user_set.add(self.user1)
        
        request = self.factory.get(reverse('group_detail_users', kwargs={'pk': self.group.pk}))
        request.user = self.admin_user
        response = group_detail_users(request, self.group.pk)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.group, response.content['group'].user_set.all())

    def test_group_detail_users_post_add_users(self):
        """Prueba que la vista POST puede agregar usuarios a un grupo."""
        data = {'users': [self.user1.id, self.user2.id]}
        
        request = self.factory.post(reverse('group_detail_users', kwargs={'pk': self.group.pk}), data)
        request.user = self.admin_user
        response = group_detail_users(request, self.group.pk)
        
        self.assertEqual(response.status_code, 302) # Redirige
        self.assertCountEqual(self.group.user_set.all(), [self.user1, self.user2]) # Comprueba que los usuarios se han añadido

    def test_group_detail_users_post_remove_users(self):
        """Prueba que la vista POST puede remover usuarios de un grupo."""
        self.group.user_set.add(self.user1, self.user2)
        
        data = {'users': [self.user1.id]}
        
        request = self.factory.post(reverse('group_detail_users', kwargs={'pk': self.group.pk}), data)
        request.user = self.admin_user
        response = group_detail_users(request, self.group.pk)
        
        self.assertEqual(response.status_code, 302)
        self.assertCountEqual(self.group.user_set.all(), [self.user1])

class SearchUsersTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='testpassword'
        )
        self.user1 = CustomUser.objects.create_user(email='testuser1@test.com', username='testuser1', password='test')
        self.user2 = CustomUser.objects.create_user(email='anotheruser@test.com', username='anotheruser', password='test')

    def test_search_users_with_query(self):
        """Prueba que la API de búsqueda de usuarios devuelve los resultados correctos."""
        request = self.factory.get(reverse('search_users'), {'q': 'testuser'})
        request.user = self.admin_user
        response = search_users(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'testuser1@test.com', response.content)
        self.assertNotIn(b'anotheruser@test.com', response.content)
    
    def test_search_users_without_query(self):
        """Prueba que la API devuelve una lista vacía sin una consulta."""
        request = self.factory.get(reverse('search_users'))
        request.user = self.admin_user
        response = search_users(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'[]')
