"""
Tests para reportes de transacciones y ganancias
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import json
from io import BytesIO

from ganancias.models import RegistroGanancia, ResumenGananciaDiaria, ResumenGananciaMensual
from transacciones.models import Transaccion
from divisas.models import Divisa
from clientes.models import Cliente, Segmento

User = get_user_model()


class ReporteTransaccionesGananciasTest(TestCase):
    """Tests para los reportes de transacciones y ganancias"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        permission = Permission.objects.get(codename='view_registroganancia')
        self.user.user_permissions.add(permission)
        
        self.client = Client()
        self.client.login(email='test@example.com', password='testpass123')
        
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
        
        # Crear múltiples transacciones con ganancias
        self._crear_transacciones_prueba()
    
    def _crear_transacciones_prueba(self):
        """Crea transacciones de prueba con ganancias"""
        hoy = timezone.now()
        
        # Transacción 1: Venta USD
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
        
        # Los RegistroGanancia se crean autom�ticamente por signals al crear la transacci�n
        
        # Transacción 2: Compra USD
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
        
        # Los RegistroGanancia se crean autom�ticamente por signals al crear la transacci�n
        
        # Transacción 3: Venta EUR
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
        
        # Los RegistroGanancia se crean autom�ticamente por signals al crear la transacci�n
    
    def test_reporte_muestra_todas_transacciones(self):
        """Test que el reporte muestra todas las transacciones"""
        response = self.client.get(reverse('ganancias:tablero'))
        
        todas_transacciones = response.context['todas_transacciones']
        self.assertIsNotNone(todas_transacciones)
        self.assertGreaterEqual(todas_transacciones.count(), 3)
    
    def test_reporte_calcula_totales_correctamente(self):
        """Test que el reporte calcula los totales correctamente"""
        response = self.client.get(
            reverse('ganancias:tablero'),
            {'periodo': 'todo'}
        )
        
        totales = response.context['totales']
        
        # Total de ganancias: 5000 + 5000 + 6000 = 16000
        self.assertEqual(totales['total_spread'], Decimal('16000.00'))
        self.assertEqual(totales['cantidad_transacciones'], 3)
    
    def test_reporte_filtra_por_divisa(self):
        """Test que el reporte filtra correctamente por divisa"""
        response = self.client.get(
            reverse('ganancias:tablero'),
            {
                'periodo': 'todo',
                'divisa': self.usd.id
            }
        )
        
        totales = response.context['totales']
        
        # Solo las transacciones USD: 5000 + 5000 = 10000
        self.assertEqual(totales['total_spread'], Decimal('10000.00'))
        self.assertEqual(totales['cantidad_transacciones'], 2)
    
    def test_reporte_separa_compras_y_ventas(self):
        """Test que el reporte separa ganancias por tipo de operación"""
        response = self.client.get(
            reverse('ganancias:tablero'),
            {'periodo': 'todo'}
        )
        
        total_compras = response.context['total_compras']
        total_ventas = response.context['total_ventas']
        
        # Compras: 5000
        self.assertEqual(total_compras['total'], Decimal('5000.00'))
        self.assertEqual(total_compras['cantidad'], 1)
        
        # Ventas: 5000 + 6000 = 11000
        self.assertEqual(total_ventas['total'], Decimal('11000.00'))
        self.assertEqual(total_ventas['cantidad'], 2)
    
    def test_reporte_ganancias_por_divisa(self):
        """Test de desglose de ganancias por divisa"""
        response = self.client.get(
            reverse('ganancias:tablero'),
            {'periodo': 'todo'}
        )
        
        ganancias_por_divisa = response.context['ganancias_por_divisa']
        
        # Debe haber 2 divisas (USD y EUR)
        self.assertEqual(len(ganancias_por_divisa), 2)
        
        # Verificar que tiene los campos esperados
        for item in ganancias_por_divisa:
            self.assertIn('divisa_referencia__code', item)
            self.assertIn('total', item)
            self.assertIn('cantidad', item)
    
    def test_reporte_top_transacciones(self):
        """Test del top 10 de transacciones con mayor ganancia"""
        response = self.client.get(
            reverse('ganancias:tablero'),
            {'periodo': 'todo'}
        )
        
        top_transacciones = response.context['top_transacciones']
        
        # Debe haber 3 transacciones
        self.assertEqual(len(top_transacciones), 3)
        
        # Verificar que están ordenadas por monto_total descendente
        ganancias = [float(t.monto_total) for t in top_transacciones]
        self.assertEqual(ganancias, sorted(ganancias, reverse=True))
    
    def test_reporte_promedio_por_transaccion(self):
        """Test del cálculo de promedio por transacción"""
        response = self.client.get(
            reverse('ganancias:tablero'),
            {'periodo': 'todo'}
        )
        
        promedio = response.context['promedio_por_transaccion']
        
        # Promedio: 16000 / 3 = 5333.33
        self.assertAlmostEqual(
            float(promedio),
            5333.33,
            places=2
        )
    
    def test_reporte_variacion_porcentual(self):
        """Test del cálculo de variación porcentual"""
        # Crear ganancias del período anterior
        fecha_anterior = timezone.now() - timedelta(days=30)
        
        trans_anterior = Transaccion.objects.create(
            numero_transaccion='TRX-ANTERIOR',
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
        trans_anterior.fecha_creacion = fecha_anterior
        trans_anterior.save()
        
        # Los RegistroGanancia se crean autom�ticamente por signals al crear la transacci�n
        
        response = self.client.get(
            reverse('ganancias:tablero'),
            {'periodo': 'mes_actual'}
        )
        
        variacion = response.context['variacion_porcentual']
        self.assertIsNotNone(variacion)


class ExportarReporteExcelTest(TestCase):
    """Tests para la exportación de reportes a Excel"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        permission = Permission.objects.get(codename='view_registroganancia')
        self.user.user_permissions.add(permission)
        
        self.client = Client()
        self.client.login(email='test@example.com', password='testpass123')
        
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
        
        self.segmento = Segmento.objects.create(name='general')
        self.cliente = Cliente.objects.create(
            cedula='12345678',
            nombre_completo='Test User',
            email='test@example.com',
            telefono='0981234567',
            segmento=self.segmento
        )
        
        # Crear transacción con ganancia
        trans = Transaccion.objects.create(
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
        
        # Los RegistroGanancia se crean autom�ticamente por signals al crear la transacci�n
    
    def test_exportar_excel_genera_archivo(self):
        """Test que genera un archivo Excel válido"""
        response = self.client.get(reverse('ganancias:exportar_excel'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    def test_exportar_excel_nombre_archivo(self):
        """Test que el nombre del archivo es correcto"""
        response = self.client.get(reverse('ganancias:exportar_excel'))
        
        content_disposition = response['Content-Disposition']
        self.assertIn('attachment', content_disposition)
        self.assertIn('ganancias_', content_disposition)
        self.assertIn('.xlsx', content_disposition)
    
    def test_exportar_excel_con_filtros(self):
        """Test de exportación con filtros aplicados"""
        hoy = timezone.now().date()
        
        response = self.client.get(
            reverse('ganancias:exportar_excel'),
            {
                'periodo': 'mes_actual',
                'divisa': self.usd.id
            }
        )
        
        self.assertEqual(response.status_code, 200)
    
    def test_exportar_excel_contenido_no_vacio(self):
        """Test que el archivo Excel no está vacío"""
        response = self.client.get(reverse('ganancias:exportar_excel'))
        
        # Verificar que el contenido tiene tamaño
        self.assertGreater(len(response.content), 1000)


class ResumenesConsolidadosTest(TestCase):
    """Tests para resúmenes consolidados de ganancias"""
    
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
    
    def test_resumen_diario_se_actualiza_correctamente(self):
        """Test que el resumen diario se actualiza con nuevas transacciones"""
        hoy = timezone.now().date()
        
        # Crear primera transacción
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
            margen_spread=Decimal('50.00')  # Esto genera ganancia de 5000.00
        )
        
        # Los RegistroGanancia se crean autom�ticamente por signals al crear la transacci�n
        
        # Actualizar resumen
        ResumenGananciaDiaria.actualizar_resumen(hoy)
        
        resumen = ResumenGananciaDiaria.objects.get(fecha=hoy)
        self.assertEqual(resumen.total_spread, Decimal('5000.00'))
        self.assertEqual(resumen.cantidad_transacciones, 1)
        
        # Crear segunda transacción
        trans2 = Transaccion.objects.create(
            numero_transaccion='TRX-002',
            tipo_operacion='venta',
            divisa_origen=self.usd,
            divisa_destino=self.pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('730000.00'),
            tasa_de_cambio_aplicada=Decimal('7300.00'),
            estado='completado',
            cliente=self.cliente,
            margen_spread=Decimal('30.00')  # Esto genera ganancia de 3000.00
        )
        
        # Los RegistroGanancia se crean autom�ticamente por signals al crear la transacci�n
        
        # Actualizar resumen nuevamente
        ResumenGananciaDiaria.actualizar_resumen(hoy)
        
        resumen.refresh_from_db()
        self.assertEqual(resumen.total_spread, Decimal('8000.00'))
        self.assertEqual(resumen.cantidad_transacciones, 2)
    
    def test_resumen_mensual_calcula_promedio_diario(self):
        """Test que el resumen mensual calcula el promedio diario"""
        hoy = timezone.now()
        año = hoy.year
        mes = hoy.month
        
        # Crear transacciones que generan registros de ganancia
        for i in range(5):
            Transaccion.objects.create(
                numero_transaccion=f'TRX-{i+1:03d}',
                tipo_operacion='venta',
                divisa_origen=self.usd,
                divisa_destino=self.pyg,
                monto_origen=Decimal('100.00'),
                monto_destino=Decimal('730000.00'),
                tasa_de_cambio_aplicada=Decimal('7300.00'),
                estado='completado',
                cliente=self.cliente,
                margen_spread=Decimal('100.00')  # Genera ganancia de 10000.00
            )
        
        # Actualizar resumen mensual
        resumen_mensual = ResumenGananciaMensual.actualizar_resumen(año, mes)
        
        # Verificar promedio diario
        self.assertGreater(resumen_mensual.promedio_diario, Decimal('0.00'))
        self.assertEqual(resumen_mensual.cantidad_transacciones, 5)
    
    def test_multiples_resumenes_mensuales(self):
        """Test de creación de múltiples resúmenes mensuales"""
        # Crear resúmenes para diferentes meses
        for mes in range(1, 13):
            ResumenGananciaMensual.objects.create(
                año=2024,
                mes=mes,
                total_spread=Decimal(str(mes * 10000)),
                total_general=Decimal(str(mes * 10000)),
                cantidad_transacciones=mes * 10
            )
        
        # Verificar que se crearon todos
        resumenes = ResumenGananciaMensual.objects.filter(año=2024)
        self.assertEqual(resumenes.count(), 12)
        
        # Verificar ordenamiento (más reciente primero)
        primer_resumen = resumenes.first()
        self.assertEqual(primer_resumen.mes, 12)
