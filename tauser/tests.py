# -*- coding: utf-8 -*-
"""
Suite de tests para el sistema TAUSER.
Ejecutar con: python manage.py test tauser
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .models import (
    Terminal,
    InventarioDenominacionTerminal,
    RegistroTransaccionTerminal,
)
from transacciones.models import Transaccion
from clientes.models import Cliente
from divisas.models import Divisa, Denominacion
from mfa.models import MFAConfig
from .services import calcular_desglose_optimo

User = get_user_model()


class TauserCodeTestCase(TestCase):
    """Tests para el código TAUSER único en transacciones."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        self.cliente = Cliente.objects.create(
            cedula="1234567",
            nombre_completo="Cliente Test",
            email="test@test.com",
            esta_activo=True
        )
        self.divisa_pyg = Divisa.objects.create(
            code="PYG",
            nombre="Guaraní Paraguayo",
            simbolo="₲",
            is_active=True
        )
        self.divisa_usd = Divisa.objects.create(
            code="USD",
            nombre="Dólar Estadounidense",
            simbolo="$",
            is_active=True
        )
    
    def test_tauser_code_se_genera_automaticamente(self):
        """Verifica que el código TAUSER se genera automáticamente al crear transacción."""
        transaccion = Transaccion.objects.create(
            cliente=self.cliente,
            tipo_operacion='compra',
            divisa_origen=self.divisa_pyg,
            divisa_destino=self.divisa_usd,
            monto_origen=Decimal('100'),
            monto_destino=Decimal('100'),
            tasa_de_cambio_aplicada=Decimal('1'),
            estado='pagada'  # Debe estar pagada para generar código TAUSER
        )
        
        self.assertIsNotNone(transaccion.tauser_code)
        self.assertEqual(len(transaccion.tauser_code), 8)
        self.assertTrue(transaccion.tauser_code.isalnum())
    
    def test_tauser_code_es_unico(self):
        """Verifica que cada transacción tiene un código TAUSER único."""
        transacciones = []
        for i in range(10):
            t = Transaccion.objects.create(
                cliente=self.cliente,
                tipo_operacion='venta',  # Venta siempre genera código
                divisa_origen=self.divisa_usd,
                divisa_destino=self.divisa_pyg,
                monto_origen=Decimal('100'),
                monto_destino=Decimal('100'),
                tasa_de_cambio_aplicada=Decimal('1'),
                estado='pendiente'
            )
            transacciones.append(t)
        
        codigos = [t.tauser_code for t in transacciones]
        # Verificar que no hay duplicados
        self.assertEqual(len(codigos), len(set(codigos)))
    
    def test_buscar_transaccion_por_tauser_code(self):
        """Verifica que se puede buscar una transacción por su código TAUSER."""
        transaccion = Transaccion.objects.create(
            cliente=self.cliente,
            tipo_operacion='venta',
            divisa_origen=self.divisa_usd,
            divisa_destino=self.divisa_pyg,
            monto_origen=Decimal('100'),
            monto_destino=Decimal('100'),
            tasa_de_cambio_aplicada=Decimal('1'),
            estado='pendiente'
        )
        
        # Buscar por código
        encontrada = Transaccion.objects.get(tauser_code=transaccion.tauser_code)
        self.assertEqual(encontrada.id, transaccion.id)


class AlgoritmoDenominacionesTestCase(TestCase):
    """Tests para el algoritmo de cálculo de denominaciones."""
    
    def setUp(self):
        """Crear datos de prueba."""
        self.divisa = Divisa.objects.create(
            code="USD",
            nombre="Dólar",
            simbolo="$",
            is_active=True
        )
        
        self.terminal = Terminal.objects.create(
            codigo="TEST001",
            nombre="Terminal Test",
            ubicacion="Test Location",
            is_activa=True
        )
        
        # Crear denominaciones
        self.denom_100 = Denominacion.objects.create(
            divisa=self.divisa,
            valor=Decimal('100'),
            is_active=True
        )
        self.denom_50 = Denominacion.objects.create(
            divisa=self.divisa,
            valor=Decimal('50'),
            is_active=True
        )
        self.denom_20 = Denominacion.objects.create(
            divisa=self.divisa,
            valor=Decimal('20'),
            is_active=True
        )
        self.denom_10 = Denominacion.objects.create(
            divisa=self.divisa,
            valor=Decimal('10'),
            is_active=True
        )
    
    def test_algoritmo_greedy_caso_simple(self):
        """Test del algoritmo greedy con caso simple."""
        # Crear inventario
        inv_100 = InventarioDenominacionTerminal.objects.create(
            terminal=self.terminal,
            denominacion=self.denom_100,
            cantidad=5
        )
        inv_50 = InventarioDenominacionTerminal.objects.create(
            terminal=self.terminal,
            denominacion=self.denom_50,
            cantidad=10
        )
        inv_20 = InventarioDenominacionTerminal.objects.create(
            terminal=self.terminal,
            denominacion=self.denom_20,
            cantidad=20
        )
        
        inventarios = [inv_100, inv_50, inv_20]
        resultado = calcular_desglose_optimo(inventarios, Decimal('270'))
        
        self.assertTrue(resultado['posible'])
        self.assertEqual(resultado['sobrante'], Decimal('0'))
        self.assertEqual(resultado['algoritmo_usado'], 'greedy')
    
    def test_algoritmo_backtracking_cuando_greedy_falla(self):
        """Test del backtracking cuando greedy no encuentra solución."""
        # Caso donde greedy falla: 1x30 disponible, 2x20 disponibles, queremos 40
        denom_30 = Denominacion.objects.create(
            divisa=self.divisa,
            valor=Decimal('30'),
            is_active=True
        )
        
        inv_30 = InventarioDenominacionTerminal.objects.create(
            terminal=self.terminal,
            denominacion=denom_30,
            cantidad=1
        )
        inv_20 = InventarioDenominacionTerminal.objects.create(
            terminal=self.terminal,
            denominacion=self.denom_20,
            cantidad=2
        )
        
        inventarios = [inv_30, inv_20]
        resultado = calcular_desglose_optimo(inventarios, Decimal('40'))
        
        self.assertTrue(resultado['posible'])
        self.assertEqual(resultado['sobrante'], Decimal('0'))
        self.assertEqual(resultado['algoritmo_usado'], 'backtracking')
    
    def test_algoritmo_caso_imposible(self):
        """Test cuando no es posible formar el monto exacto."""
        inv_50 = InventarioDenominacionTerminal.objects.create(
            terminal=self.terminal,
            denominacion=self.denom_50,
            cantidad=2
        )
        
        inventarios = [inv_50]
        resultado = calcular_desglose_optimo(inventarios, Decimal('35'))
        
        self.assertFalse(resultado['posible'])
        self.assertGreater(resultado['sobrante'], Decimal('0'))


class TerminalTestCase(TestCase):
    """Tests para el modelo Terminal."""
    
    def test_crear_terminal(self):
        """Verifica que se puede crear un terminal correctamente."""
        terminal = Terminal.objects.create(
            codigo="TERM001",
            nombre="Terminal Principal",
            ubicacion="Sucursal Centro",
            is_activa=True
        )
        
        self.assertEqual(terminal.codigo, "TERM001")
        self.assertTrue(terminal.is_activa)
    
    def test_terminal_puede_desactivarse(self):
        """Verifica que un terminal puede ser activado/desactivado."""
        terminal = Terminal.objects.create(
            codigo="TERM002",
            nombre="Terminal Test",
            ubicacion="Test",
            is_activa=True
        )
        
        terminal.is_activa = False
        terminal.save()
        
        terminal.refresh_from_db()
        self.assertFalse(terminal.is_activa)


class InventarioDenominacionTestCase(TestCase):
    """Tests para el inventario de denominaciones."""
    
    def setUp(self):
        """Configuración inicial."""
        self.divisa = Divisa.objects.create(
            code="USD",
            nombre="Dólar",
            simbolo="$",
            is_active=True
        )
        
        self.terminal = Terminal.objects.create(
            codigo="TEST001",
            nombre="Terminal Test",
            ubicacion="Test",
            is_activa=True
        )
        
        self.denom = Denominacion.objects.create(
            divisa=self.divisa,
            valor=Decimal('100'),
            is_active=True
        )
    
    def test_crear_inventario_denominacion(self):
        """Verifica que se puede crear inventario de denominaciones."""
        inventario = InventarioDenominacionTerminal.objects.create(
            terminal=self.terminal,
            denominacion=self.denom,
            cantidad=50,
            cantidad_minima=10
        )
        
        self.assertEqual(inventario.cantidad, 50)
        self.assertEqual(inventario.valor_total, Decimal('5000'))
    
    def test_valor_total_se_calcula_correctamente(self):
        """Verifica que el valor total se calcula correctamente."""
        inventario = InventarioDenominacionTerminal.objects.create(
            terminal=self.terminal,
            denominacion=self.denom,
            cantidad=25
        )
        
        self.assertEqual(inventario.valor_total, Decimal('2500'))
    
    def test_necesita_reposicion(self):
        """Verifica la propiedad necesita_reposicion."""
        inventario = InventarioDenominacionTerminal.objects.create(
            terminal=self.terminal,
            denominacion=self.denom,
            cantidad=5,
            cantidad_minima=10
        )
        
        self.assertTrue(inventario.necesita_reposicion)
        
        inventario.cantidad = 15
        inventario.save()
        
        self.assertFalse(inventario.necesita_reposicion)


class MFAConfigTestCase(TestCase):
    """Tests para la configuración de MFA."""
    
    def test_mfa_config_singleton(self):
        """Verifica que MFAConfig funciona como singleton."""
        config1 = MFAConfig.get_config()
        config2 = MFAConfig.get_config()
        
        self.assertEqual(config1.id, config2.id)
    
    def test_mfa_tauser_puede_habilitarse(self):
        """Verifica que el MFA para TAUSER puede habilitarse/deshabilitarse."""
        config = MFAConfig.get_config()
        
        # Habilitar
        config.mfa_tauser_enabled = True
        config.save()
        
        config.refresh_from_db()
        self.assertTrue(config.mfa_tauser_enabled)
        
        # Deshabilitar
        config.mfa_tauser_enabled = False
        config.save()
        
        config.refresh_from_db()
        self.assertFalse(config.mfa_tauser_enabled)


class ViewsExternalTestCase(TestCase):
    """Tests para las vistas externas de TAUSER."""
    
    def setUp(self):
        """Configuración inicial."""
        self.client = Client()
        
        self.divisa = Divisa.objects.create(
            code="USD",
            nombre="Dólar",
            simbolo="$",
            is_active=True
        )
        
        self.terminal = Terminal.objects.create(
            codigo="TEST001",
            nombre="Terminal Test",
            ubicacion="Test Location",
            is_activa=True
        )
        
        self.denom = Denominacion.objects.create(
            divisa=self.divisa,
            valor=Decimal('100'),
            is_active=True
        )
        
        self.inventario = InventarioDenominacionTerminal.objects.create(
            terminal=self.terminal,
            denominacion=self.denom,
            cantidad=50
        )
    
    def test_tauser_home_accesible(self):
        """Verifica que la página principal de TAUSER es accesible."""
        response = self.client.get(reverse('tauser_external:home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Terminales TAUSER')
    
    def test_tauser_home_muestra_terminales_activos(self):
        """Verifica que solo muestra terminales activos."""
        # Terminal inactivo
        Terminal.objects.create(
            codigo="INACTIVO",
            nombre="Terminal Inactivo",
            ubicacion="Test",
            is_activa=False
        )
        
        response = self.client.get(reverse('tauser_external:home'))
        
        # Debe mostrar solo el terminal activo
        self.assertContains(response, 'TEST001')
        self.assertNotContains(response, 'INACTIVO')
    
    def test_gestion_inventario_accesible(self):
        """Verifica que la gestión de inventario es accesible sin autenticación."""
        url = reverse('tauser_external:gestion_inventario_denominaciones', 
                     kwargs={'terminal_pk': self.terminal.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)


class MiddlewareTestCase(TestCase):
    """Tests para el middleware modificado."""
    
    def setUp(self):
        """Configuración inicial."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_tauser_rutas_excluidas_de_middleware(self):
        """Verifica que las rutas /tauser/ no son afectadas por ClienteActivoMiddleware."""
        # Login
        self.client.login(username='testuser', password='testpass123')
        
        # Acceder a ruta de TAUSER (no debería redirigir a selección de cliente)
        response = self.client.get('/tauser/')
        
        # Verificar que no redirige (status 200 o 404, pero no 302)
        self.assertIn(response.status_code, [200, 404])


class SessionSecurityTestCase(TestCase):
    """Tests de seguridad de sesiones."""
    
    def setUp(self):
        """Configuración inicial."""
        self.client = Client()
        
        self.cliente = Cliente.objects.create(
            cedula="9876543",
            nombre_completo="Cliente Test",
            email="test@test.com",
            esta_activo=True
        )
        
        self.divisa_pyg = Divisa.objects.create(
            code="PYG",
            nombre="Guaraní",
            simbolo="₲",
            is_active=True
        )
        
        self.divisa_usd = Divisa.objects.create(
            code="USD",
            nombre="Dólar",
            simbolo="$",
            is_active=True
        )
        
        self.transaccion = Transaccion.objects.create(
            cliente=self.cliente,
            tipo_operacion='compra',
            divisa_origen=self.divisa_pyg,
            divisa_destino=self.divisa_usd,
            monto_origen=Decimal('100'),
            monto_destino=Decimal('100'),
            tasa_de_cambio_aplicada=Decimal('1'),
            estado='pendiente'
        )
    
    def test_sesion_independiente_para_tauser(self):
        """Verifica que las sesiones de TAUSER son independientes."""
        # Simular sesión en TAUSER
        session = self.client.session
        session['transaccion_tauser_id'] = self.transaccion.id
        session.save()
        
        # Verificar que la sesión persiste
        self.assertEqual(
            self.client.session.get('transaccion_tauser_id'),
            self.transaccion.id
        )
