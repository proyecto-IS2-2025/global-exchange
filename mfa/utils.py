# mfa/utils.py

import random
from datetime import timedelta
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib import messages
from .models import OTPCode
from django.conf import settings
import logging

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
    
    try:
        send_mail(
            subject, 
            message, 
            settings.DEFAULT_FROM_EMAIL, 
            [user.email],
            fail_silently=False  # ← Capturar errores para diagnóstico
        )
        logger.info(f"OTP enviado exitosamente a {user.email}")
        
        if request:
            messages.success(
                request, 
                f"Se ha enviado un código a {user.email[:3]}***@g***.com. "
                f"Es válido por {OTP_EXPIRATION_TIME} min."
            )
    except Exception as e:
        # Registrar el error completo
        logger.error(f"Error enviando OTP a {user.email}: {str(e)}")
        
        # ⚠️ FALLBACK: Mostrar código en logs cuando falla el envío
        logger.warning(f"⚠️ CÓDIGO OTP PARA {user.email}: {otp_code} (válido {OTP_EXPIRATION_TIME} min)")
        print(f"\n{'='*60}")
        print(f"⚠️ ERROR ENVIANDO EMAIL - CÓDIGO EN LOGS")
        print(f"Usuario: {user.email}")
        print(f"Código OTP: {otp_code}")
        print(f"Válido por: {OTP_EXPIRATION_TIME} minutos")
        print(f"{'='*60}\n")
        
        if request:
            messages.warning(
                request, 
                "⚠️ No se pudo enviar el email. Verifica los logs del sistema para obtener el código MFA."
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