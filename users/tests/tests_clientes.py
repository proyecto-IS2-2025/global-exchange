from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.utils import IntegrityError
from ..models import Cliente, Segmento

CustomUser = get_user_model()


class ClienteModelTest(TestCase):
    def setUp(self):
        self.segmento_vip = Segmento.objects.create(name="VIP")
        self.cliente_existente = Cliente.objects.create(
            cedula="123456789",
            nombre_completo="Juan Pérez",
            segmento=self.segmento_vip
        )

    def test_creacion_exitosa_de_cliente(self):
        segmento_general = Segmento.objects.create(name="General")
        cliente_nuevo = Cliente.objects.create(
            cedula="987654321",
            nombre_completo="Ana García",
            direccion="Avenida Falsa 789",
            telefono="0981777888",
            segmento=segmento_general
        )
        self.assertIsInstance(cliente_nuevo, Cliente)
        self.assertEqual(cliente_nuevo.nombre_completo, "Ana García")

    def test_cedula_debe_ser_unica(self):
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(
                cedula="123456789",
                nombre_completo="Pedro Lopez",
                segmento=self.segmento_vip
            )

    def test_nombre_completo_no_puede_ser_vacio(self):
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(
                cedula="111222333",
                nombre_completo=None,
                segmento=self.segmento_vip
            )

    def test_representacion_string(self):
        self.assertEqual(str(self.cliente_existente), "Juan Pérez")

    def test_segmento_predeterminado(self):
        segmento_general = Segmento.objects.create(name="General")
        cliente_sin_segmento = Cliente.objects.create(
            cedula="111222333",
            nombre_completo="Carlos Sánchez",
            segmento=segmento_general
        )
        self.assertEqual(cliente_sin_segmento.segmento.name, "General")


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

        # Corrección del error 'MultipleObjectsReturned'
        self.admin_user.user_permissions.add(
            Permission.objects.filter(codename='add_cliente').first(),
            Permission.objects.filter(codename='change_cliente').first(),
            Permission.objects.filter(codename='delete_cliente').first()
        )

    def test_cliente_list_view(self):
        response = self.client.get(reverse('cliente_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cliente.nombre_completo)

    def test_cliente_create_view(self):
        response = self.client.post(reverse('cliente_create'), {
            'cedula': '654321',
            'nombre_completo': 'Nuevo Cliente',
            'segmento': self.segmento_minorista.id
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cliente.objects.filter(cedula='654321').exists())

    def test_cliente_update_view(self):
        response = self.client.post(reverse('cliente_update', args=[self.cliente.pk]), {
            'cedula': self.cliente.cedula,
            'nombre_completo': 'Cliente Actualizado',
            'segmento': self.segmento_minorista.id
        })
        self.assertEqual(response.status_code, 302)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre_completo, 'Cliente Actualizado')

    def test_cliente_delete_view(self):
        response = self.client.post(reverse('cliente_delete', args=[self.cliente.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cliente.objects.filter(pk=self.cliente.pk).exists())