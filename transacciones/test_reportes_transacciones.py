"""
Tests para reportes de transacciones
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import json

from transacciones.models import Transaccion
from divisas.models import Divisa
from clientes.models import Cliente, Segmento

User = get_user_model()


class ReporteTransaccionesTest(TestCase):
    """Tests para reportes de transacciones"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Agregar permisos necesarios
        permission = Permission.objects.get(codename='view_transaccion')
        self.user.user_permissions.add(permission)
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Crear datos de prueba
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
        
        self.eur = Divisa.objects.create(
            code='EUR',
            nombre='Euro',
            simbolo='€',
            is_active=True
        )
        
        self.segmento = Segmento.objects.create(name='general')
        self.cliente = Cliente.objects.create(
            cedula='12345678',
            nombre_completo='Juan Pérez',
            email='juan@example.com',
            telefono='0981234567',
            segmento=self.segmento
        )
        
        # Crear transacciones de prueba
        self._crear_transacciones_prueba()
    
    def _crear_transacciones_prueba(self):
        """Crea transacciones de prueba"""
        hoy = timezone.now()
        
        # Transacción 1: Venta USD completada
        trans1 = Transaccion.objects.create(
            numero_transaccion='TRX-001',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('730000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='completado',
            cliente=self.cliente,
            margen_spread=Decimal('50.00')
        )
        trans1.fecha_creacion = hoy
        trans1.save()
        
        # Transacción 2: Compra USD completada
        trans2 = Transaccion.objects.create(
            numero_transaccion='TRX-002',
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
        trans2.fecha_creacion = hoy - timedelta(days=1)
        trans2.save()
        
        # Transacción 3: Venta EUR completada
        trans3 = Transaccion.objects.create(
            numero_transaccion='TRX-003',
            tipo_operacion='venta',
            divisa_origen=self.eur,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('800000.00'),
            tasa_de_cambio_aplicada=Decimal('8000.00'),
            estado='completado',
            cliente=self.cliente,
            margen_spread=Decimal('60.00')
        )
        trans3.fecha_creacion = hoy - timedelta(days=2)
        trans3.save()
        
        # Transacción 4: Pendiente
        trans4 = Transaccion.objects.create(
            numero_transaccion='TRX-004',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('50.00'),
            monto_destino=Decimal('365000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='pendiente',
            cliente=self.cliente
        )
        trans4.fecha_creacion = hoy
        trans4.save()
    
    def test_listar_todas_transacciones(self):
        """Test que lista todas las transacciones"""
        # Verificar que se crearon las transacciones
        transacciones = Transaccion.objects.all()
        self.assertEqual(transacciones.count(), 4)
    
    def test_filtrar_transacciones_por_estado(self):
        """Test de filtrado por estado"""
        completadas = Transaccion.objects.filter(estado='completado')
        pendientes = Transaccion.objects.filter(estado='pendiente')
        
        self.assertEqual(completadas.count(), 3)
        self.assertEqual(pendientes.count(), 1)
    
    def test_filtrar_transacciones_por_tipo_operacion(self):
        """Test de filtrado por tipo de operación"""
        ventas = Transaccion.objects.filter(tipo_operacion='venta')
        compras = Transaccion.objects.filter(tipo_operacion='compra')
        
        self.assertEqual(ventas.count(), 3)
        self.assertEqual(compras.count(), 1)
    
    def test_filtrar_transacciones_por_divisa(self):
        """Test de filtrado por divisa"""
        trans_usd = Transaccion.objects.filter(divisa_origen=self.usd)
        trans_eur = Transaccion.objects.filter(divisa_origen=self.eur)
        
        self.assertEqual(trans_usd.count(), 2)
        self.assertEqual(trans_eur.count(), 1)
    
    def test_filtrar_transacciones_por_cliente(self):
        """Test de filtrado por cliente"""
        trans_cliente = Transaccion.objects.filter(cliente=self.cliente)
        self.assertEqual(trans_cliente.count(), 4)
    
    def test_filtrar_transacciones_por_fecha(self):
        """Test de filtrado por rango de fechas"""
        hoy = timezone.now().date()
        ayer = hoy - timedelta(days=1)
        
        trans_hoy = Transaccion.objects.filter(fecha_creacion__date=hoy)
        trans_ayer = Transaccion.objects.filter(fecha_creacion__date=ayer)
        
        self.assertGreaterEqual(trans_hoy.count(), 1)
        self.assertEqual(trans_ayer.count(), 1)
    
    def test_ordenar_transacciones_por_fecha(self):
        """Test de ordenamiento por fecha"""
        transacciones = Transaccion.objects.all().order_by('-fecha_creacion')
        
        # La primera debe ser la más reciente
        self.assertIn(transacciones.first().numero_transaccion, ['TRX-001', 'TRX-004'])
    
    def test_contar_transacciones_por_tipo(self):
        """Test de conteo por tipo de operación"""
        from django.db.models import Count
        
        stats = Transaccion.objects.values('tipo_operacion').annotate(
            total=Count('id')
        )
        
        self.assertEqual(len(stats), 2)  # compra y venta
    
    def test_sumar_montos_por_divisa(self):
        """Test de suma de montos por divisa"""
        from django.db.models import Sum
        
        # Sumar transacciones en USD
        total_usd = Transaccion.objects.filter(
            divisa_origen=self.usd,
            estado='completado'
        ).aggregate(total=Sum('monto_origen'))
        
        self.assertEqual(total_usd['total'], Decimal('100.00'))
    
    def test_transacciones_con_margen(self):
        """Test de transacciones que tienen margen de spread"""
        con_margen = Transaccion.objects.filter(
            margen_spread__isnull=False,
            margen_spread__gt=0
        )
        
        self.assertEqual(con_margen.count(), 3)
    
    def test_calcular_promedio_tasa(self):
        """Test de cálculo de tasa promedio"""
        from django.db.models import Avg
        
        promedio = Transaccion.objects.filter(
            divisa_origen=self.usd,
            estado='completado'
        ).aggregate(promedio=Avg('tasa_aplicada'))
        
        self.assertIsNotNone(promedio['promedio'])
    
    def test_reporte_por_periodo(self):
        """Test de reporte por período de tiempo"""
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        
        transacciones_mes = Transaccion.objects.filter(
            fecha_creacion__date__gte=inicio_mes,
            fecha_creacion__date__lte=hoy
        )
        
        self.assertGreaterEqual(transacciones_mes.count(), 4)
    
    def test_estadisticas_basicas(self):
        """Test de estadísticas básicas del reporte"""
        from django.db.models import Count, Sum, Avg
        
        stats = Transaccion.objects.filter(estado='completado').aggregate(
            total_transacciones=Count('id'),
            monto_total_origen=Sum('monto_origen'),
            monto_total_destino=Sum('monto_destino'),
            tasa_promedio=Avg('tasa_aplicada')
        )
        
        self.assertEqual(stats['total_transacciones'], 3)
        self.assertIsNotNone(stats['monto_total_origen'])
        self.assertIsNotNone(stats['tasa_promedio'])


class TransaccionModelTest(TestCase):
    """Tests adicionales para el modelo Transaccion"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
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
    
    def test_crear_transaccion_venta(self):
        """Test de creación de transacción de venta"""
        trans = Transaccion.objects.create(
            numero_transaccion='TRX-TEST-001',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('730000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='completado',
            cliente=self.cliente
        )
        
        self.assertEqual(trans.tipo_operacion, 'venta')
        self.assertEqual(trans.estado, 'completado')
        self.assertIsNotNone(trans.fecha_creacion)
    
    def test_crear_transaccion_compra(self):
        """Test de creación de transacción de compra"""
        trans = Transaccion.objects.create(
            numero_transaccion='TRX-TEST-002',
            tipo_operacion='compra',
            divisa_origen=self.pyg,
            divisa_destino=self.usd,
            monto_origen=Decimal('730000.00'),
            monto_destino=Decimal('100.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='completado',
            cliente=self.cliente
        )
        
        self.assertEqual(trans.tipo_operacion, 'compra')
        self.assertEqual(trans.divisa_destino, self.usd)
    
    def test_transaccion_str(self):
        """Test del método __str__ de Transaccion"""
        trans = Transaccion.objects.create(
            numero_transaccion='TRX-TEST-003',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('730000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='completado',
            cliente=self.cliente
        )
        
        str_repr = str(trans)
        self.assertIn('TRX-TEST-003', str_repr)
    
    def test_cambiar_estado_transaccion(self):
        """Test de cambio de estado de transacción"""
        trans = Transaccion.objects.create(
            numero_transaccion='TRX-TEST-004',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('730000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='pendiente',
            cliente=self.cliente
        )
        
        self.assertEqual(trans.estado, 'pendiente')
        
        # Cambiar estado
        trans.estado = 'completado'
        trans.save()
        
        trans.refresh_from_db()
        self.assertEqual(trans.estado, 'completado')
    
    def test_transaccion_con_margen_spread(self):
        """Test de transacción con margen de spread"""
        trans = Transaccion.objects.create(
            numero_transaccion='TRX-TEST-005',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('730000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='completado',
            cliente=self.cliente,
            margen_spread=Decimal('50.00')
        )
        
        self.assertEqual(trans.margen_spread, Decimal('50.00'))
