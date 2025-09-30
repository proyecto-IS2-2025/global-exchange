# mfa/utils.py

import random
from datetime import timedelta
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib import messages
from .models import OTPCode
from django.conf import settings

# Constantes de tiempo
MASTER_CODE = '000000'
RESEND_WAIT_TIME = 60 # 1 minuto en segundos
OTP_EXPIRATION_TIME = 5 # 5 minutos

def generate_and_send_otp(user, request=None):
    # 1. Verificar tiempo de espera (1 minuto)
    try:
        latest_code = OTPCode.objects.filter(user=user).latest()
        time_since_last_code = timezone.now() - latest_code.created_at
        
        if time_since_last_code < timedelta(seconds=RESEND_WAIT_TIME):
            wait_seconds = (timedelta(seconds=RESEND_WAIT_TIME) - time_since_last_code).total_seconds()
            if request:
                messages.warning(request, f"Debes esperar {int(wait_seconds)} segundos antes de solicitar un nuevo código.")
            return False

    except OTPCode.DoesNotExist:
        pass

    # 2. Invalida códigos anteriores
    OTPCode.objects.filter(user=user, is_active=True).update(is_active=False)

    # 3. Genera y guarda el nuevo código
    otp_code = str(random.randint(100000, 999999))
    OTPCode.objects.create(user=user, code=otp_code)

    # 4. Envía el código por correo
    subject = 'Tu código de verificación para Global Exchange'
    message = (
        f'Tu código de un solo uso (OTP) es: {otp_code}. '
        f'Es válido por {OTP_EXPIRATION_TIME} minutos.'
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    
    if request:
        messages.success(request, f"Se ha enviado un código a {user.email[:3]}***@g***.com. Es válido por {OTP_EXPIRATION_TIME} min.")

    return True

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