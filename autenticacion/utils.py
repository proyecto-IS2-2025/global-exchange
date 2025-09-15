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

    Crea un token único para el correo electrónico del usuario y genera
    un enlace de verificación. Luego, utiliza la configuración de correo
    de Django para enviar el mensaje con ese enlace.

    :param email: Correo electrónico del destinatario.
    :return: No devuelve nada.
    """
    token = generar_token(email)
    enlace = f"http://127.0.0.1:8000/verificar/{token}/"  # Usá tu dominio local o real
    asunto = "Verificá tu correo electrónico"
    mensaje = f"Hacé clic en el siguiente enlace para verificar tu cuenta:\n{enlace}"

    send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [email])

