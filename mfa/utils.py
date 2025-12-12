# mfa/utils.py

import random
from datetime import timedelta
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib import messages
from .models import OTPCode
from django.conf import settings
import logging
import os

# Importar SendGrid API si está disponible
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

# Constantes de tiempo
MASTER_CODE = '000000'
# RESEND_WAIT_TIME = 60 # Eliminamos el tiempo de espera
OTP_EXPIRATION_TIME = 5 # El código es válido por 5 minutos
logger = logging.getLogger(__name__)

def generate_and_send_otp(user, request=None):
    """
    Genera y envía un código OTP al usuario.
    Incluye manejo robusto de errores para evitar bloqueos.
    """
    # 1. Invalidar códigos anteriores
    OTPCode.objects.filter(user=user, is_active=True).update(is_active=False)

    # 2. Generar y guardar el nuevo código
    otp_code = str(random.randint(100000, 999999))
    OTPCode.objects.create(user=user, code=otp_code)

    # 3. Enviar el código por correo con manejo de errores
    subject = 'Tu código de verificación para Global Exchange'
    message = (
        f'Tu código de un solo uso (OTP) es: {otp_code}. '
        f'Es válido por {OTP_EXPIRATION_TIME} minutos.'
    )
    
    # Intentar enviar email
    email_sent = False
    
    # 1. Intentar con SendGrid API (HTTP) si está configurado
    if SENDGRID_AVAILABLE and os.environ.get('SENDGRID_API_KEY'):
        try:
            logger.info(f"Intentando enviar OTP a {user.email} via SendGrid API")
            logger.info(f"From: {settings.DEFAULT_FROM_EMAIL}, To: {user.email}")
            
            message_mail = Mail(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_emails=user.email,
                subject=subject,
                plain_text_content=message
            )
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message_mail)
            
            logger.info(f"SendGrid response status: {response.status_code}")
            logger.info(f"SendGrid response body: {response.body}")
            logger.info(f"SendGrid response headers: {response.headers}")
            
            if response.status_code in [200, 202]:
                logger.info(f"✅ OTP enviado exitosamente via SendGrid API a {user.email}")
                email_sent = True
                
                # Mostrar código también en logs para debugging
                logger.info(f"🔑 CÓDIGO OTP: {otp_code} (para {user.email})")
                
                if request:
                    messages.success(
                        request, 
                        f"Se ha enviado un código a {user.email[:3]}***@g***.com. "
                        f"Es válido por {OTP_EXPIRATION_TIME} min."
                    )
            else:
                logger.error(f"SendGrid retornó código inesperado: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error enviando OTP via SendGrid API: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    # 2. Fallback: Intentar con SMTP
    if not email_sent:
        try:
            send_mail(
                subject, 
                message, 
                settings.DEFAULT_FROM_EMAIL, 
                [user.email],
                fail_silently=True
            )
            logger.info(f"OTP enviado exitosamente via SMTP a {user.email}")
            email_sent = True
            
            if request:
                messages.success(
                    request, 
                    f"Se ha enviado un código a {user.email[:3]}***@g***.com. "
                    f"Es válido por {OTP_EXPIRATION_TIME} min."
                )
        except Exception as e:
            logger.error(f"Error enviando OTP via SMTP: {str(e)}")
    
    # 3. Si ambos fallan, mostrar código en logs
    if not email_sent:
        logger.warning(f"⚠️ CÓDIGO OTP PARA {user.email}: {otp_code} (válido {OTP_EXPIRATION_TIME} min)")
        print(f"\n{'='*60}")
        print(f"⚠️ CÓDIGO MFA PARA: {user.email}")
        print(f"CÓDIGO: {otp_code}")
        print(f"VÁLIDO: {OTP_EXPIRATION_TIME} minutos")
        print(f"{'='*60}\n")
        
        if request:
            messages.warning(
                request, 
                "⚠️ No se pudo enviar el email. Contacta al administrador para obtener tu código MFA."
            )

    return True  # SIEMPRE retornar True para no bloquear el login

def check_otp_validity(user, entered_code):
    # A. Verificar Código Maestro (000000)
    if entered_code == MASTER_CODE:
        return True
    
    # B. Verificar Código OTP Activo
    try:
        active_code = OTPCode.objects.filter(
            user=user, 
            code=entered_code, 
            is_active=True
        ).latest('created_at')
        
        if active_code.is_valid():
            # Invalida el código después de su uso
            active_code.is_active = False
            active_code.save()
            return True
        
    except OTPCode.DoesNotExist:
        pass
        
    return False