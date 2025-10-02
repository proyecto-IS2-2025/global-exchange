"""
Módulo de vistas de la aplicación de autenticación.

Este módulo maneja las vistas relacionadas con el registro, verificación de correo electrónico
e inicio de sesión de usuarios. Utiliza el sistema de mensajes de Django para notificar
a los usuarios sobre el estado de sus acciones.

Funciones:
    - `registro_usuario`: Maneja el registro de nuevos usuarios.
    - `verificar_correo`: Activa la cuenta del usuario a través de un token de verificación.
    - `login_view`: Maneja el inicio de sesión e implementa el flujo MFA.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.urls import reverse
from .utils import enviar_verificacion
# Importa tus modelos para el registro
from autenticacion.models import PerfilUsuario 
# Importar la utilidad de MFA de la nueva aplicación
from mfa.utils import generate_and_send_otp 


User = get_user_model()


def registro_usuario(request):
    """
    Vista para el registro de un nuevo usuario.

    Procesa el formulario de registro. Si es POST, crea un nuevo usuario inactivo,
    crea su perfil asociado y envía un correo de verificación.
    """
    if request.method == 'POST':
        # 1. Obtener datos del formulario (de registro.html)
        nombre_completo = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        password = request.POST.get('password')

        # Usamos el email como username para el modelo CustomUser
        username = email

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Este correo electrónico ya está registrado.')
            return render(request, 'registro.html')
        
        try:
            # 2. Crear el Usuario (inactivo hasta la verificación)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=False  # Cuenta inactiva
            )
            
            # 3. Crear el perfil asociado
            PerfilUsuario.objects.create(
                usuario=user,
                nombre_completo=nombre_completo,
                telefono=telefono
            )

            # 4. Enviar correo de verificación (usando tu utilidad existente)
            enviar_verificacion(email)

            messages.success(request, 'Registro exitoso. Revisa tu correo para verificar tu cuenta y poder iniciar sesión.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Ocurrió un error durante el registro: {e}')
    
    return render(request, 'registro.html')


def verificar_correo(request, token):
    """
    Función para verificar el correo electrónico del usuario usando un token.
    """
    signer = TimestampSigner()
    try:
        # Intenta unsign con un límite de tiempo (ej. 48 horas, si no está definido en TimestampSigner)
        email = signer.unsign(token, max_age=172800) 
        
        # Buscar el usuario por email
        user = get_object_or_404(User, email=email)
        
        if not user.is_active:
            user.is_active = True
            user.save()
            messages.success(request, '¡Tu correo ha sido verificado! Ya puedes iniciar sesión.')
        else:
            messages.info(request, 'Tu cuenta ya estaba activa. Ya puedes iniciar sesión.')

    except SignatureExpired:
        messages.error(request, 'El enlace de verificación ha caducado. Por favor, regístrate de nuevo.')
    except BadSignature:
        messages.error(request, 'El token de verificación es inválido.')
    except Exception:
        messages.error(request, 'Ha ocurrido un error inesperado durante la verificación.')

    return redirect('login')


# ----------------------------------------------------------------------

def login_view(request):
    """
    Vista modificada para el inicio de sesión. 
    Tras credenciales válidas, inicia el flujo de verificación MFA.
    """
    # 1. Si el usuario ya está autenticado, redirigir
    if request.user.is_authenticated:
        # Usa tu vista de redirección por grupo
        return redirect('redirect_dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Autentica usando el EmailBackend
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:
                # ==========================================================
                # === IMPLEMENTACIÓN MFA: REEMPLAZA EL LOGIN DIRECTO ===
                # ==========================================================
                
                # 1. Almacenar el ID del usuario en la sesión para el proceso MFA
                #    (No logueamos al usuario con login() todavía)
                request.session['mfa_user_id'] = user.id
                
                # 2. Generar y enviar el primer código OTP
                #    La función devuelve False si hay que esperar 1 min
                if generate_and_send_otp(user, request):
                     # 3. Redirigir a la página de verificación MFA
                    return redirect(reverse('mfa:mfa_verify'))
                else:
                    # Si falla por tiempo de espera (genera_and_send_otp devuelve False)
                    # El mensaje de advertencia ya fue añadido. Limpiamos sesión temporal
                    if 'mfa_user_id' in request.session:
                        del request.session['mfa_user_id']
                    return render(request, 'login.html') 

            else:
                messages.error(request, 'Tu cuenta no ha sido activada. Revisa tu correo.')
        else:
            messages.error(request, 'Correo o contraseña incorrectos.')

    return render(request, 'login.html')