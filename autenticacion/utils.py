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
logger = logging.getLogger(__name__)

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
    Incluye manejo robusto de errores para evitar bloqueos.
    """
    try:
        token = generar_token(email)
        # Usar el dominio de producción o desarrollo según corresponda
        dominio = "https://global-exchange.onrender.com" if not settings.DEBUG else "http://127.0.0.1:8000"
        enlace = f"{dominio}/verificar/{token}/"
        
        asunto = "Verificá tu correo electrónico - Global Exchange"
        mensaje = f"Hacé clic en el siguiente enlace para verificar tu cuenta:\n\n{enlace}"

        send_mail(
            asunto, 
            mensaje, 
            settings.DEFAULT_FROM_EMAIL, 
            [email],
            fail_silently=True  # ← NO BLOQUEAR si falla el envío
        )
        logger.info(f"Email de verificación enviado a {email}")
        
    except Exception as e:
        logger.error(f"Error enviando verificación a {email}: {str(e)}")
        
        # En desarrollo, mostrar el enlace en consola
        if settings.DEBUG:
            print(f"\n{'='*60}")
            print(f"⚠️  ERROR ENVIANDO EMAIL - MODO DEBUG")
            print(f"ENLACE DE VERIFICACIÓN PARA {email}:")
            print(f"{enlace}")
            print(f"{'='*60}\n")

