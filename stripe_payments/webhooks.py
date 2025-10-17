"""
Webhook handler para recibir eventos de Stripe
"""
import stripe
import logging
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import StripeTransaction

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Endpoint para recibir webhooks de Stripe
    
    Este endpoint debe configurarse en el Dashboard de Stripe:
    https://dashboard.stripe.com/test/webhooks
    
    URL del webhook: https://tudominio.com/stripe/webhook/
    
    Eventos a suscribir:
    - payment_intent.succeeded
    - payment_intent.payment_failed
    - payment_intent.canceled
    - charge.succeeded
    - charge.failed
    - charge.refunded
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    # Verificar la firma del webhook
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Payload inválido
        logger.error(f"Webhook payload inválido: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Firma inválida
        logger.error(f"Webhook firma inválida: {e}")
        return HttpResponse(status=400)
    
    # Obtener el tipo de evento
    event_type = event['type']
    event_data = event['data']['object']
    
    logger.info(f"Webhook recibido: {event_type} - ID: {event.get('id')}")
    
    # Procesar el evento según su tipo
    try:
        if event_type == 'payment_intent.succeeded':
            handle_payment_intent_succeeded(event_data)
        
        elif event_type == 'payment_intent.payment_failed':
            handle_payment_intent_failed(event_data)
        
        elif event_type == 'payment_intent.canceled':
            handle_payment_intent_canceled(event_data)
        
        elif event_type == 'charge.succeeded':
            handle_charge_succeeded(event_data)
        
        elif event_type == 'charge.failed':
            handle_charge_failed(event_data)
        
        elif event_type == 'charge.refunded':
            handle_charge_refunded(event_data)
        
        else:
            logger.info(f"Evento no manejado: {event_type}")
    
    except Exception as e:
        logger.error(f"Error procesando webhook {event_type}: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'status': 'success'})


def handle_payment_intent_succeeded(payment_intent):
    """
    Maneja el evento payment_intent.succeeded
    Se dispara cuando un pago es exitoso
    """
    payment_intent_id = payment_intent['id']
    
    try:
        transaction = StripeTransaction.objects.get(payment_intent_id=payment_intent_id)
        
        # Actualizar el estado
        transaction.status = 'succeeded'
        
        # Actualizar información del cargo si está disponible
        if payment_intent.get('charges') and payment_intent['charges'].get('data'):
            charge = payment_intent['charges']['data'][0]
            transaction.charge_id = charge['id']
            
            # Información de la tarjeta
            if charge.get('payment_method_details', {}).get('card'):
                card = charge['payment_method_details']['card']
                transaction.card_brand = card.get('brand')
                transaction.card_last4 = card.get('last4')
        
        # Actualizar metadata
        if not transaction.metadata:
            transaction.metadata = {}
        transaction.metadata['webhook_updated'] = True
        transaction.metadata['last_webhook'] = 'payment_intent.succeeded'
        
        transaction.stripe_response = payment_intent
        transaction.save()
        
        logger.info(f"✓ Payment Intent {payment_intent_id} actualizado a succeeded")
        
    except StripeTransaction.DoesNotExist:
        logger.warning(f"Transaction no encontrada para Payment Intent: {payment_intent_id}")
    except Exception as e:
        logger.error(f"Error actualizando Payment Intent {payment_intent_id}: {e}", exc_info=True)


def handle_payment_intent_failed(payment_intent):
    """
    Maneja el evento payment_intent.payment_failed
    Se dispara cuando un pago falla
    """
    payment_intent_id = payment_intent['id']
    
    try:
        transaction = StripeTransaction.objects.get(payment_intent_id=payment_intent_id)
        
        # Actualizar el estado
        transaction.status = 'failed'
        
        # Guardar el mensaje de error
        if payment_intent.get('last_payment_error'):
            error = payment_intent['last_payment_error']
            transaction.error_message = error.get('message', 'Error desconocido')
        
        # Actualizar metadata
        if not transaction.metadata:
            transaction.metadata = {}
        transaction.metadata['webhook_updated'] = True
        transaction.metadata['last_webhook'] = 'payment_intent.payment_failed'
        
        transaction.stripe_response = payment_intent
        transaction.save()
        
        logger.info(f"✓ Payment Intent {payment_intent_id} actualizado a failed")
        
    except StripeTransaction.DoesNotExist:
        logger.warning(f"Transaction no encontrada para Payment Intent: {payment_intent_id}")
    except Exception as e:
        logger.error(f"Error actualizando Payment Intent {payment_intent_id}: {e}", exc_info=True)


def handle_payment_intent_canceled(payment_intent):
    """
    Maneja el evento payment_intent.canceled
    Se dispara cuando un pago es cancelado
    """
    payment_intent_id = payment_intent['id']
    
    try:
        transaction = StripeTransaction.objects.get(payment_intent_id=payment_intent_id)
        
        # Actualizar el estado
        transaction.status = 'canceled'
        
        # Actualizar metadata
        if not transaction.metadata:
            transaction.metadata = {}
        transaction.metadata['webhook_updated'] = True
        transaction.metadata['last_webhook'] = 'payment_intent.canceled'
        transaction.metadata['cancellation_reason'] = payment_intent.get('cancellation_reason')
        
        transaction.stripe_response = payment_intent
        transaction.save()
        
        logger.info(f"✓ Payment Intent {payment_intent_id} actualizado a canceled")
        
    except StripeTransaction.DoesNotExist:
        logger.warning(f"Transaction no encontrada para Payment Intent: {payment_intent_id}")
    except Exception as e:
        logger.error(f"Error actualizando Payment Intent {payment_intent_id}: {e}", exc_info=True)


def handle_charge_succeeded(charge):
    """
    Maneja el evento charge.succeeded
    Se dispara cuando un cargo es exitoso
    """
    charge_id = charge['id']
    payment_intent_id = charge.get('payment_intent')
    
    if not payment_intent_id:
        logger.warning(f"Charge {charge_id} sin Payment Intent asociado")
        return
    
    try:
        transaction = StripeTransaction.objects.get(payment_intent_id=payment_intent_id)
        
        # Actualizar información del cargo
        transaction.charge_id = charge_id
        transaction.status = 'succeeded'
        
        # Información de la tarjeta
        if charge.get('payment_method_details', {}).get('card'):
            card = charge['payment_method_details']['card']
            transaction.card_brand = card.get('brand')
            transaction.card_last4 = card.get('last4')
        
        # Actualizar metadata
        if not transaction.metadata:
            transaction.metadata = {}
        transaction.metadata['webhook_updated'] = True
        transaction.metadata['last_webhook'] = 'charge.succeeded'
        transaction.metadata['charge_id'] = charge_id
        
        transaction.save()
        
        logger.info(f"✓ Charge {charge_id} procesado para Payment Intent {payment_intent_id}")
        
    except StripeTransaction.DoesNotExist:
        logger.warning(f"Transaction no encontrada para Payment Intent: {payment_intent_id}")
    except Exception as e:
        logger.error(f"Error procesando Charge {charge_id}: {e}", exc_info=True)


def handle_charge_failed(charge):
    """
    Maneja el evento charge.failed
    Se dispara cuando un cargo falla
    """
    charge_id = charge['id']
    payment_intent_id = charge.get('payment_intent')
    
    if not payment_intent_id:
        logger.warning(f"Charge {charge_id} sin Payment Intent asociado")
        return
    
    try:
        transaction = StripeTransaction.objects.get(payment_intent_id=payment_intent_id)
        
        # Actualizar estado
        transaction.status = 'failed'
        transaction.charge_id = charge_id
        
        # Guardar mensaje de error
        if charge.get('failure_message'):
            transaction.error_message = charge['failure_message']
        
        # Actualizar metadata
        if not transaction.metadata:
            transaction.metadata = {}
        transaction.metadata['webhook_updated'] = True
        transaction.metadata['last_webhook'] = 'charge.failed'
        transaction.metadata['failure_code'] = charge.get('failure_code')
        
        transaction.save()
        
        logger.info(f"✓ Charge failed {charge_id} procesado para Payment Intent {payment_intent_id}")
        
    except StripeTransaction.DoesNotExist:
        logger.warning(f"Transaction no encontrada para Payment Intent: {payment_intent_id}")
    except Exception as e:
        logger.error(f"Error procesando Charge failed {charge_id}: {e}", exc_info=True)


def handle_charge_refunded(charge):
    """
    Maneja el evento charge.refunded
    Se dispara cuando un cargo es reembolsado
    """
    charge_id = charge['id']
    payment_intent_id = charge.get('payment_intent')
    
    if not payment_intent_id:
        logger.warning(f"Charge {charge_id} sin Payment Intent asociado")
        return
    
    try:
        transaction = StripeTransaction.objects.get(payment_intent_id=payment_intent_id)
        
        # Actualizar estado
        if charge.get('refunded'):
            transaction.status = 'refunded'
        
        # Actualizar metadata con información del reembolso
        if not transaction.metadata:
            transaction.metadata = {}
        transaction.metadata['webhook_updated'] = True
        transaction.metadata['last_webhook'] = 'charge.refunded'
        transaction.metadata['refunded'] = True
        transaction.metadata['amount_refunded'] = charge.get('amount_refunded')
        
        # Información de los reembolsos
        if charge.get('refunds', {}).get('data'):
            refunds = charge['refunds']['data']
            transaction.metadata['refunds'] = [
                {
                    'id': r['id'],
                    'amount': r['amount'],
                    'reason': r.get('reason'),
                    'status': r['status'],
                }
                for r in refunds
            ]
        
        transaction.save()
        
        logger.info(f"✓ Reembolso procesado para Charge {charge_id} (Payment Intent {payment_intent_id})")
        
    except StripeTransaction.DoesNotExist:
        logger.warning(f"Transaction no encontrada para Payment Intent: {payment_intent_id}")
    except Exception as e:
        logger.error(f"Error procesando reembolso de Charge {charge_id}: {e}", exc_info=True)
