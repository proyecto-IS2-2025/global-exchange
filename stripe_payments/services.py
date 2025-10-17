"""
Servicios de procesamiento de pagos con Stripe
"""
import stripe
import logging
from django.conf import settings
from decimal import Decimal
from typing import Dict, Optional, Tuple
from .models import StripeTransaction

logger = logging.getLogger(__name__)

# Configurar la API key de Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentProcessor:
    """
    Procesador de pagos con Stripe usando Payment Intents
    """
    
    def __init__(self):
        self.api_key = settings.STRIPE_SECRET_KEY
        stripe.api_key = self.api_key
    
    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str = 'pyg',
        customer_email: str = None,
        metadata: dict = None,
        description: str = None
    ) -> Tuple[bool, Optional[stripe.PaymentIntent], Optional[str]]:
        """
        Crea un Payment Intent en Stripe
        
        Args:
            amount: Monto en la unidad más pequeña de la moneda (guaraníes)
            currency: Código de moneda (pyg, usd, etc.)
            customer_email: Email del cliente
            metadata: Metadatos adicionales
            description: Descripción del pago
            
        Returns:
            Tuple con (éxito, payment_intent, mensaje_error)
        """
        try:
            # Convertir el monto a entero (Stripe requiere centavos/unidad más pequeña)
            # Para guaraníes, ya está en la unidad más pequeña
            amount_cents = int(amount)
            
            if amount_cents <= 0:
                return False, None, "El monto debe ser mayor a cero"
            
            # Preparar parámetros
            params = {
                'amount': amount_cents,
                'currency': currency.lower(),
                'automatic_payment_methods': {
                    'enabled': True,
                    'allow_redirects': 'never',  # No permitir métodos con redirección
                },
            }
            
            if description:
                params['description'] = description
            
            if customer_email:
                params['receipt_email'] = customer_email
            
            if metadata:
                params['metadata'] = metadata
            
            # Crear el Payment Intent
            logger.info(f"Creando Payment Intent: {params}")
            payment_intent = stripe.PaymentIntent.create(**params)
            
            logger.info(f"Payment Intent creado exitosamente: {payment_intent.id}")
            return True, payment_intent, None
            
        except stripe.error.CardError as e:
            # Errores de tarjeta (tarjeta declinada, fondos insuficientes, etc.)
            error_msg = e.user_message or str(e)
            logger.error(f"Error de tarjeta en Stripe: {error_msg}")
            return False, None, error_msg
            
        except stripe.error.InvalidRequestError as e:
            # Parámetros inválidos
            error_msg = f"Parámetros inválidos: {str(e)}"
            logger.error(f"Error de request en Stripe: {error_msg}")
            return False, None, error_msg
            
        except stripe.error.AuthenticationError as e:
            # Error de autenticación con Stripe
            error_msg = "Error de autenticación con Stripe"
            logger.error(f"Error de autenticación en Stripe: {str(e)}")
            return False, None, error_msg
            
        except stripe.error.APIConnectionError as e:
            # Error de conexión con la API
            error_msg = "Error de conexión con Stripe. Intente nuevamente."
            logger.error(f"Error de conexión con Stripe: {str(e)}")
            return False, None, error_msg
            
        except stripe.error.StripeError as e:
            # Otros errores de Stripe
            error_msg = f"Error en Stripe: {str(e)}"
            logger.error(f"Error general de Stripe: {error_msg}")
            return False, None, error_msg
            
        except Exception as e:
            # Errores inesperados
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(f"Error inesperado en create_payment_intent: {error_msg}", exc_info=True)
            return False, None, error_msg
    
    def confirm_payment_with_card(
        self,
        payment_intent_id: str,
        card_number: str,
        exp_month: int,
        exp_year: int,
        cvc: str,
        cardholder_name: str = None
    ) -> Tuple[bool, Optional[stripe.PaymentIntent], Optional[str]]:
        """
        Confirma un Payment Intent con los datos de una tarjeta
        
        Args:
            payment_intent_id: ID del Payment Intent
            card_number: Número de tarjeta
            exp_month: Mes de vencimiento
            exp_year: Año de vencimiento
            cvc: Código de seguridad
            cardholder_name: Nombre en la tarjeta
            
        Returns:
            Tuple con (éxito, payment_intent, mensaje_error)
        """
        try:
            # Determinar si estamos en modo test (número de tarjeta empieza con 4242)
            is_test_mode = card_number.replace(' ', '').startswith('4242')
            
            if is_test_mode:
                # En modo test, usar token de prueba de Stripe directamente
                logger.info("🧪 Modo TEST detectado - usando Payment Method de prueba de Stripe")
                # Usar pm_card_visa (Payment Method de prueba proporcionado por Stripe)
                payment_method_id = 'pm_card_visa'
                logger.info(f"✓ Usando Payment Method de prueba: {payment_method_id}")
            else:
                # En modo producción, crear token y payment method normalmente
                logger.info("Creando token de tarjeta...")
                token = stripe.Token.create(
                    card={
                        'number': card_number,
                        'exp_month': exp_month,
                        'exp_year': exp_year,
                        'cvc': cvc,
                        'name': cardholder_name,
                    }
                )
                logger.info(f"✓ Token creado: {token.id}")
                
                # Crear el Payment Method usando el token
                logger.info("Creando Payment Method desde token...")
                payment_method = stripe.PaymentMethod.create(
                    type='card',
                    card={
                        'token': token.id,
                    },
                    billing_details={
                        'name': cardholder_name,
                    } if cardholder_name else None
                )
                payment_method_id = payment_method.id
                logger.info(f"✓ Payment Method creado: {payment_method_id}")
            
            # Confirmar el Payment Intent con el Payment Method
            logger.info(f"Confirmando Payment Intent {payment_intent_id}...")
            payment_intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                payment_method=payment_method_id
            )
            
            logger.info(f"Payment Intent {payment_intent_id} confirmado con estado: {payment_intent.status}")
            
            # Verificar el estado
            if payment_intent.status == 'succeeded':
                return True, payment_intent, None
            elif payment_intent.status == 'requires_action':
                return False, payment_intent, "La transacción requiere autenticación adicional (3D Secure)"
            else:
                return False, payment_intent, f"El pago no pudo completarse. Estado: {payment_intent.status}"
                
        except stripe.error.CardError as e:
            error_msg = e.user_message or str(e)
            logger.error(f"Error de tarjeta al confirmar: {error_msg}")
            return False, None, error_msg
            
        except stripe.error.StripeError as e:
            error_msg = f"Error en Stripe: {str(e)}"
            logger.error(f"Error de Stripe al confirmar: {error_msg}")
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(f"Error inesperado en confirm_payment_with_card: {error_msg}", exc_info=True)
            return False, None, error_msg
    
    def retrieve_payment_intent(self, payment_intent_id: str) -> Optional[stripe.PaymentIntent]:
        """
        Recupera un Payment Intent de Stripe
        
        Args:
            payment_intent_id: ID del Payment Intent
            
        Returns:
            Payment Intent o None si hay error
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return payment_intent
        except Exception as e:
            logger.error(f"Error al recuperar Payment Intent {payment_intent_id}: {str(e)}")
            return None
    
    def cancel_payment_intent(self, payment_intent_id: str) -> Tuple[bool, Optional[str]]:
        """
        Cancela un Payment Intent
        
        Args:
            payment_intent_id: ID del Payment Intent
            
        Returns:
            Tuple con (éxito, mensaje_error)
        """
        try:
            payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)
            logger.info(f"Payment Intent {payment_intent_id} cancelado")
            return True, None
        except Exception as e:
            error_msg = f"Error al cancelar: {str(e)}"
            logger.error(f"Error al cancelar Payment Intent {payment_intent_id}: {error_msg}")
            return False, error_msg


def process_stripe_payment(
    cliente,
    medio_pago_data,  # Puede ser Dict o ClienteMedioDePago
    operacion_data: Dict,
    client_ip: str = None
) -> Tuple[bool, Optional[StripeTransaction], Optional[str]]:
    """
    Procesa un pago completo con Stripe y registra la transacción
    
    Args:
        cliente: Usuario/Cliente que realiza el pago
        medio_pago_data: ClienteMedioDePago o diccionario con los datos del medio de pago
        operacion_data: Diccionario con datos de la operación (monto, divisa, tasa, etc.)
        client_ip: IP del cliente (opcional)
        
    Returns:
        Tuple con (éxito, transacción, mensaje_error)
    """
    from clientes.models import ClienteMedioDePago
    
    processor = StripePaymentProcessor()
    
    try:
        logger.info(f"=== INICIANDO PROCESO DE PAGO CON STRIPE ===")
        logger.info(f"Cliente: {cliente.email}")
        logger.info(f"Tipo de medio_pago_data: {type(medio_pago_data)}")
        
        # Extraer datos de la operación
        monto_guaranies = Decimal(str(operacion_data.get('monto_guaranies', 0)))
        divisa_code = operacion_data.get('divisa', '')
        monto_divisa = operacion_data.get('monto_divisa')
        tasa_cambio = operacion_data.get('tasa_cambio')
        tipo_operacion = operacion_data.get('tipo', 'compra')
        
        logger.info(f"Monto: {monto_guaranies} PYG, Divisa: {divisa_code}, Tipo: {tipo_operacion}")
        
        # Preparar descripción
        description = f"Operación de {tipo_operacion} - {divisa_code}"
        if monto_divisa:
            description += f" - {monto_divisa} {divisa_code}"
        
        # Obtener ID del medio de pago
        medio_pago_id = None
        if isinstance(medio_pago_data, ClienteMedioDePago):
            medio_pago_id = medio_pago_data.id
        elif isinstance(medio_pago_data, dict):
            medio_pago_id = medio_pago_data.get('id')
        
        # Preparar metadata
        metadata = {
            'cliente_id': str(cliente.id),
            'cliente_email': cliente.email,
            'tipo_operacion': tipo_operacion,
            'divisa': divisa_code,
        }
        
        if medio_pago_id:
            metadata['medio_pago_id'] = str(medio_pago_id)
        
        # Crear Payment Intent
        logger.info(f"Creando Payment Intent en Stripe...")
        success, payment_intent, error = processor.create_payment_intent(
            amount=monto_guaranies,
            currency='pyg',
            customer_email=cliente.email,
            metadata=metadata,
            description=description
        )
        
        if not success:
            logger.error(f"Error al crear Payment Intent: {error}")
            return False, None, error
        
        logger.info(f"✓ Payment Intent creado: {payment_intent.id}")
        
        # Extraer datos de la tarjeta del medio de pago
        logger.info(f"Extrayendo datos de tarjeta...")
        card_data = _extract_card_data(medio_pago_data)
        
        if not card_data:
            logger.error("No se encontraron datos de tarjeta válidos")
            # Cancelar el Payment Intent si no hay datos de tarjeta
            processor.cancel_payment_intent(payment_intent.id)
            return False, None, "No se encontraron datos de tarjeta válidos. Verifique que todos los campos estén completos."
        
        logger.info(f"✓ Datos de tarjeta extraídos correctamente")
        
        # Confirmar el pago con la tarjeta
        logger.info(f"Confirmando pago con Stripe...")
        success, confirmed_intent, error = processor.confirm_payment_with_card(
            payment_intent_id=payment_intent.id,
            **card_data
        )
        
        # Crear registro de transacción
        logger.info(f"Registrando transacción en BD...")
        transaction = StripeTransaction.objects.create(
            cliente=cliente,
            transaction_type=tipo_operacion,
            payment_intent_id=payment_intent.id,
            amount=monto_guaranies,
            currency='PYG',
            divisa_code=divisa_code,
            monto_divisa=Decimal(str(monto_divisa)) if monto_divisa else None,
            tasa_cambio=Decimal(str(tasa_cambio)) if tasa_cambio else None,
            status='succeeded' if success else 'failed',
            stripe_response=confirmed_intent.to_dict() if confirmed_intent else payment_intent.to_dict(),
            error_message=error,
            cliente_medio_pago_id=medio_pago_id,
            metadata=metadata,
            client_ip=client_ip
        )
        
        # Si el pago fue confirmado, extraer información de la tarjeta
        if confirmed_intent and hasattr(confirmed_intent, 'charges'):
            charges = confirmed_intent.charges.data
            if charges:
                charge = charges[0]
                transaction.charge_id = charge.id
                if hasattr(charge, 'payment_method_details'):
                    card_details = charge.payment_method_details.card
                    transaction.card_last4 = card_details.last4
                    transaction.card_brand = card_details.brand
                transaction.save()
        
        if success:
            logger.info(f"✅ PAGO PROCESADO EXITOSAMENTE")
            logger.info(f"Payment Intent: {transaction.payment_intent_id}")
            logger.info(f"Transacción ID: {transaction.id}")
            logger.info(f"=== FIN PROCESO STRIPE ===")
            return True, transaction, None
        else:
            logger.warning(f"❌ PAGO FALLIDO: {error}")
            logger.info(f"=== FIN PROCESO STRIPE ===")
            return False, transaction, error
            
    except Exception as e:
        error_msg = f"Error inesperado al procesar el pago: {str(e)}"
        logger.error(f"❌ ERROR CRÍTICO: {error_msg}", exc_info=True)
        logger.info(f"=== FIN PROCESO STRIPE (CON ERROR) ===")
        return False, None, error_msg


def _extract_card_data(medio_pago_data: Dict) -> Optional[Dict]:
    """
    Extrae los datos de tarjeta del diccionario de medio de pago o del objeto ClienteMedioDePago
    
    Args:
        medio_pago_data: Diccionario con los datos del medio de pago o instancia de ClienteMedioDePago
        
    Returns:
        Diccionario con los datos de tarjeta o None si no se encuentran
    """
    try:
        from clientes.models import ClienteMedioDePago
        
        # Si es un objeto ClienteMedioDePago, extraer desde datos_campos
        if isinstance(medio_pago_data, ClienteMedioDePago):
            logger.info(f"Extrayendo datos de tarjeta desde ClienteMedioDePago ID: {medio_pago_data.id}")
            datos_campos = medio_pago_data.datos_campos or {}
            
            logger.info(f"📋 ESTRUCTURA COMPLETA DE datos_campos:")
            for campo, valor in datos_campos.items():
                # Enmascarar valores sensibles para el log
                valor_log = str(valor)[:4] + "****" if len(str(valor)) > 4 else valor
                logger.info(f"  - '{campo}' = '{valor_log}'")
            
            card_data = {}
            
            # Buscar cada campo necesario en datos_campos
            for nombre_campo, valor in datos_campos.items():
                nombre_lower = nombre_campo.lower()
                # Normalizar: quitar tildes y caracteres especiales
                nombre_normalizado = nombre_lower.replace('ú', 'u').replace('ó', 'o').replace('á', 'a').replace('é', 'e').replace('í', 'i')
                
                # Número de tarjeta
                if 'numero' in nombre_normalizado and 'tarjeta' in nombre_normalizado:
                    card_data['card_number'] = str(valor).replace(' ', '').replace('-', '')
                    logger.info(f"✓ Número de tarjeta encontrado en campo '{nombre_campo}'")
                
                # Mes de vencimiento
                elif 'mes' in nombre_normalizado and 'venc' in nombre_normalizado:
                    card_data['exp_month'] = int(valor)
                    logger.info(f"✓ Mes de vencimiento encontrado en campo '{nombre_campo}'")
                
                # Año de vencimiento
                elif 'año' in nombre_lower and 'venc' in nombre_normalizado:
                    year = int(valor)
                    # Si el año es de 2 dígitos, convertir a 4
                    if year < 100:
                        card_data['exp_year'] = 2000 + year
                    else:
                        card_data['exp_year'] = year
                    logger.info(f"✓ Año de vencimiento encontrado en campo '{nombre_campo}'")
                
                # CVC/CVV/CBU - Detectar por nombre del campo o posición
                # Incluir más variaciones: "código de seguridad", "codigo seguridad", "cvc", "cvv", "cbu", "cvu"
                elif ('codigo' in nombre_normalizado and 'seguridad' in nombre_normalizado) or \
                     'cbu' in nombre_normalizado or 'cvc' in nombre_normalizado or \
                     'cvv' in nombre_normalizado or 'cvu' in nombre_normalizado:
                    card_data['cvc'] = str(valor)
                    logger.info(f"✓ CVC encontrado en campo '{nombre_campo}'")
                
                # Nombre del titular
                # Incluir más variaciones: "nombre en la tarjeta", "titular", "nombre tarjeta"
                elif 'titular' in nombre_normalizado or \
                     ('nombre' in nombre_normalizado and 'tarjeta' in nombre_normalizado):
                    card_data['cardholder_name'] = str(valor)
                    logger.info(f"✓ Nombre del titular encontrado en campo '{nombre_campo}'")
            
            logger.info(f"Campos extraídos: {list(card_data.keys())}")
            
        # Si es un diccionario (formato de medio_pago de sesión o vista)
        elif isinstance(medio_pago_data, dict):
            logger.info(f"Extrayendo datos de tarjeta desde diccionario")
            
            # Intentar primero con 'datos_campos' si existe
            datos_campos = medio_pago_data.get('datos_campos', {})
            if datos_campos:
                card_data = {}
                
                for nombre_campo, valor in datos_campos.items():
                    nombre_lower = nombre_campo.lower()
                    # Normalizar: quitar tildes y caracteres especiales
                    nombre_normalizado = nombre_lower.replace('ú', 'u').replace('ó', 'o').replace('á', 'a').replace('é', 'e').replace('í', 'i')
                    
                    # Número de tarjeta
                    if ('tarjeta' in nombre_normalizado or 'card' in nombre_normalizado) and \
                       ('numero' in nombre_normalizado or 'number' in nombre_normalizado):
                        card_data['card_number'] = str(valor).replace(' ', '').replace('-', '')
                    
                    # Mes de vencimiento
                    if 'mes' in nombre_normalizado and ('venc' in nombre_normalizado or 'exp' in nombre_normalizado):
                        card_data['exp_month'] = int(valor)
                    
                    # Año de vencimiento
                    if 'año' in nombre_lower and ('venc' in nombre_normalizado or 'exp' in nombre_normalizado):
                        year = int(valor)
                        if year < 100:
                            card_data['exp_year'] = 2000 + year
                        else:
                            card_data['exp_year'] = year
                    
                    # CVC/CVV - Incluir "código de seguridad"
                    if ('codigo' in nombre_normalizado and 'seguridad' in nombre_normalizado) or \
                       'cvc' in nombre_normalizado or 'cvv' in nombre_normalizado or \
                       'cbu' in nombre_normalizado or 'cvu' in nombre_normalizado:
                        card_data['cvc'] = str(valor)
                    
                    # Nombre del titular
                    if 'titular' in nombre_normalizado or \
                       ('nombre' in nombre_normalizado and 'tarjeta' in nombre_normalizado):
                        card_data['cardholder_name'] = str(valor)
            
            # Fallback: buscar en estructura antigua con 'campos'
            else:
                campos = medio_pago_data.get('campos', [])
                card_data = {}
                
                for campo in campos:
                    nombre = campo.get('nombre', '').lower()
                    # Normalizar
                    nombre_normalizado = nombre.replace('ú', 'u').replace('ó', 'o').replace('á', 'a').replace('é', 'e').replace('í', 'i')
                    valor = campo.get('valor', '')
                    
                    if 'tarjeta' in nombre or 'card_number' in nombre or 'numero' in nombre_normalizado:
                        card_data['card_number'] = valor.replace(' ', '').replace('-', '')
                    elif 'mes' in nombre and 'vencimiento' in nombre:
                        card_data['exp_month'] = int(valor)
                    elif 'año' in nombre and 'vencimiento' in nombre:
                        year = int(valor)
                        if year < 100:
                            card_data['exp_year'] = 2000 + year
                        else:
                            card_data['exp_year'] = year
                    elif ('codigo' in nombre_normalizado and 'seguridad' in nombre_normalizado) or \
                         'cvc' in nombre or 'cvv' in nombre or 'cbu' in nombre:
                        card_data['cvc'] = valor
                    elif 'nombre' in nombre and 'tarjeta' in nombre or 'titular' in nombre:
                        card_data['cardholder_name'] = valor
        
        else:
            logger.error(f"Tipo de medio_pago_data no soportado: {type(medio_pago_data)}")
            return None
        
        # Validar que tenemos todos los datos requeridos
        required_fields = ['card_number', 'exp_month', 'exp_year', 'cvc']
        missing_fields = [field for field in required_fields if field not in card_data]
        
        if not missing_fields:
            logger.info(f"✓ Datos de tarjeta completos extraídos exitosamente")
            return card_data
        else:
            logger.warning(f"Datos de tarjeta incompletos. Falta: {missing_fields}. Encontrados: {list(card_data.keys())}")
            return None
            
    except Exception as e:
        logger.error(f"Error al extraer datos de tarjeta: {str(e)}", exc_info=True)
        return None


def get_transaction_history(cliente, limit: int = None) -> list:
    """
    Obtiene el historial de transacciones de Stripe para un cliente
    
    Args:
        cliente: Usuario/Cliente
        limit: Límite de transacciones a retornar (opcional)
        
    Returns:
        Lista de transacciones ordenadas por fecha descendente
    """
    queryset = StripeTransaction.objects.filter(cliente=cliente).order_by('-created_at')
    
    if limit:
        queryset = queryset[:limit]
    
    return list(queryset)


def get_transaction_by_payment_intent(payment_intent_id: str) -> Optional[StripeTransaction]:
    """
    Obtiene una transacción por su Payment Intent ID
    
    Args:
        payment_intent_id: ID del Payment Intent
        
    Returns:
        StripeTransaction o None si no existe
    """
    try:
        return StripeTransaction.objects.get(payment_intent_id=payment_intent_id)
    except StripeTransaction.DoesNotExist:
        return None
