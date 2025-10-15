# mfa/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from .utils import generate_and_send_otp, check_otp_validity
from .models import MFAConfig

User = get_user_model()

# ----------------------------------------------------------------------
# Verificar si el usuario es admin
# ----------------------------------------------------------------------
def is_admin(user):
    return user.is_authenticated and user.groups.filter(name='admin').exists()

# ----------------------------------------------------------------------
# Vista de Configuración MFA (Solo Admins)
# ----------------------------------------------------------------------
@login_required
@user_passes_test(is_admin)
def mfa_config_view(request):
    """Vista para configurar el MFA (activar/desactivar)."""
    config = MFAConfig.get_config()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'toggle_login':
            config.mfa_login_enabled = not config.mfa_login_enabled
            config.updated_by = request.user
            config.save()
            status = "activado" if config.mfa_login_enabled else "desactivado"
            messages.success(request, f"MFA en Login {status} exitosamente.")
        
        elif action == 'toggle_compra':
            config.mfa_compra_enabled = not config.mfa_compra_enabled
            config.updated_by = request.user
            config.save()
            status = "activado" if config.mfa_compra_enabled else "desactivado"
            messages.success(request, f"MFA en Compra {status} exitosamente.")
        
        return redirect('mfa:config')
    
    context = {
        'config': config,
        'grupo_admin': True
    }
    return render(request, 'mfa/mfa_config.html', context)

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
        if 'mfa_user_id' in request.session:
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
        if 'mfa_user_id' in request.session:
            del request.session['mfa_user_id']
        return redirect('login')

    if request.method == 'POST':
        # Esta vista ahora solo maneja el intento de verificación del código
        entered_code = request.POST.get('otp_code', '').strip()

        if check_otp_validity(user, entered_code):
            # Éxito: Limpiar sesión MFA ANTES de login
            if 'mfa_user_id' in request.session:
                del request.session['mfa_user_id']
            
            # Iniciar sesión
            login(request, user)
            # del request.session['mfa_user_id']
            messages.success(request, f"¡Inicio de sesión exitoso!")
            
            # Usar tu redirección existente por grupo
            return redirect('inicio')
        else:
            messages.error(request, "El código es incorrecto o ha expirado.")

    context = {
        'email_masked': f"{user.email[:3]}***@g***.com" 
    }
    return render(request, 'mfa/mfa_verify.html', context)