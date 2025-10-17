"""
Tests para los modelos de stripe_payments
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from stripe_payments.models import StripeTransaction

User = get_user_model()


class StripeTransactionModelTest(TestCase):
    """Tests para el modelo StripeTransaction"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_stripe_transaction_success(self):
        """Test: Crear una transacción exitosa"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_test_123',
            amount=Decimal('100000.00'),
            currency='PYG',
            status='succeeded',
            transaction_type='compra',
            divisa_code='USD',
            monto_divisa=Decimal('15.00'),
            tasa_cambio=Decimal('6666.67')
        )
        
        self.assertEqual(transaction.cliente, self.user)
        self.assertEqual(transaction.payment_intent_id, 'pi_test_123')
        self.assertEqual(transaction.amount, Decimal('100000.00'))
        self.assertEqual(transaction.currency, 'PYG')
        self.assertEqual(transaction.status, 'succeeded')
        self.assertEqual(transaction.transaction_type, 'compra')
        self.assertIsNotNone(transaction.created_at)
        self.assertIsNotNone(transaction.updated_at)
    
    def test_payment_intent_id_unique(self):
        """Test: payment_intent_id debe ser único"""
        StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_unique_123',
            amount=Decimal('50000.00'),
            currency='PYG',
            status='pending'
        )
        
        # Intentar crear otra con el mismo payment_intent_id
        with self.assertRaises(Exception):  # IntegrityError
            StripeTransaction.objects.create(
                cliente=self.user,
                payment_intent_id='pi_unique_123',
                amount=Decimal('60000.00'),
                currency='PYG',
                status='pending'
            )
    
    def test_required_fields(self):
        """Test: Campos requeridos deben estar presentes"""
        # payment_intent_id puede no ser requerido en el modelo pero es crítico para el negocio
        # Verificamos que al menos cliente y amount son requeridos
        with self.assertRaises(Exception):
            StripeTransaction.objects.create(
                # Sin cliente ni amount
                payment_intent_id='pi_test'
            )
    
    def test_default_values(self):
        """Test: Valores por defecto"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_defaults_123',
            amount=Decimal('50000.00')
        )
        
        self.assertEqual(transaction.currency, 'PYG')
        self.assertEqual(transaction.status, 'pending')
        self.assertEqual(transaction.transaction_type, 'compra')
        self.assertIsNone(transaction.charge_id)
        # metadata puede ser None o {} dependiendo de la implementación
        self.assertIn(transaction.metadata, [None, {}])
    
    def test_is_successful_property(self):
        """Test: Propiedad is_successful"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_success_123',
            amount=Decimal('50000.00'),
            status='succeeded'
        )
        self.assertTrue(transaction.is_successful)
        
        transaction.status = 'failed'
        transaction.save()
        self.assertFalse(transaction.is_successful)
        
        transaction.status = 'pending'
        transaction.save()
        self.assertFalse(transaction.is_successful)
    
    def test_is_pending_property(self):
        """Test: Propiedad is_pending"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_pending_123',
            amount=Decimal('50000.00'),
            status='pending'
        )
        self.assertTrue(transaction.is_pending)
        
        transaction.status = 'processing'
        transaction.save()
        self.assertTrue(transaction.is_pending)
        
        transaction.status = 'requires_action'
        transaction.save()
        self.assertTrue(transaction.is_pending)
        
        transaction.status = 'succeeded'
        transaction.save()
        self.assertFalse(transaction.is_pending)
    
    def test_is_failed_property(self):
        """Test: Propiedad is_failed"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_failed_123',
            amount=Decimal('50000.00'),
            status='failed'
        )
        self.assertTrue(transaction.is_failed)
        
        transaction.status = 'canceled'
        transaction.save()
        self.assertTrue(transaction.is_failed)
        
        transaction.status = 'succeeded'
        transaction.save()
        self.assertFalse(transaction.is_failed)
    
    def test_get_amount_display(self):
        """Test: Método get_amount_display()"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_amount_123',
            amount=Decimal('100000.00'),
            currency='PYG'
        )
        
        display = transaction.get_amount_display()
        # Verificar que contiene el monto (puede usar . o , como separador)
        self.assertTrue('100' in display and '000' in display)
        # Verificar que contiene PYG o símbolo ₲
        self.assertTrue('PYG' in display or '₲' in display)
    
    def test_get_status_badge_class(self):
        """Test: Método get_status_badge_class()"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_badge_123',
            amount=Decimal('50000.00'),
            status='succeeded'
        )
        
        # Verificar que contiene la clase correcta (puede incluir prefijo badge-)
        badge_class = transaction.get_status_badge_class()
        self.assertIn('success', badge_class)
        
        transaction.status = 'failed'
        transaction.save()
        badge_class = transaction.get_status_badge_class()
        self.assertIn('danger', badge_class)
        
        transaction.status = 'canceled'
        transaction.save()
        badge_class = transaction.get_status_badge_class()
        self.assertIn('warning', badge_class)  # canceled usa badge-warning
        
        transaction.status = 'pending'
        transaction.save()
        badge_class = transaction.get_status_badge_class()
        self.assertIn('info', badge_class)  # pending usa badge-info
        
        transaction.status = 'processing'
        transaction.save()
        badge_class = transaction.get_status_badge_class()
        self.assertIn('primary', badge_class)  # processing usa badge-primary
    
    def test_str_method(self):
        """Test: Método __str__"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_str_123',
            amount=Decimal('50000.00'),
            status='succeeded'
        )
        
        str_representation = str(transaction)
        self.assertIn('pi_str_123', str_representation)
        # El __str__ puede usar el status o su display name
        self.assertTrue('succeeded' in str_representation.lower() or 'exitosa' in str_representation.lower())
    
    def test_metadata_field(self):
        """Test: Campo metadata (JSONField)"""
        metadata = {
            'cliente_id': '123',
            'divisa': 'USD',
            'tipo_operacion': 'compra'
        }
        
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_metadata_123',
            amount=Decimal('50000.00'),
            metadata=metadata
        )
        
        # Recuperar y verificar
        transaction_from_db = StripeTransaction.objects.get(payment_intent_id='pi_metadata_123')
        self.assertEqual(transaction_from_db.metadata, metadata)
        self.assertEqual(transaction_from_db.metadata['divisa'], 'USD')
    
    def test_stripe_response_field(self):
        """Test: Campo stripe_response (JSONField)"""
        stripe_response = {
            'id': 'pi_test_123',
            'object': 'payment_intent',
            'amount': 100000,
            'currency': 'pyg',
            'status': 'succeeded'
        }
        
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_response_123',
            amount=Decimal('100000.00'),
            stripe_response=stripe_response
        )
        
        # Recuperar y verificar
        transaction_from_db = StripeTransaction.objects.get(payment_intent_id='pi_response_123')
        self.assertEqual(transaction_from_db.stripe_response['id'], 'pi_test_123')
        self.assertEqual(transaction_from_db.stripe_response['status'], 'succeeded')
    
    def test_card_information_fields(self):
        """Test: Campos de información de tarjeta"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_card_123',
            amount=Decimal('50000.00'),
            card_last4='4242',
            card_brand='visa'
        )
        
        self.assertEqual(transaction.card_last4, '4242')
        self.assertEqual(transaction.card_brand, 'visa')
    
    def test_error_message_field(self):
        """Test: Campo error_message"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_error_123',
            amount=Decimal('50000.00'),
            status='failed',
            error_message='Tarjeta declinada - fondos insuficientes'
        )
        
        self.assertEqual(transaction.error_message, 'Tarjeta declinada - fondos insuficientes')
        self.assertTrue(transaction.is_failed)
    
    def test_transaction_type_choices(self):
        """Test: Tipos de transacción válidos"""
        # Compra
        transaction_compra = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_compra_123',
            amount=Decimal('50000.00'),
            transaction_type='compra'
        )
        self.assertEqual(transaction_compra.transaction_type, 'compra')
        
        # Venta
        transaction_venta = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_venta_123',
            amount=Decimal('50000.00'),
            transaction_type='venta'
        )
        self.assertEqual(transaction_venta.transaction_type, 'venta')
    
    def test_status_choices(self):
        """Test: Estados válidos"""
        valid_statuses = [
            'pending', 'processing', 'succeeded', 'failed', 
            'canceled', 'requires_action', 'refunded'
        ]
        
        for i, status in enumerate(valid_statuses):
            transaction = StripeTransaction.objects.create(
                cliente=self.user,
                payment_intent_id=f'pi_status_{i}',
                amount=Decimal('50000.00'),
                status=status
            )
            self.assertEqual(transaction.status, status)
    
    def test_divisa_code_and_exchange_rate(self):
        """Test: Campos de divisa y tasa de cambio"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_exchange_123',
            amount=Decimal('666667.00'),  # 100 USD * 6666.67
            currency='PYG',
            divisa_code='USD',
            monto_divisa=Decimal('100.00'),
            tasa_cambio=Decimal('6666.67')
        )
        
        self.assertEqual(transaction.divisa_code, 'USD')
        self.assertEqual(transaction.monto_divisa, Decimal('100.00'))
        self.assertEqual(transaction.tasa_cambio, Decimal('6666.67'))
        
        # Verificar cálculo
        calculated_amount = transaction.monto_divisa * transaction.tasa_cambio
        self.assertAlmostEqual(float(calculated_amount), float(transaction.amount), places=2)
    
    def test_client_ip_field(self):
        """Test: Campo client_ip"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_ip_123',
            amount=Decimal('50000.00'),
            client_ip='192.168.1.100'
        )
        
        self.assertEqual(transaction.client_ip, '192.168.1.100')
    
    def test_ordering(self):
        """Test: Ordenamiento por defecto (más recientes primero)"""
        # Crear varias transacciones
        t1 = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_order_1',
            amount=Decimal('50000.00')
        )
        
        t2 = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_order_2',
            amount=Decimal('60000.00')
        )
        
        t3 = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_order_3',
            amount=Decimal('70000.00')
        )
        
        # Obtener todas y verificar orden
        transactions = list(StripeTransaction.objects.all())
        
        # El más reciente (t3) debe estar primero
        self.assertEqual(transactions[0].id, t3.id)
        self.assertEqual(transactions[1].id, t2.id)
        self.assertEqual(transactions[2].id, t1.id)
