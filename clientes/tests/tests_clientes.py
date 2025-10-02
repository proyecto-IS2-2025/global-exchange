"""
Pruebas unitarias para modelos y vistas de clientes.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model  # ✅ AGREGAR
from django.db.utils import IntegrityError 
from django.db import transaction 

# ✅ Imports modularizados (ya están correctos)
from clientes.models import Cliente, Segmento, AsignacionCliente

CustomUser = get_user_model()


class ClienteModelTest(TestCase):
    """Tests básicos para el modelo Cliente sin usar vistas web."""

    def setUp(self):
        self.segmento_minorista = Segmento.objects.create(name="Minorista")
        self.segmento_mayorista = Segmento.objects.create(name="Mayorista")

    def test_crear_cliente_basico(self):
        """Verifica la creación básica de un cliente."""
        cliente = Cliente.objects.create(
            cedula="123456",
            nombre_completo="Cliente Test",
            segmento=self.segmento_minorista,
        )
        
        self.assertEqual(cliente.cedula, "123456")
        self.assertEqual(cliente.nombre_completo, "Cliente Test")
        self.assertEqual(cliente.segmento, self.segmento_minorista)
        
        # Verificar que se guardó en la base de datos
        self.assertTrue(Cliente.objects.filter(cedula="123456").exists())

    def test_cliente_str_method(self):
        """Verifica el método __str__ del modelo Cliente."""
        cliente = Cliente.objects.create(
            cedula="789012",
            nombre_completo="Juan Pérez",
            segmento=self.segmento_mayorista,
        )
        
        # El método __str__ debería retornar información útil del cliente
        str_representation = str(cliente)
        self.assertIsInstance(str_representation, str)
        self.assertTrue(len(str_representation) > 0)

    def test_segmento_relationship(self):
        """Verifica la relación entre Cliente y Segmento."""
        cliente1 = Cliente.objects.create(
            cedula="111111",
            nombre_completo="Cliente Minorista",
            segmento=self.segmento_minorista,
        )
        
        cliente2 = Cliente.objects.create(
            cedula="222222",
            nombre_completo="Cliente Mayorista",
            segmento=self.segmento_mayorista,
        )
        
        # Verificar que los segmentos se asignaron correctamente
        self.assertEqual(cliente1.segmento, self.segmento_minorista)
        self.assertEqual(cliente2.segmento, self.segmento_mayorista)
        
        # Verificar que podemos filtrar clientes por segmento
        clientes_minoristas = Cliente.objects.filter(segmento=self.segmento_minorista)
        clientes_mayoristas = Cliente.objects.filter(segmento=self.segmento_mayorista)
        
        self.assertEqual(clientes_minoristas.count(), 1)
        self.assertEqual(clientes_mayoristas.count(), 1)
        self.assertEqual(clientes_minoristas.first(), cliente1)
        self.assertEqual(clientes_mayoristas.first(), cliente2)

    def test_crear_multiples_clientes(self):
        """Verifica que se pueden crear múltiples clientes."""
        Cliente.objects.create(
            cedula="001",
            nombre_completo="Cliente Uno",
            segmento=self.segmento_minorista,
        )
        
        Cliente.objects.create(
            cedula="002",
            nombre_completo="Cliente Dos",
            segmento=self.segmento_mayorista,
        )
        
        Cliente.objects.create(
            cedula="003",
            nombre_completo="Cliente Tres",
            segmento=self.segmento_minorista,
        )
        
        # Verificar que todos los clientes se crearon
        self.assertEqual(Cliente.objects.count(), 3)
        
        # Verificar distribución por segmentos
        self.assertEqual(Cliente.objects.filter(segmento=self.segmento_minorista).count(), 2)
        self.assertEqual(Cliente.objects.filter(segmento=self.segmento_mayorista).count(), 1)

    def test_cedula_unique_constraint(self):
        """Verifica la restricción de unicidad en el campo cedula."""
        # 1. Crear el primer cliente (debe funcionar)
        Cliente.objects.create(
            cedula="UNIQUE001",
            nombre_completo="Primer Cliente",
            segmento=self.segmento_minorista,
        )
        self.assertEqual(Cliente.objects.filter(cedula="UNIQUE001").count(), 1)

        # 2. Intentar crear otro cliente con la misma cédula (DEBE fallar)
        with self.assertRaises(IntegrityError):
            with transaction.atomic(): # <-- Esto aísla la excepción de unicidad
                Cliente.objects.create(
                    cedula="UNIQUE001",
                    nombre_completo="Segundo Cliente",
                    segmento=self.segmento_mayorista,
                )
            
        # 3. Verificar que solo existe el primer cliente después de que el error fue capturado.
        self.assertEqual(Cliente.objects.filter(cedula="UNIQUE001").count(), 1)


class SegmentoModelTest(TestCase):
    """Tests básicos para el modelo Segmento."""

    def test_crear_segmento(self):
        """Verifica la creación básica de un segmento."""
        segmento = Segmento.objects.create(name="Corporativo")
        
        self.assertEqual(segmento.name, "Corporativo")
        self.assertTrue(Segmento.objects.filter(name="Corporativo").exists())

    def test_segmento_str_method(self):
        """Verifica el método __str__ del modelo Segmento."""
        segmento = Segmento.objects.create(name="Premium")
        
        str_representation = str(segmento)
        self.assertIsInstance(str_representation, str)
        self.assertTrue(len(str_representation) > 0)