"""
Tests para los webhooks de stripe_payments
"""
from decimal import Decimal
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from stripe_payments.models import StripeTransaction
import json
import stripe

User = get_user_model()


class StripeWebhookTest(TestCase):
    """Tests para el webhook de Stripe"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.webhook_url = reverse('stripe_payments:webhook')
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_requires_post(self, mock_construct):
        """Test: Webhook solo acepta POST"""
        response = self.client.get(self.webhook_url)
        
        # Debe retornar 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_invalid_signature(self, mock_construct):
        """Test: Firma inválida"""
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            message='Invalid signature',
            sig_header='invalid'
        )
        
        response = self.client.post(
            self.webhook_url,
            data='{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )
        
        self.assertEqual(response.status_code, 400)
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_invalid_payload(self, mock_construct):
        """Test: Payload inválido"""
        mock_construct.side_effect = ValueError('Invalid payload')
        
        response = self.client.post(
            self.webhook_url,
            data='invalid json',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='sig_123'
        )
        
        self.assertEqual(response.status_code, 400)
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_payment_intent_succeeded(self, mock_construct):
        """Test: Evento payment_intent.succeeded"""
        # Crear transacción previa
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_webhook_success',
            amount=Decimal('100000.00'),
            status='pending'
        )
        
        # Mock del evento
        event = {
            'id': 'evt_test_123',
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_webhook_success',
                    'status': 'succeeded',
                    'charges': {
                        'data': [
                            {
                                'id': 'ch_123',
                                'payment_method_details': {
                                    'card': {
                                        'brand': 'visa',
                                        'last4': '4242'
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_construct.return_value = event
        
        # Enviar webhook
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que la transacción se actualizó
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'succeeded')
        self.assertEqual(transaction.charge_id, 'ch_123')
        self.assertEqual(transaction.card_brand, 'visa')
        self.assertEqual(transaction.card_last4, '4242')
        self.assertTrue(transaction.metadata.get('webhook_updated'))
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_payment_intent_failed(self, mock_construct):
        """Test: Evento payment_intent.payment_failed"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_webhook_failed',
            amount=Decimal('100000.00'),
            status='pending'
        )
        
        event = {
            'id': 'evt_failed_123',
            'type': 'payment_intent.payment_failed',
            'data': {
                'object': {
                    'id': 'pi_webhook_failed',
                    'status': 'failed',
                    'last_payment_error': {
                        'message': 'Tarjeta declinada'
                    }
                }
            }
        }
        mock_construct.return_value = event
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'failed')
        self.assertEqual(transaction.error_message, 'Tarjeta declinada')
        self.assertTrue(transaction.metadata.get('webhook_updated'))
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_payment_intent_canceled(self, mock_construct):
        """Test: Evento payment_intent.canceled"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_webhook_canceled',
            amount=Decimal('100000.00'),
            status='pending'
        )
        
        event = {
            'id': 'evt_canceled_123',
            'type': 'payment_intent.canceled',
            'data': {
                'object': {
                    'id': 'pi_webhook_canceled',
                    'status': 'canceled',
                    'cancellation_reason': 'abandoned'
                }
            }
        }
        mock_construct.return_value = event
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'canceled')
        self.assertEqual(transaction.metadata.get('cancellation_reason'), 'abandoned')
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_charge_succeeded(self, mock_construct):
        """Test: Evento charge.succeeded"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_charge_success',
            amount=Decimal('100000.00'),
            status='pending'
        )
        
        event = {
            'id': 'evt_charge_123',
            'type': 'charge.succeeded',
            'data': {
                'object': {
                    'id': 'ch_success_123',
                    'payment_intent': 'pi_charge_success',
                    'payment_method_details': {
                        'card': {
                            'brand': 'mastercard',
                            'last4': '5555'
                        }
                    }
                }
            }
        }
        mock_construct.return_value = event
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'succeeded')
        self.assertEqual(transaction.charge_id, 'ch_success_123')
        self.assertEqual(transaction.card_brand, 'mastercard')
        self.assertEqual(transaction.card_last4, '5555')
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_charge_failed(self, mock_construct):
        """Test: Evento charge.failed"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_charge_failed',
            amount=Decimal('100000.00'),
            status='pending'
        )
        
        event = {
            'id': 'evt_charge_failed',
            'type': 'charge.failed',
            'data': {
                'object': {
                    'id': 'ch_failed_123',
                    'payment_intent': 'pi_charge_failed',
                    'failure_message': 'Fondos insuficientes',
                    'failure_code': 'insufficient_funds'
                }
            }
        }
        mock_construct.return_value = event
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'failed')
        self.assertEqual(transaction.error_message, 'Fondos insuficientes')
        self.assertEqual(transaction.metadata.get('failure_code'), 'insufficient_funds')
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_charge_refunded(self, mock_construct):
        """Test: Evento charge.refunded"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_refund',
            amount=Decimal('100000.00'),
            status='succeeded'
        )
        
        event = {
            'id': 'evt_refund_123',
            'type': 'charge.refunded',
            'data': {
                'object': {
                    'id': 'ch_refund_123',
                    'payment_intent': 'pi_refund',
                    'refunded': True,
                    'amount_refunded': 100000,
                    'refunds': {
                        'data': [
                            {
                                'id': 're_123',
                                'amount': 100000,
                                'reason': 'requested_by_customer',
                                'status': 'succeeded'
                            }
                        ]
                    }
                }
            }
        }
        mock_construct.return_value = event
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'refunded')
        self.assertTrue(transaction.metadata.get('refunded'))
        self.assertEqual(transaction.metadata.get('amount_refunded'), 100000)
        self.assertIsNotNone(transaction.metadata.get('refunds'))
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_unknown_event_type(self, mock_construct):
        """Test: Tipo de evento desconocido (no manejado)"""
        event = {
            'id': 'evt_unknown_123',
            'type': 'unknown.event.type',
            'data': {
                'object': {}
            }
        }
        mock_construct.return_value = event
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        # Debe retornar 200 (success) aunque no procese el evento
        self.assertEqual(response.status_code, 200)
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_transaction_not_found(self, mock_construct):
        """Test: Webhook para transacción que no existe en BD"""
        event = {
            'id': 'evt_not_found',
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_not_in_database',
                    'status': 'succeeded'
                }
            }
        }
        mock_construct.return_value = event
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        # Debe retornar 200 pero loguear warning
        self.assertEqual(response.status_code, 200)
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_charge_without_payment_intent(self, mock_construct):
        """Test: Evento charge sin Payment Intent asociado"""
        event = {
            'id': 'evt_no_pi',
            'type': 'charge.succeeded',
            'data': {
                'object': {
                    'id': 'ch_no_pi',
                    # Sin payment_intent
                }
            }
        }
        mock_construct.return_value = event
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        # Debe retornar 200 aunque no procese
        self.assertEqual(response.status_code, 200)
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_response_format(self, mock_construct):
        """Test: Formato de respuesta del webhook"""
        event = {
            'id': 'evt_format',
            'type': 'unknown.event',
            'data': {'object': {}}
        }
        mock_construct.return_value = event
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_updates_metadata(self, mock_construct):
        """Test: Webhook actualiza metadata correctamente"""
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_metadata_update',
            amount=Decimal('100000.00'),
            status='pending',
            metadata={'initial': 'data'}
        )
        
        event = {
            'id': 'evt_metadata',
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_metadata_update',
                    'status': 'succeeded',
                    'charges': {'data': []}
                }
            }
        }
        mock_construct.return_value = event
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(event),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )
        
        transaction.refresh_from_db()
        
        # Debe mantener metadata inicial y agregar webhook info
        self.assertEqual(transaction.metadata['initial'], 'data')
        self.assertTrue(transaction.metadata['webhook_updated'])
        self.assertEqual(transaction.metadata['last_webhook'], 'payment_intent.succeeded')


class WebhookHandlerFunctionsTest(TestCase):
    """Tests para las funciones individuales de manejo de eventos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_handle_payment_intent_succeeded_updates_status(self):
        """Test: handle_payment_intent_succeeded actualiza el estado"""
        from stripe_payments.webhooks import handle_payment_intent_succeeded
        
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_handler_success',
            amount=Decimal('100000.00'),
            status='pending'
        )
        
        payment_intent = {
            'id': 'pi_handler_success',
            'status': 'succeeded',
            'charges': {'data': []}
        }
        
        handle_payment_intent_succeeded(payment_intent)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'succeeded')
    
    def test_handle_payment_intent_failed_saves_error(self):
        """Test: handle_payment_intent_failed guarda el error"""
        from stripe_payments.webhooks import handle_payment_intent_failed
        
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_handler_failed',
            amount=Decimal('100000.00'),
            status='pending'
        )
        
        payment_intent = {
            'id': 'pi_handler_failed',
            'status': 'failed',
            'last_payment_error': {
                'message': 'Card declined'
            }
        }
        
        handle_payment_intent_failed(payment_intent)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'failed')
        self.assertEqual(transaction.error_message, 'Card declined')
    
    def test_handle_charge_refunded_creates_refund_info(self):
        """Test: handle_charge_refunded crea información de reembolso"""
        from stripe_payments.webhooks import handle_charge_refunded
        
        transaction = StripeTransaction.objects.create(
            cliente=self.user,
            payment_intent_id='pi_refund_handler',
            amount=Decimal('100000.00'),
            status='succeeded'
        )
        
        charge = {
            'id': 'ch_refund',
            'payment_intent': 'pi_refund_handler',
            'refunded': True,
            'amount_refunded': 100000,
            'refunds': {
                'data': [
                    {
                        'id': 're_123',
                        'amount': 100000,
                        'reason': 'duplicate',
                        'status': 'succeeded'
                    }
                ]
            }
        }
        
        handle_charge_refunded(charge)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'refunded')
        refunds = transaction.metadata.get('refunds', [])
        self.assertEqual(len(refunds), 1)
        self.assertEqual(refunds[0]['id'], 're_123')
        self.assertEqual(refunds[0]['reason'], 'duplicate')
