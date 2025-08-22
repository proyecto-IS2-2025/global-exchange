# users/tests/test_clients.py

from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from users.models import Cliente, Segmento
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

CustomUser = get_user_model()


# Pruebas para el modelo Cliente.
class ClienteModelTest(TestCase):
    """
    Pruebas para el modelo Cliente.
    """

    def setUp(self):
        """
        Configura datos de prueba antes de cada test.
        """
        self.segmento_minorista = Segmento.objects.create(name="minorista")
        self.cliente_existente = Cliente.objects.create(
            cedula="123456789",
            nombre_completo="Juan Pérez",
            segmento="VIP"
        )
        # Asegura que el segmento exista si lo estás usando
        self.segmento_vip = Segmento.objects.get(name="VIP")

    def test_creacion_exitosa_de_cliente(self):
        """
        Verifica que un cliente se pueda crear con todos los campos válidos.
        """
        cliente_nuevo = Cliente.objects.create(
            cedula="987654321",
            nombre_completo="Ana García",
            direccion="Avenida Falsa 789",
            telefono="0981777888",
            segmento=self.segmento_minorista
        )
        self.assertIsInstance(cliente_nuevo, Cliente)
        self.assertEqual(cliente_nuevo.nombre_completo, "Ana García")

    def test_segmento_predeterminado(self):
        """
        Verifica que el campo 'segmento' tenga el valor 'General' por defecto.
        """
        cliente_sin_segmento = Cliente.objects.create(
            cedula="111222333",
            nombre_completo="Carlos Sánchez"
        )
        self.assertEqual(cliente_sin_segmento.segmento, self.segmento_minorista)

    def test_cedula_debe_ser_unica(self):
        """
        Asegura que no se puedan crear dos clientes con la misma cédula.
        """
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(
                cedula="123456789",  # Cédula ya utilizada por self.cliente_existente
                nombre_completo="Pedro Sanz",
                segmento=self.segmento_minorista
            )

    def test_nombre_completo_no_puede_ser_vacio(self):
        """
        Confirma que se lance un ValidationError si el nombre_completo es nulo.
        """
        cliente_invalido = Cliente(cedula="111111111", nombre_completo="", segmento=self.segmento_minorista)
        with self.assertRaises(ValidationError):
            cliente_invalido.full_clean()

    def test_representacion_string(self):
        """
        Verifica que el método __str__ retorne el nombre completo del cliente.
        """
        self.assertEqual(str(self.cliente_existente), "Juan Pérez")


# Pruebas unitarias de vistas de cliente
class ClienteViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        self.client.login(username='admin', password='password')
        self.segmento_minorista = Segmento.objects.create(name="minorista")
        self.cliente = Cliente.objects.create(
            cedula='123456',
            nombre_completo='Cliente Prueba',
            direccion='Calle Falsa 123',
            telefono='123456789',
            segmento=self.segmento_minorista
        )
        self.admin_user.user_permissions.add(
            Permission.objects.get(codename='add_cliente'),
            Permission.objects.get(codename='change_cliente'),
            Permission.objects.get(codename='delete_cliente')
        )

    def test_cliente_list_view(self):
        response = self.client.get(reverse('cliente_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/cliente_list.html')
        self.assertContains(response, 'Cliente Prueba')

    def test_cliente_create_view(self):
        response = self.client.get(reverse('cliente_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/cliente_form.html')

    def test_cliente_update_view(self):
        response = self.client.get(reverse('cliente_update', args=[self.cliente.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/cliente_form.html')
        self.assertContains(response, 'Cliente Prueba')

    def test_cliente_delete_view(self):
        response = self.client.get(reverse('cliente_delete', args=[self.cliente.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/cliente_confirm_delete.html')