"""
Tests para los servicios de stripe_payments
"""
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from stripe_payments.services import (
    StripePaymentProcessor,
    process_stripe_payment,
    _extract_card_data,
    get_transaction_history,
    get_transaction_by_payment_intent
)
from stripe_payments.models import StripeTransaction
import stripe
from stripe_payments.models import StripeTransaction

User = get_user_model()


class StripePaymentProcessorTest(TestCase):
    """Tests para la clase StripePaymentProcessor"""
    
    def setUp(self):
        """Configuración inicial"""
        self.processor = StripePaymentProcessor()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_success(self, mock_create):
        """Test: Crear Payment Intent exitosamente"""
        # Mock del Payment Intent de Stripe
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_test_success_123'
        mock_payment_intent.status = 'requires_payment_method'
        mock_create.return_value = mock_payment_intent
        
        # Ejecutar
        success, payment_intent, error = self.processor.create_payment_intent(
            amount=Decimal('100000.00'),
            currency='pyg',
            customer_email='test@example.com',
            description='Test payment'
        )
        
        # Verificar
        self.assertTrue(success)
        self.assertIsNotNone(payment_intent)
        self.assertIsNone(error)
        self.assertEqual(payment_intent.id, 'pi_test_success_123')
        
        # Verificar que se llamó a Stripe con los parámetros correctos
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        self.assertEqual(call_kwargs['amount'], 100000)
        self.assertEqual(call_kwargs['currency'], 'pyg')
        self.assertEqual(call_kwargs['receipt_email'], 'test@example.com')
    
    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_zero_amount(self, mock_create):
        """Test: Rechazar monto cero"""
        success, payment_intent, error = self.processor.create_payment_intent(
            amount=Decimal('0'),
            currency='pyg'
        )
        
        self.assertFalse(success)
        self.assertIsNone(payment_intent)
        self.assertIn('mayor a cero', error)
        mock_create.assert_not_called()
    
    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_negative_amount(self, mock_create):
        """Test: Rechazar monto negativo"""
        success, payment_intent, error = self.processor.create_payment_intent(
            amount=Decimal('-50000'),
            currency='pyg'
        )
        
        self.assertFalse(success)
        self.assertIsNone(payment_intent)
        self.assertIn('mayor a cero', error)
        mock_create.assert_not_called()
    
    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_card_error(self, mock_create):
        """Test: Manejar error de tarjeta"""
        mock_create.side_effect = stripe.CardError(
            message='Tarjeta declinada',
            param='card',
            code='card_declined'
        )
        
        success, payment_intent, error = self.processor.create_payment_intent(
            amount=Decimal('100000'),
            currency='pyg'
        )
        
        self.assertFalse(success)
        self.assertIsNone(payment_intent)
        self.assertIsNotNone(error)
    
    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_authentication_error(self, mock_create):
        """Test: Manejar error de autenticación"""
        mock_create.side_effect = stripe.AuthenticationError(
            message='Invalid API Key'
        )
        
        success, payment_intent, error = self.processor.create_payment_intent(
            amount=Decimal('100000'),
            currency='pyg'
        )
        
        self.assertFalse(success)
        self.assertIsNone(payment_intent)
        self.assertIn('autenticación', error.lower())
    
    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_with_metadata(self, mock_create):
        """Test: Crear Payment Intent con metadata"""
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_metadata_123'
        mock_create.return_value = mock_payment_intent
        
        metadata = {
            'cliente_id': '123',
            'divisa': 'USD'
        }
        
        success, payment_intent, error = self.processor.create_payment_intent(
            amount=Decimal('100000'),
            currency='pyg',
            metadata=metadata
        )
        
        self.assertTrue(success)
        call_kwargs = mock_create.call_args[1]
        self.assertEqual(call_kwargs['metadata'], metadata)
    
    @patch('stripe.PaymentIntent.confirm')
    @patch('stripe.PaymentMethod.create')
    @patch('stripe.Token.create')
    def test_confirm_payment_with_card_success_production(self, mock_token, mock_pm, mock_confirm):
        """Test: Confirmar pago con tarjeta en modo producción"""
        # Mock del token
        mock_token_obj = Mock()
        mock_token_obj.id = 'tok_test_123'
        mock_token.return_value = mock_token_obj
        
        # Mock del Payment Method
        mock_pm_obj = Mock()
        mock_pm_obj.id = 'pm_test_123'
        mock_pm.return_value = mock_pm_obj
        
        # Mock del Payment Intent confirmado
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_confirmed_123'
        mock_payment_intent.status = 'succeeded'
        mock_confirm.return_value = mock_payment_intent
        
        # Ejecutar (tarjeta que NO es de prueba)
        success, payment_intent, error = self.processor.confirm_payment_with_card(
            payment_intent_id='pi_test_123',
            card_number='5555555555554444',  # Mastercard de prueba pero no 4242
            exp_month=12,
            exp_year=2025,
            cvc='123',
            cardholder_name='Test User'
        )
        
        # Verificar
        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(payment_intent.status, 'succeeded')
        
        # Verificar que se creó el token
        mock_token.assert_called_once()
        # Verificar que se creó el Payment Method
        mock_pm.assert_called_once()
        # Verificar que se confirmó el Payment Intent
        mock_confirm.assert_called_once_with(
            'pi_test_123',
            payment_method='pm_test_123'
        )
    
    @patch('stripe.PaymentIntent.confirm')
    def test_confirm_payment_with_card_test_mode(self, mock_confirm):
        """Test: Confirmar pago con tarjeta de prueba (4242...)"""
        # Mock del Payment Intent confirmado
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_test_mode_123'
        mock_payment_intent.status = 'succeeded'
        mock_confirm.return_value = mock_payment_intent
        
        # Ejecutar con tarjeta de prueba 4242
        success, payment_intent, error = self.processor.confirm_payment_with_card(
            payment_intent_id='pi_test_123',
            card_number='4242424242424242',
            exp_month=12,
            exp_year=2025,
            cvc='123',
            cardholder_name='Test User'
        )
        
        # Verificar
        self.assertTrue(success)
        self.assertIsNone(error)
        
        # Verificar que se usó el Payment Method de prueba
        mock_confirm.assert_called_once_with(
            'pi_test_123',
            payment_method='pm_card_visa'
        )
    
    @patch('stripe.PaymentIntent.confirm')
    def test_confirm_payment_requires_action(self, mock_confirm):
        """Test: Pago que requiere acción adicional (3D Secure)"""
        mock_payment_intent = Mock()
        mock_payment_intent.status = 'requires_action'
        mock_confirm.return_value = mock_payment_intent
        
        success, payment_intent, error = self.processor.confirm_payment_with_card(
            payment_intent_id='pi_3ds_123',
            card_number='4242424242424242',
            exp_month=12,
            exp_year=2025,
            cvc='123'
        )
        
        self.assertFalse(success)
        self.assertIsNotNone(payment_intent)
        self.assertIn('autenticación adicional', error)
    
    @patch('stripe.PaymentIntent.confirm')
    def test_confirm_payment_card_error(self, mock_confirm):
        """Test: Error de tarjeta al confirmar"""
        mock_confirm.side_effect = stripe.CardError(
            message='Tarjeta declinada',
            param='card',
            code='card_declined'
        )
        
        success, payment_intent, error = self.processor.confirm_payment_with_card(
            payment_intent_id='pi_declined_123',
            card_number='4242424242424242',
            exp_month=12,
            exp_year=2025,
            cvc='123'
        )
        
        self.assertFalse(success)
        self.assertIsNone(payment_intent)
        self.assertIsNotNone(error)
    
    @patch('stripe.PaymentIntent.retrieve')
    def test_retrieve_payment_intent_success(self, mock_retrieve):
        """Test: Recuperar Payment Intent"""
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_retrieve_123'
        mock_retrieve.return_value = mock_payment_intent
        
        payment_intent = self.processor.retrieve_payment_intent('pi_retrieve_123')
        
        self.assertIsNotNone(payment_intent)
        self.assertEqual(payment_intent.id, 'pi_retrieve_123')
        mock_retrieve.assert_called_once_with('pi_retrieve_123')
    
    @patch('stripe.PaymentIntent.retrieve')
    def test_retrieve_payment_intent_error(self, mock_retrieve):
        """Test: Error al recuperar Payment Intent"""
        mock_retrieve.side_effect = Exception('Not found')
        
        payment_intent = self.processor.retrieve_payment_intent('pi_not_found')
        
        self.assertIsNone(payment_intent)
    
    @patch('stripe.PaymentIntent.cancel')
    def test_cancel_payment_intent_success(self, mock_cancel):
        """Test: Cancelar Payment Intent exitosamente"""
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_cancel_123'
        mock_payment_intent.status = 'canceled'
        mock_cancel.return_value = mock_payment_intent
        
        success, error = self.processor.cancel_payment_intent('pi_cancel_123')
        
        self.assertTrue(success)
        self.assertIsNone(error)
        mock_cancel.assert_called_once_with('pi_cancel_123')
    
    @patch('stripe.PaymentIntent.cancel')
    def test_cancel_payment_intent_error(self, mock_cancel):
        """Test: Error al cancelar Payment Intent"""
        mock_cancel.side_effect = Exception('Cannot cancel')
        
        success, error = self.processor.cancel_payment_intent('pi_cannot_cancel')
        
        self.assertFalse(success)
        self.assertIsNotNone(error)


class ProcessStripePaymentTest(TestCase):
    """Tests para la función process_stripe_payment"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('stripe_payments.services.StripePaymentProcessor')
    def test_process_stripe_payment_success(self, mock_processor_class):
        """Test: Procesar pago exitosamente"""
        # Mock del processor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        # Mock create_payment_intent
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_process_123'
        mock_payment_intent.to_dict.return_value = {'id': 'pi_process_123'}
        mock_processor.create_payment_intent.return_value = (True, mock_payment_intent, None)
        
        # Mock confirm_payment_with_card
        mock_confirmed = Mock()
        mock_confirmed.id = 'pi_process_123'
        mock_confirmed.to_dict.return_value = {'id': 'pi_process_123', 'status': 'succeeded'}
        mock_confirmed.charges = Mock()
        mock_confirmed.charges.data = [
            Mock(
                id='ch_123',
                payment_method_details=Mock(
                    card=Mock(last4='4242', brand='visa')
                )
            )
        ]
        mock_processor.confirm_payment_with_card.return_value = (True, mock_confirmed, None)
        
        # Datos del medio de pago
        medio_pago_data = {
            'id': 1,
            'datos_campos': {
                'Número de Tarjeta': '4242424242424242',
                'Mes de Vencimiento': 12,
                'Año de Vencimiento': 2025,
                'Código de Seguridad': '123',
                'Nombre del Titular': 'Test User'
            }
        }
        
        # Datos de la operación
        operacion_data = {
            'monto_guaranies': '100000.00',
            'divisa': 'USD',
            'monto_divisa': '15.00',
            'tasa_cambio': '6666.67',
            'tipo': 'compra'
        }
        
        # Ejecutar
        success, transaction, error = process_stripe_payment(
            cliente=self.user,
            medio_pago_data=medio_pago_data,
            operacion_data=operacion_data,
            client_ip='127.0.0.1'
        )
        
        # Verificar
        self.assertTrue(success)
        self.assertIsNotNone(transaction)
        self.assertIsNone(error)
        self.assertEqual(transaction.payment_intent_id, 'pi_process_123')
        self.assertEqual(transaction.status, 'succeeded')
        self.assertEqual(transaction.card_last4, '4242')
        self.assertEqual(transaction.card_brand, 'visa')
    
    @patch('stripe_payments.services.StripePaymentProcessor')
    def test_process_stripe_payment_create_intent_fails(self, mock_processor_class):
        """Test: Fallo al crear Payment Intent"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        # Mock create_payment_intent con fallo
        mock_processor.create_payment_intent.return_value = (False, None, 'Error de API')
        
        medio_pago_data = {'id': 1, 'datos_campos': {}}
        operacion_data = {'monto_guaranies': '100000.00'}
        
        success, transaction, error = process_stripe_payment(
            cliente=self.user,
            medio_pago_data=medio_pago_data,
            operacion_data=operacion_data
        )
        
        self.assertFalse(success)
        self.assertIsNone(transaction)
        self.assertEqual(error, 'Error de API')
    
    @patch('stripe_payments.services.StripePaymentProcessor')
    def test_process_stripe_payment_no_card_data(self, mock_processor_class):
        """Test: Sin datos de tarjeta"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        # Mock create_payment_intent exitoso
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_no_card_123'
        mock_processor.create_payment_intent.return_value = (True, mock_payment_intent, None)
        
        # Mock cancel (debe ser llamado)
        mock_processor.cancel_payment_intent.return_value = (True, None)
        
        # Sin datos de tarjeta
        medio_pago_data = {'id': 1, 'datos_campos': {}}
        operacion_data = {'monto_guaranies': '100000.00'}
        
        success, transaction, error = process_stripe_payment(
            cliente=self.user,
            medio_pago_data=medio_pago_data,
            operacion_data=operacion_data
        )
        
        self.assertFalse(success)
        self.assertIsNone(transaction)
        self.assertIn('datos de tarjeta', error.lower())
        
        # Verificar que se canceló el Payment Intent
        mock_processor.cancel_payment_intent.assert_called_once_with('pi_no_card_123')
    
    @patch('stripe_payments.services.StripePaymentProcessor')
    def test_process_stripe_payment_confirm_fails(self, mock_processor_class):
        """Test: Fallo al confirmar el pago"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        # Mock create_payment_intent exitoso
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_confirm_fail_123'
        mock_payment_intent.to_dict.return_value = {'id': 'pi_confirm_fail_123'}
        mock_processor.create_payment_intent.return_value = (True, mock_payment_intent, None)
        
        # Mock confirm_payment_with_card con fallo - NO devuelve intent
        mock_processor.confirm_payment_with_card.return_value = (False, None, 'Tarjeta declinada')
        
        medio_pago_data = {
            'id': 1,
            'datos_campos': {
                'Número de Tarjeta': '4000000000000002',  # Tarjeta que siempre falla
                'Mes de Vencimiento': 12,
                'Año de Vencimiento': 2025,
                'Código de Seguridad': '123',
                'Nombre del Titular': 'Test User'
            }
        }
        operacion_data = {'monto_guaranies': '100000.00', 'divisa': 'USD'}
        
        success, transaction, error = process_stripe_payment(
            cliente=self.user,
            medio_pago_data=medio_pago_data,
            operacion_data=operacion_data
        )
        
        # Cuando confirm falla completamente, puede no crear transacción
        self.assertFalse(success)
        self.assertEqual(error, 'Tarjeta declinada')


class ExtractCardDataTest(TestCase):
    """Tests para la función _extract_card_data"""
    
    def test_extract_card_data_from_dict_complete(self):
        """Test: Extraer datos completos desde diccionario"""
        medio_pago_data = {
            'datos_campos': {
                'Número de Tarjeta': '4242424242424242',
                'Mes de Vencimiento': 12,
                'Año de Vencimiento': 2025,
                'Código de Seguridad': '123',
                'Nombre del Titular': 'Test User'
            }
        }
        
        card_data = _extract_card_data(medio_pago_data)
        
        self.assertIsNotNone(card_data)
        self.assertEqual(card_data['card_number'], '4242424242424242')
        self.assertEqual(card_data['exp_month'], 12)
        self.assertEqual(card_data['exp_year'], 2025)
        self.assertEqual(card_data['cvc'], '123')
        self.assertEqual(card_data['cardholder_name'], 'Test User')
    
    def test_extract_card_data_incomplete(self):
        """Test: Datos incompletos deben retornar None"""
        medio_pago_data = {
            'datos_campos': {
                'Número de Tarjeta': '4242424242424242',
                'Mes de Vencimiento': 12
                # Faltan: año, CVC
            }
        }
        
        card_data = _extract_card_data(medio_pago_data)
        
        self.assertIsNone(card_data)
    
    def test_extract_card_data_normalize_field_names(self):
        """Test: Normalización de nombres de campos (tildes, mayúsculas)"""
        medio_pago_data = {
            'datos_campos': {
                'numero de tarjeta': '4242 4242 4242 4242',  # Con espacios
                'mes de vencimiento': '12',  # String
                'año de vencimiento': '25',  # Año de 2 dígitos
                'codigo de seguridad': '123',
                'titular': 'Test User'
            }
        }
        
        card_data = _extract_card_data(medio_pago_data)
        
        self.assertIsNotNone(card_data)
        self.assertEqual(card_data['card_number'], '4242424242424242')  # Sin espacios
        self.assertEqual(card_data['exp_month'], 12)
        self.assertEqual(card_data['exp_year'], 2025)  # Convertido a 4 dígitos
    
    def test_extract_card_data_cvc_variations(self):
        """Test: Detectar variaciones de CVC/CVV/CBU"""
        variations = ['CVC', 'CVV', 'CBU', 'CVU', 'Código de Seguridad']
        
        for variation in variations:
            medio_pago_data = {
                'datos_campos': {
                    'Número de Tarjeta': '4242424242424242',
                    'Mes de Vencimiento': 12,
                    'Año de Vencimiento': 2025,
                    variation: '123',
                    'Titular': 'Test'
                }
            }
            
            card_data = _extract_card_data(medio_pago_data)
            self.assertIsNotNone(card_data, f"Failed for variation: {variation}")
            self.assertEqual(card_data['cvc'], '123')
    
    def test_extract_card_data_year_conversion(self):
        """Test: Conversión de año de 2 dígitos a 4 dígitos"""
        medio_pago_data = {
            'datos_campos': {
                'Número de Tarjeta': '4242424242424242',
                'Mes de Vencimiento': 12,
                'Año de Vencimiento': 25,  # 2 dígitos
                'CVC': '123',
                'Titular': 'Test'
            }
        }
        
        card_data = _extract_card_data(medio_pago_data)
        
        self.assertEqual(card_data['exp_year'], 2025)
    
    def test_extract_card_data_removes_spaces_and_dashes(self):
        """Test: Eliminar espacios y guiones del número de tarjeta"""
        medio_pago_data = {
            'datos_campos': {
                'Número de Tarjeta': '4242-4242-4242-4242',
                'Mes de Vencimiento': 12,
                'Año de Vencimiento': 2025,
                'CVC': '123'
            }
        }
        
        card_data = _extract_card_data(medio_pago_data)
        
        self.assertEqual(card_data['card_number'], '4242424242424242')


class TransactionHistoryTest(TestCase):
    """Tests para funciones de historial de transacciones"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear transacciones de prueba
        for i in range(5):
            StripeTransaction.objects.create(
                cliente=self.user,
                payment_intent_id=f'pi_history_{i}',
                amount=Decimal('50000.00'),
                status='succeeded'
            )
    
    def test_get_transaction_history_all(self):
        """Test: Obtener todo el historial"""
        transactions = get_transaction_history(self.user)
        
        self.assertEqual(len(transactions), 5)
    
    def test_get_transaction_history_with_limit(self):
        """Test: Obtener historial con límite"""
        transactions = get_transaction_history(self.user, limit=3)
        
        self.assertEqual(len(transactions), 3)
    
    def test_get_transaction_history_ordered_by_date(self):
        """Test: Historial ordenado por fecha descendente"""
        transactions = get_transaction_history(self.user)
        
        # Verificar que están ordenadas de más reciente a más antigua
        for i in range(len(transactions) - 1):
            self.assertGreaterEqual(
                transactions[i].created_at,
                transactions[i + 1].created_at
            )
    
    def test_get_transaction_by_payment_intent_exists(self):
        """Test: Obtener transacción por Payment Intent ID"""
        transaction = get_transaction_by_payment_intent('pi_history_0')
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.payment_intent_id, 'pi_history_0')
    
    def test_get_transaction_by_payment_intent_not_exists(self):
        """Test: Transacción no encontrada"""
        transaction = get_transaction_by_payment_intent('pi_not_exists')
        
        self.assertIsNone(transaction)
