"""
Tests para los modelos del módulo de ganancias
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import datetime, timedelta

from ganancias.models import RegistroGanancia, ResumenGananciaDiaria, ResumenGananciaMensual
from transacciones.models import Transaccion
from divisas.models import Divisa, CotizacionSegmento
from clientes.models import Cliente, Segmento

User = get_user_model()


class RegistroGananciaModelTest(TestCase):
    """Tests para el modelo RegistroGanancia"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear usuario
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear divisas
        self.pyg = Divisa.objects.create(
            code='PYG',
            nombre='Guaraní Paraguayo',
            simbolo='Gs.',
            is_active=True
        )
        
        self.usd = Divisa.objects.create(
            code='USD',
            nombre='Dólar Americano',
            simbolo='$',
            is_active=True
        )
        
        # Crear segmento
        self.segmento = Segmento.objects.create(
            name='general'
        )
        
        # Crear cliente
        self.cliente = Cliente.objects.create(
            cedula='12345678',
            nombre_completo='Juan Pérez',
            email='juan@example.com',
            telefono='0981234567',
            segmento=self.segmento
        )
        
        # Crear transacción
        self.transaccion = Transaccion.objects.create(
            numero_transaccion='TRX-TEST-001',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('730000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='completado',
            cliente=self.cliente,
            margen_spread=Decimal('50.00')  # Ganancia de 50 Gs por dólar
        )
    
    def test_crear_registro_ganancia(self):
        """Test de creación básica de un registro de ganancia"""
        # El registro se crea automáticamente via signal al guardar la transacción
        registro = RegistroGanancia.objects.get(transaccion=self.transaccion)
        
        # Verificar que el registro existe y tiene los datos correctos
        self.assertIsNotNone(registro)
        self.assertEqual(registro.transaccion, self.transaccion)
        self.assertGreater(registro.monto_total, Decimal('0.00'))
        self.assertIsNotNone(registro.fecha_registro)
    
    def test_registro_ganancia_str(self):
        """Test del método __str__ del modelo"""
        # Obtener el registro creado automáticamente por signal
        registro = RegistroGanancia.objects.get(transaccion=self.transaccion)
        
        str_repr = str(registro)
        self.assertIn('TRX-TEST-001', str_repr)
    
    def test_registro_ganancia_save_calcula_monto_total(self):
        """Test que el método save calcula correctamente el monto total"""
        # Obtener el registro creado automáticamente
        registro = RegistroGanancia.objects.get(transaccion=self.transaccion)
        
        # Modificar valores y guardar para verificar que recalcula monto_total
        registro.monto_spread = Decimal('5000.00')
        registro.save()
        
        # Verificar que el monto total se calculó correctamente
        self.assertEqual(registro.monto_total, Decimal('5000.00'))
    
    def test_calcular_ganancia_transaccion_venta(self):
        """Test de cálculo de ganancia para transacción de venta"""
        registro = RegistroGanancia.calcular_ganancia_transaccion(self.transaccion)
        
        self.assertIsNotNone(registro)
        self.assertEqual(registro.transaccion, self.transaccion)
        self.assertEqual(registro.tipo_ganancia, 'spread')
        # Ganancia = margen_spread × monto_origen (100 USD × 50 Gs = 5000 Gs)
        self.assertEqual(registro.monto_spread, Decimal('5000.00'))
        self.assertEqual(registro.divisa_referencia, self.usd)
    
    def test_calcular_ganancia_transaccion_compra(self):
        """Test de cálculo de ganancia para transacción de compra"""
        transaccion_compra = Transaccion.objects.create(
            numero_transaccion='TRX-TEST-002',
            tipo_operacion='compra',
            divisa_origen=self.pyg,
            divisa_destino=self.usd,
            monto_origen=Decimal('730000.00'),
            monto_destino=Decimal('100.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='completado',
            cliente=self.cliente,
            margen_spread=Decimal('50.00')
        )
        
        registro = RegistroGanancia.calcular_ganancia_transaccion(transaccion_compra)
        
        self.assertIsNotNone(registro)
        self.assertEqual(registro.tipo_ganancia, 'spread')
        # En compra: margen_spread × monto_destino (100 USD × 50 Gs = 5000 Gs)
        self.assertEqual(registro.monto_spread, Decimal('5000.00'))
        self.assertEqual(registro.divisa_referencia, self.usd)
    
    def test_calcular_ganancia_transaccion_pendiente_retorna_none(self):
        """Test que no calcula ganancia para transacciones no completadas"""
        transaccion_pendiente = Transaccion.objects.create(
            numero_transaccion='TRX-TEST-003',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('730000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='pendiente',
            cliente=self.cliente,
            margen_spread=Decimal('50.00')
        )
        
        registro = RegistroGanancia.calcular_ganancia_transaccion(transaccion_pendiente)
        self.assertIsNone(registro)
    
    def test_registro_ganancia_ordering(self):
        """Test del ordenamiento por defecto de registros"""
        fecha1 = timezone.now() - timedelta(days=2)
        fecha2 = timezone.now() - timedelta(days=1)
        fecha3 = timezone.now()
        
        # Crear transacciones con diferentes fechas
        trans1 = Transaccion.objects.create(
            numero_transaccion='TRX-001',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('730000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='completado',
            cliente=self.cliente
        )
        trans1.fecha_creacion = fecha1
        trans1.save()
        
        trans2 = Transaccion.objects.create(
            numero_transaccion='TRX-002',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('730000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='completado',
            cliente=self.cliente
        )
        trans2.fecha_creacion = fecha2
        trans2.save()
        
        # Los registros de ganancia se crean automáticamente por signals
        # Obtenerlos para verificar el ordenamiento
        reg1 = RegistroGanancia.objects.get(transaccion=trans1)
        reg2 = RegistroGanancia.objects.get(transaccion=trans2)
        
        # Verificar ordenamiento (más reciente primero)
        # Filtrar solo los registros de este test
        registros = list(RegistroGanancia.objects.filter(transaccion__in=[trans1, trans2]).order_by('-fecha_registro'))
        self.assertEqual(len(registros), 2)
        self.assertEqual(registros[0], reg2)
        self.assertEqual(registros[1], reg1)


class ResumenGananciaDiariaModelTest(TestCase):
    """Tests para el modelo ResumenGananciaDiaria"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.pyg = Divisa.objects.create(
            code='PYG',
            nombre='Guaraní Paraguayo',
            simbolo='Gs.',
            is_active=True
        )
        
        self.usd = Divisa.objects.create(
            code='USD',
            nombre='Dólar Americano',
            simbolo='$',
            is_active=True
        )
        
        self.segmento = Segmento.objects.create(name='general')
        self.cliente = Cliente.objects.create(
            cedula='12345678',
            nombre_completo='Test User',
            email='test@example.com',
            telefono='0981234567',
            segmento=self.segmento
        )
    
    def test_crear_resumen_diario(self):
        """Test de creación de resumen diario"""
        hoy = timezone.now().date()
        resumen = ResumenGananciaDiaria.objects.create(
            fecha=hoy,
            total_comisiones=Decimal('1000.00'),
            total_spread=Decimal('5000.00'),
            total_general=Decimal('5000.00'),
            cantidad_transacciones=10
        )
        
        self.assertEqual(resumen.fecha, hoy)
        self.assertEqual(resumen.total_general, Decimal('5000.00'))
        self.assertEqual(resumen.cantidad_transacciones, 10)
    
    def test_resumen_diario_str(self):
        """Test del método __str__"""
        hoy = timezone.now().date()
        resumen = ResumenGananciaDiaria.objects.create(
            fecha=hoy,
            total_general=Decimal('10000.00')
        )
        
        str_repr = str(resumen)
        self.assertIn(str(hoy), str_repr)
        self.assertIn('10000', str_repr)
    
    def test_actualizar_resumen_vacio(self):
        """Test de actualización de resumen sin ganancias"""
        hoy = timezone.now().date()
        resumen = ResumenGananciaDiaria.actualizar_resumen(hoy)
        
        self.assertIsNotNone(resumen)
        self.assertEqual(resumen.total_general, Decimal('0.00'))
        self.assertEqual(resumen.cantidad_transacciones, 0)
    
    def test_actualizar_resumen_con_ganancias(self):
        """Test de actualización de resumen con ganancias existentes"""
        hoy = timezone.now().date()
        
        # Crear transacción y ganancia
        transaccion = Transaccion.objects.create(
            numero_transaccion='TRX-001',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('730000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='completado',
            cliente=self.cliente,
            margen_spread=Decimal('5000.00')
        )
        
        # El RegistroGanancia se crea automáticamente por signal
        # Actualizar resumen
        resumen = ResumenGananciaDiaria.actualizar_resumen(hoy)
        
        self.assertIsNotNone(resumen)
        self.assertGreater(resumen.total_general, Decimal('0.00'))
        self.assertEqual(resumen.cantidad_transacciones, 1)
    
    def test_resumen_diario_fecha_unica(self):
        """Test que la fecha es única en el modelo"""
        hoy = timezone.now().date()
        
        ResumenGananciaDiaria.objects.create(fecha=hoy)
        
        with self.assertRaises(Exception):
            ResumenGananciaDiaria.objects.create(fecha=hoy)


class ResumenGananciaMensualModelTest(TestCase):
    """Tests para el modelo ResumenGananciaMensual"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.pyg = Divisa.objects.create(
            code='PYG',
            nombre='Guaraní Paraguayo',
            simbolo='Gs.',
            is_active=True
        )
        
        self.usd = Divisa.objects.create(
            code='USD',
            nombre='Dólar Americano',
            simbolo='$',
            is_active=True
        )
        
        self.segmento = Segmento.objects.create(name='general')
        self.cliente = Cliente.objects.create(
            cedula='12345678',
            nombre_completo='Test User',
            email='test@example.com',
            telefono='0981234567',
            segmento=self.segmento
        )
    
    def test_crear_resumen_mensual(self):
        """Test de creación de resumen mensual"""
        resumen = ResumenGananciaMensual.objects.create(
            año=2024,
            mes=12,
            total_comisiones=Decimal('10000.00'),
            total_spread=Decimal('50000.00'),
            total_general=Decimal('50000.00'),
            cantidad_transacciones=100,
            promedio_diario=Decimal('1666.67')
        )
        
        self.assertEqual(resumen.año, 2024)
        self.assertEqual(resumen.mes, 12)
        self.assertEqual(resumen.total_general, Decimal('50000.00'))
    
    def test_resumen_mensual_str(self):
        """Test del método __str__"""
        resumen = ResumenGananciaMensual.objects.create(
            año=2024,
            mes=12,
            total_general=Decimal('50000.00')
        )
        
        str_repr = str(resumen)
        self.assertIn('12/2024', str_repr)
        self.assertIn('50000', str_repr)
    
    def test_actualizar_resumen_mensual(self):
        """Test de actualización de resumen mensual"""
        hoy = timezone.now()
        año = hoy.year
        mes = hoy.month
        
        # Crear algunas ganancias
        transaccion = Transaccion.objects.create(
            numero_transaccion='TRX-001',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('730000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='completado',
            cliente=self.cliente,
            margen_spread=Decimal('5000.00')
        )
        
        # El RegistroGanancia se crea automáticamente por signal
        # Obtener o crear resumen diario
        resumen_diario, _ = ResumenGananciaDiaria.objects.get_or_create(
            fecha=hoy.date(),
            defaults={
                'total_spread': Decimal('5000.00'),
                'total_general': Decimal('5000.00'),
                'cantidad_transacciones': 1
            }
        )
        
        # Actualizar resumen mensual
        resumen = ResumenGananciaMensual.actualizar_resumen(año, mes)
        
        self.assertIsNotNone(resumen)
        self.assertEqual(resumen.año, año)
        self.assertEqual(resumen.mes, mes)
        self.assertGreaterEqual(resumen.total_general, Decimal('5000.00'))
    
    def test_resumen_mensual_unique_together(self):
        """Test que año y mes son únicos juntos"""
        ResumenGananciaMensual.objects.create(año=2024, mes=12)
        
        with self.assertRaises(Exception):
            ResumenGananciaMensual.objects.create(año=2024, mes=12)
    
    def test_resumen_mensual_ordering(self):
        """Test del ordenamiento por defecto"""
        ResumenGananciaMensual.objects.create(año=2024, mes=1)
        ResumenGananciaMensual.objects.create(año=2024, mes=12)
        ResumenGananciaMensual.objects.create(año=2023, mes=12)
        
        resumenes = list(ResumenGananciaMensual.objects.all())
        
        # Debe estar ordenado por año DESC, mes DESC
        self.assertEqual(resumenes[0].año, 2024)
        self.assertEqual(resumenes[0].mes, 12)
        self.assertEqual(resumenes[1].año, 2024)
        self.assertEqual(resumenes[1].mes, 1)
        self.assertEqual(resumenes[2].año, 2023)
