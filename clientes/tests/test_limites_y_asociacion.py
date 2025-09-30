"""
Pruebas para límites y asociaciones.
"""
from django.test import TestCase

# ⚠️ ACTUALIZAR IMPORTS
from clientes.models import LimiteDiario, LimiteMensual, Cliente, AsignacionCliente

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date, time, timedelta
from unittest.mock import patch, MagicMock, PropertyMock
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

# Importaciones
from clientes.models import Cliente, AsignacionCliente, Segmento, LimiteDiario, LimiteMensual
from clientes.services import verificar_limites
from clientes.forms import LimiteDiarioForm, LimiteMensualForm # Necesarias para los tests de validación

User = get_user_model()


# --- CLASE DE PRUEBAS PARA ASOCIACIÓN ---
class AdminAsociacionTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpassword',
            email='admin@example.com'
        )
        self.normal_user = User.objects.create_user(
            username='user1',
            password='password123'
        )
        self.segmento_prueba = Segmento.objects.create(name='Minorista')
        self.cliente1 = Cliente.objects.create(
            nombre_completo='Cliente Uno',
            cedula='1111',
            segmento=self.segmento_prueba
        )

    def test_admin_asociar_clientes_direct(self):
        """Test directo de creación de asociación sin vista web."""
        AsignacionCliente.objects.create(
            usuario=self.normal_user, 
            cliente=self.cliente1
        )
        self.assertTrue(AsignacionCliente.objects.filter(
            usuario=self.normal_user, cliente=self.cliente1
        ).exists())


# --- CLASE DE PRUEBAS DE LÍMITES (Servicio 'verificar_limites') ---
class TestVerificarLimitesService(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.segmento_prueba = Segmento.objects.create(name='Test')
        self.cliente = Cliente.objects.create(
            cedula='12345678',
            nombre_completo='Cliente Test',
            segmento=self.segmento_prueba,
            esta_activo=True
        )

    def _create_mock_queryset_with_aggregate(self, total_value):
        """
        Crea un mock que simula el resultado de la agregación de transacciones.
        """
        total_decimal = Decimal(total_value) if total_value is not None else Decimal('0')
        
        aggregate_dict = {'total': total_decimal} 
        mock_qs = MagicMock()
        mock_qs.aggregate.return_value = aggregate_dict
        mock_relation = MagicMock()
        mock_qs_intermediate = MagicMock()
        
        # Simula .all().exclude().filter()
        mock_qs_intermediate.exclude.return_value.filter.return_value = mock_qs
        # Simula .all().filter()
        mock_qs_intermediate.filter.return_value = mock_qs
        
        mock_relation.all.return_value = mock_qs_intermediate
        
        return mock_relation

    def _setup_mocks_fecha_diario(self):
        """Configura los mocks de fecha para un test diario."""
        patch('clientes.services.timezone.localdate', return_value=date(2024, 1, 15)).start()
        
        mock_make_aware = patch('clientes.services.timezone.make_aware').start()
        mock_datetime_module = patch('clientes.services.datetime').start()

        mock_date = date(2024, 1, 15)
        mock_datetime_combined = datetime.combine(mock_date, time.min)
        mock_datetime_module.combine.return_value = mock_datetime_combined
        mock_make_aware.return_value = mock_datetime_combined
        
        return mock_date

    def _setup_mocks_fecha_mensual(self):
        """Configura los mocks de fecha para un test mensual."""
        patch('clientes.services.timezone.localdate', return_value=date(2024, 1, 15)).start()
        patch('clientes.services.timezone.make_aware').start()
        patch('clientes.services.datetime').start()
        
        mock_mes = date(2024, 1, 1)
        return mock_mes
    
    def tearDown(self):
        # Limpiar todos los mocks después de cada prueba
        patch.stopall()

    # --- CASOS DE ÉXITO (APROBADO) ---

    def test_sin_limites_retorna_true(self):
        """Test sin límites configurados debe retornar True. (Paso Normal)"""
        resultado, mensaje = verificar_limites(self.cliente, Decimal('10000.00'))
        self.assertTrue(resultado)

    @patch('clientes.models.Cliente.transacciones', new_callable=PropertyMock)
    def test_limite_diario_aprobado(self, mock_transacciones_property):
        """Test límite diario no superado, debe retornar True. (Paso Normal)"""
        self._setup_mocks_fecha_diario()
        LimiteDiario.objects.create(fecha=date(2024, 1, 15), monto=Decimal('50000.00'), inicio_vigencia=timezone.now())
        
        # 40000 + 10000 = 50000 <= 50000 (límite) -> True
        mock_manager = self._create_mock_queryset_with_aggregate('40000.00')
        mock_transacciones_property.return_value = mock_manager

        resultado, mensaje = verificar_limites(self.cliente, Decimal('10000.00'))
        self.assertTrue(resultado)

    @patch('clientes.models.Cliente.transacciones', new_callable=PropertyMock)
    def test_limite_diario_borde_igual_pasa(self, mock_transacciones_property):
        """Test límite diario al borde (igual), debe retornar True. (Paso de Borde)"""
        self._setup_mocks_fecha_diario()
        LimiteDiario.objects.create(fecha=date(2024, 1, 15), monto=Decimal('50000.00'), inicio_vigencia=timezone.now())
        
        # 49900 + 100 = 50000 <= 50000 (límite) -> True
        mock_manager = self._create_mock_queryset_with_aggregate('49900.00')
        mock_transacciones_property.return_value = mock_manager

        resultado, mensaje = verificar_limites(self.cliente, Decimal('100.00'))
        self.assertTrue(resultado)

    @patch('clientes.models.Cliente.transacciones', new_callable=PropertyMock)
    def test_verificar_limites_excluyendo_transaccion(self, mock_transacciones_property):
        """Test de caso de edición (excluir), debe retornar True. (Paso Normal)"""
        self._setup_mocks_fecha_diario()
        LimiteDiario.objects.create(fecha=date(2024, 1, 15), monto=Decimal('50000.00'), inicio_vigencia=timezone.now())
        
        transaccion_a_excluir = MagicMock(pk=10)
        
        # 40000 (previo excluido) + 5000 (monto nuevo) = 45000 < 50000 (límite) -> True
        mock_manager = self._create_mock_queryset_with_aggregate('40000.00')
        mock_transacciones_property.return_value = mock_manager
        
        resultado, mensaje = verificar_limites(self.cliente, Decimal('5000.00'), transaccion_a_excluir)
        self.assertTrue(resultado)
        
    # --- CASOS DE FALLO (RECHAZADO) ---

    @patch('clientes.models.Cliente.transacciones', new_callable=PropertyMock)
    def test_limite_diario_superado(self, mock_transacciones_property):
        """Test límite diario superado, debe retornar False. (Fallo Normal)"""
        self._setup_mocks_fecha_diario()
        LimiteDiario.objects.create(fecha=date(2024, 1, 15), monto=Decimal('50000.00'), inicio_vigencia=timezone.now())
        
        # 40000 + 15000 = 55000 > 50000 (límite) -> False
        mock_manager = self._create_mock_queryset_with_aggregate('40000.00')
        mock_transacciones_property.return_value = mock_manager
        
        resultado, mensaje = verificar_limites(self.cliente, Decimal('15000.00'))
        
        self.assertFalse(resultado) 
        self.assertIn("Supera el límite diario", mensaje)

    @patch('clientes.models.Cliente.transacciones', new_callable=PropertyMock)
    def test_limite_diario_superado_borde(self, mock_transacciones_property):
        """Test límite diario superado por 1 céntimo, debe retornar False. (Fallo de Borde)"""
        self._setup_mocks_fecha_diario()
        LimiteDiario.objects.create(fecha=date(2024, 1, 15), monto=Decimal('50000.00'), inicio_vigencia=timezone.now())
        
        # 49999.99 + 0.02 = 50000.01 > 50000.00 (límite) -> False
        mock_manager = self._create_mock_queryset_with_aggregate('49999.99')
        mock_transacciones_property.return_value = mock_manager
        
        resultado, mensaje = verificar_limites(self.cliente, Decimal('0.02'))
        
        self.assertFalse(resultado) 
        self.assertIn("Supera el límite diario", mensaje)

    @patch('clientes.models.Cliente.transacciones', new_callable=PropertyMock)
    def test_limite_mensual_superado(self, mock_transacciones_property):
        """Test límite mensual superado, debe retornar False. (Fallo Normal)"""
        mock_mes = self._setup_mocks_fecha_mensual()
        
        LimiteDiario.objects.all().delete()
        LimiteMensual.objects.create(mes=mock_mes, monto=Decimal('500000.00'), inicio_vigencia=timezone.now())
        
        # 450000 + 80000 = 530000 > 500000 (límite) -> False
        mock_manager = self._create_mock_queryset_with_aggregate('450000.00')
        mock_transacciones_property.return_value = mock_manager
        
        resultado, mensaje = verificar_limites(self.cliente, Decimal('80000.00'))
        
        self.assertFalse(resultado)
        self.assertIn("Supera el límite mensual", mensaje)

    @patch('clientes.models.Cliente.transacciones', new_callable=PropertyMock)
    def test_limite_cero_superado(self, mock_transacciones_property):
        """Test donde el límite está en 0.00, debe fallar al intentar aprobar cualquier monto > 0. (Fallo Extremo)"""
        self._setup_mocks_fecha_diario()
        LimiteDiario.objects.create(fecha=date(2024, 1, 15), monto=Decimal('0.00'), inicio_vigencia=timezone.now())
        
        # 0.00 (previo) + 10.00 (nuevo) = 10.00 > 0.00 (límite) -> False
        mock_manager = self._create_mock_queryset_with_aggregate('0.00')
        mock_transacciones_property.return_value = mock_manager
        
        resultado, mensaje = verificar_limites(self.cliente, Decimal('10.00'))
        
        self.assertFalse(resultado)
        self.assertIn("Supera el límite diario", mensaje)

# --- CLASE DE PRUEBAS PARA VALIDACIÓN DE FORMULARIOS (Fechas Pasadas) ---
class TestLimiteFormsValidation(TestCase):
    
    def setUp(self):
        self.segmento_prueba = Segmento.objects.create(name='Test')
        self.cliente = Cliente.objects.create(
            cedula='12345678',
            nombre_completo='Cliente Test',
            segmento=self.segmento_prueba,
            esta_activo=True
        )

    @patch('django.utils.timezone.localdate')
    def test_limite_diario_fecha_pasada_falla(self, mock_localdate):
        """
        Verifica que LimiteDiarioForm rechaza una fecha pasada e imprime errores.
        """
        mock_localdate.return_value = date(2024, 1, 15)
        
        fecha_ayer = date(2024, 1, 14)

        data = {
            'fecha': fecha_ayer.strftime('%Y-%m-%d'), 
            'monto': '1000.00'
        }
        
        form = LimiteDiarioForm(data=data)
        
        if not form.is_valid():
            # ⬇️ IMPRESIÓN MEJORADA: Usar dict(form.errors) para un formato limpio
            print(f"\n🚨 Errores de Formulario (Fecha Pasada Diario):\n{dict(form.errors)}")
        self.assertFalse(form.is_valid())
        self.assertIn('fecha', form.errors)
        self.assertIn("No se pueden registrar límites en fechas pasadas.", form.errors['fecha'][0]) 


    @patch('django.utils.timezone.localdate')
    def test_limite_mensual_mes_pasado_falla(self, mock_localdate):
        """
        Verifica que LimiteMensualForm rechaza un mes pasado e imprime errores.
        """
        mock_localdate.return_value = date(2024, 3, 20)
        
        mes_pasado = date(2024, 2, 1)

        data = {
            'mes': mes_pasado.strftime('%Y-%m'), 
            'monto': '100000.00'
        }
        
        form = LimiteMensualForm(data=data)
        
        if not form.is_valid():
            # ⬇️ IMPRESIÓN MEJORADA: Usar dict(form.errors) para un formato limpio
            print(f"\n🚨 Errores de Formulario (Mes Pasado Mensual):\n{dict(form.errors)}")
        self.assertFalse(form.is_valid())
        self.assertIn('mes', form.errors)
        self.assertIn("No se pueden registrar límites en meses pasados.", form.errors['mes'][0])


    @patch('django.utils.timezone.localdate')
    def test_limite_diario_fecha_futura_pasa(self, mock_localdate):
        """
        Verifica que LimiteDiarioForm acepta una fecha futura. (Paso de Formulario)
        """
        mock_localdate.return_value = date(2024, 1, 15)
        
        fecha_mañana = date(2024, 1, 16) 

        data = {
            'fecha': fecha_mañana.strftime('%Y-%m-%d'), 
            'monto': '2000.00'
        }
        
        form = LimiteDiarioForm(data=data)
        
        # ⬇️ IMPRESIÓN MEJORADA: Usar el f-string para la aserción
        self.assertTrue(form.is_valid(), f"Formulario no es válido: {dict(form.errors)}") 
        
        limite_creado = form.save()
        self.assertEqual(LimiteDiario.objects.filter(fecha=fecha_mañana).count(), 1)


# --- CLASE DE PRUEBAS DE MODELOS BÁSICOS ---
class TestModelosBasicos(TestCase):
    
    def setUp(self):
        self.segmento = Segmento.objects.create(name='Test Segmento')
    
    def test_crear_cliente_basico(self):
        """Test básico de creación de cliente"""
        cliente = Cliente.objects.create(
            cedula='123456',
            nombre_completo='Test Cliente',
            segmento=self.segmento,
            esta_activo=True
        )
        
        self.assertEqual(cliente.cedula, '123456')
        self.assertEqual(cliente.nombre_completo, 'Test Cliente')
        self.assertEqual(cliente.segmento, self.segmento)
        self.assertTrue(cliente.esta_activo)
    
    def test_crear_limite_diario(self):
        """Test básico de creación de límite diario"""
        fecha_limite = date(2024, 1, 15)
        limite = LimiteDiario.objects.create(
            fecha=fecha_limite,
            monto=Decimal('50000.00'),
            inicio_vigencia=timezone.now()
        )
        
        self.assertEqual(limite.fecha, fecha_limite)
        self.assertEqual(limite.monto, Decimal('50000.00'))
    
    def test_crear_limite_mensual(self):
        """Test básico de creación de límite mensual"""
        mes_limite = date(2024, 1, 1)
        limite = LimiteMensual.objects.create(
            mes=mes_limite,
            monto=Decimal('500000.00'),
            inicio_vigencia=timezone.now()
        )
        
        self.assertEqual(limite.mes, mes_limite)
        self.assertEqual(limite.monto, Decimal('500000.00'))

    @patch('django.utils.timezone.localdate')
    def test_limite_diario_duplicado_falla(self, mock_localdate):
        """Verifica que LimiteDiarioForm rechaza una fecha que ya existe e imprime errores."""
        hoy = date(2025, 1, 15)
        mock_localdate.return_value = hoy
        
        LimiteDiario.objects.create(
            fecha=hoy, 
            monto=Decimal('100.00'), 
            inicio_vigencia=timezone.now()
        )

        data = {
            'fecha': hoy.strftime('%Y-%m-%d'), 
            'monto': '2000.00'
        }
        
        form = LimiteDiarioForm(data=data)
        
        if not form.is_valid():
            # ⬇️ IMPRESIÓN MEJORADA
            print(f"\n🚨 Errores de Formulario (Duplicado Diario):\n{dict(form.errors)}")
        self.assertFalse(form.is_valid())
        self.assertIn('fecha', form.errors)
        self.assertIn("Ya existe un límite configurado para esta fecha.", form.errors['fecha'][0])


    @patch('django.utils.timezone.localdate')
    def test_limite_mensual_duplicado_falla(self, mock_localdate):
        """Verifica que LimiteMensualForm rechaza un mes que ya existe e imprime errores."""
        mes_actual = date(2025, 1, 1)
        mock_localdate.return_value = date(2025, 1, 15)

        LimiteMensual.objects.create(
            mes=mes_actual, 
            monto=Decimal('100.00'), 
            inicio_vigencia=timezone.now()
        )

        data = {
            'mes': mes_actual.strftime('%Y-%m'), 
            'monto': '200000.00'
        }
        
        form = LimiteMensualForm(data=data)
        
        if not form.is_valid():
            # ⬇️ IMPRESIÓN MEJORADA
            print(f"\n🚨 Errores de Formulario (Duplicado Mensual):\n{dict(form.errors)}")
        self.assertFalse(form.is_valid())
        self.assertIn('mes', form.errors)
        self.assertIn("Ya existe un límite configurado para este mes.", form.errors['mes'][0])


    def test_limite_diario_monto_negativo_falla(self):
        """Verifica que LimiteDiarioForm rechaza montos negativos (por validadores de modelo) e imprime errores."""
        fecha_futura = timezone.localdate() + timedelta(days=1)
        data = {
            'fecha': fecha_futura.strftime('%Y-%m-%d'), 
            'monto': '-10.00'
        }
        
        form = LimiteDiarioForm(data=data)
        
        if not form.is_valid():
            # ⬇️ IMPRESIÓN MEJORADA
            print(f"\n🚨 Errores de Formulario (Monto Negativo Diario):\n{dict(form.errors)}")
        self.assertFalse(form.is_valid())
        self.assertIn('monto', form.errors)
        expected_error_found = any(
            "mayor o igual a 0" in err or "greater than or equal to 0" in err
            for err in form.errors['monto']
        )
        self.assertTrue(expected_error_found, f"Mensaje de error inesperado: {form.errors['monto']}")

    
    def test_limite_diario_monto_vacio_falla(self):
        """Verifica que LimiteDiarioForm rechaza un monto vacío e imprime errores."""
        fecha_futura = timezone.localdate() + timedelta(days=1)
        data = {
            'fecha': fecha_futura.strftime('%Y-%m-%d'), 
            'monto': '' # Campo vacío
        }
        
        form = LimiteDiarioForm(data=data)
        
        if not form.is_valid():
            # ⬇️ IMPRESIÓN MEJORADA
            print(f"\n🚨 Errores de Formulario (Monto Vacío Diario):\n{dict(form.errors)}")
        self.assertFalse(form.is_valid())
        self.assertIn('monto', form.errors)
        self.assertIn("This field is required.", form.errors['monto'])