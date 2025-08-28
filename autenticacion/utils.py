from django.core.signing import TimestampSigner
from django.core.mail import send_mail
from django.conf import settings

def generar_token(email):
    signer = TimestampSigner()
    return signer.sign(email)

def enviar_verificacion(email):
    token = generar_token(email)
    enlace = f"http://127.0.0.1:8000/verificar/{token}/"  # Usá tu dominio local o real
    asunto = "Verificá tu correo electrónico"
    mensaje = f"Hacé clic en el siguiente enlace para verificar tu cuenta:\n{enlace}"

    send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [email])

