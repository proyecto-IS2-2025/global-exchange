# mfa/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.urls import reverse
from .utils import generate_and_send_otp, check_otp_validity

User = get_user_model()

# ----------------------------------------------------------------------
# Vista Dedicada para Reenviar el Código
# ----------------------------------------------------------------------
def mfa_resend_view(request):
    """Maneja el reenvío del código OTP y redirige a la verificación."""
    user_id = request.session.get('mfa_user_id')
    if not user_id:
        messages.error(request, "Sesión de verificación expirada.")
        return redirect('login') 
    
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
        del request.session['mfa_user_id']
        return redirect('login')

    # Llama a la función que genera y envía (con su chequeo de tiempo)
    generate_and_send_otp(user, request)
    
    # Redirige de nuevo a la página de verificación
    return redirect(reverse('mfa:mfa_verify'))

# ----------------------------------------------------------------------
# Vista de Verificación (Simplificada)
# ----------------------------------------------------------------------
def mfa_verify_view(request):
    user_id = request.session.get('mfa_user_id')
    if not user_id:
        messages.error(request, "Sesión de verificación expirada. Vuelve a iniciar sesión.")
        return redirect('login') 

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
        del request.session['mfa_user_id']
        return redirect('login')

    if request.method == 'POST':
        # Esta vista ahora solo maneja el intento de verificación del código
        entered_code = request.POST.get('otp_code', '').strip()

        if check_otp_validity(user, entered_code):
            # Éxito: Iniciar sesión, limpiar sesión MFA y redirigir
            login(request, user)
            del request.session['mfa_user_id']
            messages.success(request, "¡Inicio de sesión exitoso!")
            return redirect('inicio')
        else:
            messages.error(request, "El código es incorrecto o ha expirado.")

    context = {
        'email_masked': f"{user.email[:3]}***@g***.com" 
    }
    return render(request, 'mfa/mfa_verify.html', context)