"""
Tests para evolución histórica de tasas de cambio
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import json

from divisas.models import Divisa, CotizacionSegmento, TasaCambio
from clientes.models import Cliente, Segmento

User = get_user_model()


class HistoricoTasasViewTest(TestCase):
    """Tests para la vista de histórico de tasas de cambio"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Agregar permisos necesarios
        permission = Permission.objects.get(codename='view_cotizaciones_segmento')
        self.user.user_permissions.add(permission)
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
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
        
        self.eur = Divisa.objects.create(
            code='EUR',
            nombre='Euro',
            simbolo='€',
            is_active=True
        )
        
        # Crear segmento
        self.segmento = Segmento.objects.create(
            name='general'\r\n        )
        
        # Crear cliente
        self.cliente = Cliente.objects.create(
            cedula='12345678',
            nombre_completo='Test User',
            email='test@example.com',
            telefono='0981234567',
            segmento=self.segmento
        )
        
        # Crear cotizaciones históricas
        hoy = timezone.now()
        for i in range(30):
            fecha = hoy - timedelta(days=i)
            
            CotizacionSegmento.objects.create(
                divisa=self.usd,
                segmento=self.segmento,
                precio_base=Decimal('7300.00') + Decimal(str(i * 10)),
                comision_compra=Decimal('50.00'),
                comision_venta=Decimal('50.00'),
                valor_compra_unit=Decimal('7250.00') + Decimal(str(i * 10)),
                valor_venta_unit=Decimal('7350.00') + Decimal(str(i * 10)),
                porcentaje_descuento=Decimal('0.00'),
                fecha=fecha
            )
            
            CotizacionSegmento.objects.create(
                divisa=self.eur,
                segmento=self.segmento,
                precio_base=Decimal('8000.00') + Decimal(str(i * 10)),
                comision_compra=Decimal('50.00'),
                comision_venta=Decimal('50.00'),
                valor_compra_unit=Decimal('7950.00') + Decimal(str(i * 10)),
                valor_venta_unit=Decimal('8050.00') + Decimal(str(i * 10)),
                porcentaje_descuento=Decimal('0.00'),
                fecha=fecha
            )
    
    def test_historico_tasas_view_requiere_login(self):
        """Test que la vista requiere autenticación"""
        self.client.logout()
        response = self.client.get(reverse('divisas:historico_tasas'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_historico_tasas_view_sin_permisos(self):
        """Test que la vista requiere permisos"""
        user_sin_permisos = User.objects.create_user(
            username='sinpermisos',
            password='testpass123'
        )
        self.client.login(username='sinpermisos', password='testpass123')
        
        response = self.client.get(reverse('divisas:historico_tasas'))
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_historico_tasas_view_con_permisos(self):
        """Test que la vista funciona con permisos correctos"""
        response = self.client.get(reverse('divisas:historico_tasas'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'historico_tasas.html')
    
    def test_historico_tasas_muestra_divisas_activas(self):
        """Test que la vista muestra las divisas activas"""
        response = self.client.get(reverse('divisas:historico_tasas'))
        
        divisas_activas = response.context['divisas_activas']
        self.assertIsNotNone(divisas_activas)
        self.assertIn(self.usd, divisas_activas)
        self.assertIn(self.eur, divisas_activas)
    
    def test_historico_tasas_muestra_segmento_activo(self):
        """Test que la vista muestra el segmento activo"""
        # Simular cliente activo en sesión
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()
        
        response = self.client.get(reverse('divisas:historico_tasas'))
        
        segmento_activo = response.context['segmento_activo']
        self.assertEqual(segmento_activo, self.segmento)
    
    def test_historico_tasas_muestra_cotizaciones(self):
        """Test que la vista muestra cotizaciones actuales"""
        response = self.client.get(reverse('divisas:historico_tasas'))
        
        divisas_data = response.context['divisas_data']
        self.assertIsNotNone(divisas_data)
        self.assertGreater(len(divisas_data), 0)


class ApiHistoricoTasasTest(TestCase):
    """Tests para la API de histórico de tasas"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        permission = Permission.objects.get(codename='view_cotizaciones_segmento')
        self.user.user_permissions.add(permission)
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
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
        self.segmento = Segmento.objects.create(name='general')
        
        # Crear cotizaciones históricas
        hoy = timezone.now()
        for i in range(30):
            fecha = hoy - timedelta(days=i)
            
            CotizacionSegmento.objects.create(
                divisa=self.usd,
                segmento=self.segmento,
                precio_base=Decimal('7300.00') + Decimal(str(i * 10)),
                comision_compra=Decimal('50.00'),
                comision_venta=Decimal('50.00'),
                valor_compra_unit=Decimal('7250.00') + Decimal(str(i * 10)),
                valor_venta_unit=Decimal('7350.00') + Decimal(str(i * 10)),
                porcentaje_descuento=Decimal('0.00'),
                fecha=fecha
            )
    
    def test_api_historico_tasas_requiere_autenticacion(self):
        """Test que la API requiere autenticación"""
        self.client.logout()
        response = self.client.get(reverse('divisas:api_historico_tasas'))
        self.assertEqual(response.status_code, 302)
    
    def test_api_historico_tasas_sin_divisa_id(self):
        """Test de la API sin especificar divisa_id"""
        response = self.client.get(reverse('divisas:api_historico_tasas'))
        
        # Debería retornar error
        self.assertEqual(response.status_code, 404)
    
    def test_api_historico_tasas_con_divisa_valida(self):
        """Test de la API con divisa válida"""
        response = self.client.get(
            reverse('divisas:api_historico_tasas'),
            {
                'divisa_id': self.usd.id,
                'periodo': '30',
                'tipo': 'venta'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('divisa', data)
        self.assertEqual(data['divisa']['code'], 'USD')
        self.assertIn('datos', data)
        self.assertIsInstance(data['datos'], list)
    
    def test_api_historico_tasas_estructura_datos(self):
        """Test de la estructura de datos de la API"""
        response = self.client.get(
            reverse('divisas:api_historico_tasas'),
            {
                'divisa_id': self.usd.id,
                'periodo': '7',
                'tipo': 'venta'
            }
        )
        
        data = json.loads(response.content)
        
        if len(data['datos']) > 0:
            item = data['datos'][0]
            self.assertIn('fecha', item)
            self.assertIn('valor', item)
            self.assertIn('descuento', item)
    
    def test_api_historico_tasas_tipo_compra(self):
        """Test de la API con tipo de operación compra"""
        response = self.client.get(
            reverse('divisas:api_historico_tasas'),
            {
                'divisa_id': self.usd.id,
                'periodo': '7',
                'tipo': 'compra'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['tipo_operacion'], 'compra')
        
        # Verificar que usa valor_compra_unit
        if len(data['datos']) > 0:
            # Los valores deberían corresponder a valor_compra_unit
            self.assertGreater(data['datos'][0]['valor'], 0)
    
    def test_api_historico_tasas_tipo_venta(self):
        """Test de la API con tipo de operación venta"""
        response = self.client.get(
            reverse('divisas:api_historico_tasas'),
            {
                'divisa_id': self.usd.id,
                'periodo': '7',
                'tipo': 'venta'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['tipo_operacion'], 'venta')
    
    def test_api_historico_tasas_periodo_personalizado(self):
        """Test de la API con diferentes períodos"""
        periodos = ['7', '30', '90', '180', '365']
        
        for periodo in periodos:
            response = self.client.get(
                reverse('divisas:api_historico_tasas'),
                {
                    'divisa_id': self.usd.id,
                    'periodo': periodo,
                    'tipo': 'venta'
                }
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertIn('datos', data)
    
    def test_api_historico_tasas_ordena_por_fecha(self):
        """Test que la API ordena los datos por fecha"""
        response = self.client.get(
            reverse('divisas:api_historico_tasas'),
            {
                'divisa_id': self.usd.id,
                'periodo': '7',
                'tipo': 'venta'
            }
        )
        
        data = json.loads(response.content)
        
        if len(data['datos']) > 1:
            # Verificar que las fechas están ordenadas (más antigua primero)
            fechas = [item['fecha'] for item in data['datos']]
            self.assertEqual(fechas, sorted(fechas))


class TasaCambioModelTest(TestCase):
    """Tests para el modelo TasaCambio (histórico de tasas)"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.usd = Divisa.objects.create(
            code='USD',
            nombre='Dólar Americano',
            simbolo='$',
            is_active=True
        )
    
    def test_crear_tasa_cambio(self):
        """Test de creación de una tasa de cambio"""
        tasa = TasaCambio.objects.create(
            divisa=self.usd,
            precio_base=Decimal('7300.00'),
            comision_compra=Decimal('50.00'),
            comision_venta=Decimal('50.00')
        )
        
        self.assertIsNotNone(tasa.id)
        self.assertEqual(tasa.divisa, self.usd)
        self.assertEqual(tasa.precio_base, Decimal('7300.00'))
        self.assertIsNotNone(tasa.fecha)
    
    def test_tasa_cambio_fecha_automatica(self):
        """Test que la fecha se asigna automáticamente"""
        tasa = TasaCambio.objects.create(
            divisa=self.usd,
            precio_base=Decimal('7300.00'),
            comision_compra=Decimal('50.00'),
            comision_venta=Decimal('50.00')
        )
        
        self.assertIsNotNone(tasa.fecha)
        # La fecha debe ser reciente (último minuto)
        ahora = timezone.now()
        diferencia = ahora - tasa.fecha
        self.assertLess(diferencia.seconds, 60)


class CotizacionSegmentoEvolucionTest(TestCase):
    """Tests para la evolución de cotizaciones por segmento"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.usd = Divisa.objects.create(
            code='USD',
            nombre='Dólar Americano',
            simbolo='$',
            is_active=True
        )
        
        self.segmento_general = Segmento.objects.create(name='general')
        self.segmento_premium = Segmento.objects.create(name='premium')
    
    def test_crear_cotizaciones_diferentes_segmentos(self):
        """Test de creación de cotizaciones para diferentes segmentos"""
        hoy = timezone.now()
        
        cot_general = CotizacionSegmento.objects.create(
            divisa=self.usd,
            segmento=self.segmento_general,
            precio_base=Decimal('7300.00'),
            comision_compra=Decimal('50.00'),
            comision_venta=Decimal('50.00'),
            valor_compra_unit=Decimal('7250.00'),
            valor_venta_unit=Decimal('7350.00'),
            porcentaje_descuento=Decimal('0.00'),
            fecha=hoy
        )
        
        cot_premium = CotizacionSegmento.objects.create(
            divisa=self.usd,
            segmento=self.segmento_premium,
            precio_base=Decimal('7300.00'),
            comision_compra=Decimal('30.00'),
            comision_venta=Decimal('30.00'),
            valor_compra_unit=Decimal('7270.00'),
            valor_venta_unit=Decimal('7330.00'),
            porcentaje_descuento=Decimal('5.00'),
            fecha=hoy
        )
        
        self.assertNotEqual(cot_general.valor_venta_unit, cot_premium.valor_venta_unit)
        self.assertEqual(cot_premium.porcentaje_descuento, Decimal('5.00'))
    
    def test_cotizaciones_query_ultima_para(self):
        """Test del query helper ultima_para"""
        hoy = timezone.now()
        ayer = hoy - timedelta(days=1)
        
        # Crear cotización de ayer
        CotizacionSegmento.objects.create(
            divisa=self.usd,
            segmento=self.segmento_general,
            precio_base=Decimal('7200.00'),
            comision_compra=Decimal('50.00'),
            comision_venta=Decimal('50.00'),
            valor_compra_unit=Decimal('7150.00'),
            valor_venta_unit=Decimal('7250.00'),
            porcentaje_descuento=Decimal('0.00'),
            fecha=ayer
        )
        
        # Crear cotización de hoy
        cot_hoy = CotizacionSegmento.objects.create(
            divisa=self.usd,
            segmento=self.segmento_general,
            precio_base=Decimal('7300.00'),
            comision_compra=Decimal('50.00'),
            comision_venta=Decimal('50.00'),
            valor_compra_unit=Decimal('7250.00'),
            valor_venta_unit=Decimal('7350.00'),
            porcentaje_descuento=Decimal('0.00'),
            fecha=hoy
        )
        
        # Obtener última cotización
        ultima = CotizacionSegmento.objects.ultima_para(self.usd, self.segmento_general)
        
        self.assertEqual(ultima, cot_hoy)
    
    def test_evolucion_temporal_cotizaciones(self):
        """Test de la evolución temporal de cotizaciones"""
        # Crear serie temporal de 7 días
        valores_esperados = []
        hoy = timezone.now()
        
        for i in range(7):
            fecha = hoy - timedelta(days=i)
            valor = Decimal('7300.00') + Decimal(str(i * 10))
            
            CotizacionSegmento.objects.create(
                divisa=self.usd,
                segmento=self.segmento_general,
                precio_base=valor,
                comision_compra=Decimal('50.00'),
                comision_venta=Decimal('50.00'),
                valor_compra_unit=valor - Decimal('50.00'),
                valor_venta_unit=valor + Decimal('50.00'),
                porcentaje_descuento=Decimal('0.00'),
                fecha=fecha
            )
            
            valores_esperados.append(valor + Decimal('50.00'))
        
        # Obtener cotizaciones ordenadas por fecha
        cotizaciones = CotizacionSegmento.objects.filter(
            divisa=self.usd,
            segmento=self.segmento_general
        ).order_by('fecha')
        
        # Verificar que tenemos todas las cotizaciones
        self.assertEqual(cotizaciones.count(), 7)
        
        # Verificar la evolución (más antigua primero)
        valores_obtenidos = [cot.valor_venta_unit for cot in cotizaciones]
        valores_esperados.reverse()  # Ordenar de más antigua a más reciente
        self.assertEqual(valores_obtenidos, valores_esperados)
