"""
Módulo de utilidades para la aplicación de autenticación.

Este módulo contiene funciones de apoyo para la gestión de usuarios,
específicamente para la generación de tokens de verificación y el envío de correos
electrónicos.

Funciones:
    - `generar_token`: Genera un token firmado para la verificación de correo.
    - `enviar_verificacion`: Envía un correo electrónico de verificación al usuario.
"""
from django.core.signing import TimestampSigner
from django.core.mail import send_mail
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

# Importar SendGrid API si está disponible
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

def generar_token(email):
    """
    Genera un token de firma con marca de tiempo.

    Este token se utiliza para la verificación del correo electrónico y
    expira después de un período de tiempo predefinido.

    :param email: Correo electrónico del usuario a firmar.
    :return: El token firmado en formato de cadena de texto.
    :rtype: str
    """
    signer = TimestampSigner()
    return signer.sign(email)

def enviar_verificacion(email):
    """
    Envía un correo electrónico de verificación al usuario.
    Usa SendGrid API preferentemente, con fallback a SMTP.
    """
    token = generar_token(email)
    # Usar el dominio de producción correcto
    dominio = "https://global-exchange-atrg.onrender.com" if not settings.DEBUG else "http://127.0.0.1:8000"
    enlace = f"{dominio}/verificar/{token}/"
    
    asunto = "Verificá tu correo electrónico - Global Exchange"
    mensaje = f"Hacé clic en el siguiente enlace para verificar tu cuenta:\n\n{enlace}\n\nEste enlace es válido por 48 horas."
    
    email_sent = False
    
    # 1. Intentar con SendGrid API (HTTP)
    if SENDGRID_AVAILABLE and os.environ.get('SENDGRID_API_KEY'):
        try:
            logger.info(f"Intentando enviar verificación a {email} via SendGrid API")
            
            message_mail = Mail(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_emails=email,
                subject=asunto,
                plain_text_content=mensaje
            )
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message_mail)
            
            if response.status_code in [200, 202]:
                logger.info(f"✅ Email de verificación enviado via SendGrid API a {email}")
                logger.info(f"🔗 Enlace de verificación: {enlace}")
                email_sent = True
            else:
                logger.error(f"SendGrid retornó código inesperado: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error enviando verificación via SendGrid API: {str(e)}")
    
    # 2. Fallback: Intentar con SMTP
    if not email_sent:
        try:
            send_mail(
                asunto, 
                mensaje, 
                settings.DEFAULT_FROM_EMAIL, 
                [email],
                fail_silently=True
            )
            logger.info(f"Email de verificación enviado via SMTP a {email}")
            email_sent = True
        except Exception as e:
            logger.error(f"Error enviando verificación via SMTP: {str(e)}")
    
    # 3. Si ambos fallan, mostrar enlace en logs
    if not email_sent:
        logger.warning(f"⚠️ ENLACE DE VERIFICACIÓN PARA {email}: {enlace}")
        print(f"\n{'='*60}")
        print(f"⚠️ ENLACE DE VERIFICACIÓN")
        print(f"Email: {email}")
        print(f"Enlace: {enlace}")
        print(f"Válido: 48 horas")
        print(f"{'='*60}\n")

