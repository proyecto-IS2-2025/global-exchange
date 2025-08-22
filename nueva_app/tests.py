# users/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Cliente, AsignacionCliente


class AdminAsociacionTestCase(TestCase):
    def setUp(self):
        # Crear un usuario administrador
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpassword',
            email='admin@example.com'
        )
        # Crear un usuario normal
        self.normal_user = User.objects.create_user(
            username='user1',
            password='password123'
        )
        # Crear clientes de prueba
        self.cliente1 = Cliente.objects.create(nombre_completo='Cliente Uno', cedula='1111')
        self.cliente2 = Cliente.objects.create(nombre_completo='Cliente Dos', cedula='2222')

    def test_admin_asociar_clientes(self):
        # Iniciar sesión como administrador
        self.client.login(username='admin', password='adminpassword')

        # Simular una solicitud POST a la vista de asociación
        response = self.client.post(
            '/nueva_ruta/admin/asociar/',
            {
                'usuario': self.normal_user.id,
                'clientes': [self.cliente1.id, self.cliente2.id],
            }
        )

        # Verificar que la asociación se realizó correctamente
        self.assertEqual(response.status_code, 302)  # 302 es el código de redirección
        self.assertTrue(AsignacionCliente.objects.filter(usuario=self.normal_user, cliente=self.cliente1).exists())
        self.assertTrue(AsignacionCliente.objects.filter(usuario=self.normal_user, cliente=self.cliente2).exists())
        self.assertEqual(self.normal_user.cliente_set.count(), 2)