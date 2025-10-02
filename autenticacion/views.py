"""
Módulo de vistas de la aplicación de autenticación.

Este módulo maneja las vistas relacionadas con el registro, verificación de correo electrónico
e inicio de sesión de usuarios. Utiliza el sistema de mensajes de Django para notificar
a los usuarios sobre el estado de sus acciones.

Funciones:
    - `registro_usuario`: Maneja el registro de nuevos usuarios.
    - `verificar_correo`: Activa la cuenta del usuario a través de un token de verificación.
    - `login_view`: Maneja el inicio de sesión y redirecciona a los usuarios según su grupo.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from .utils import enviar_verificacion
User = get_user_model()

def registro_usuario(request):
    """
    Vista para el registro de un nuevo usuario.

    Esta función procesa el formulario de registro. Si el método es POST, valida
    los datos, crea un nuevo usuario inactivo y envía un correo de verificación.
    Si el usuario ya existe, muestra un mensaje de error. Si el registro es exitoso,
    redirige a la página de login.

    :param request: Objeto HttpRequest.
    :return: HttpResponse que renderiza la plantilla 'registro.html' o redirige a 'login'.
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        password = request.POST.get('password')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Ya existe un usuario con ese correo.")
            return render(request, 'registro.html')

        usuario = User.objects.create_user(username=email, email=email, password=password)
        usuario.is_active = False
        usuario.save()

        enviar_verificacion(email)

        messages.success(request, "Registro exitoso. Verificá tu correo para activar tu cuenta.")
        return redirect('login')

    return render(request, 'registro.html')


def verificar_correo(request, token):
    """
    Vista para la verificación del correo electrónico del usuario.

    Utiliza un token firmado y con límite de tiempo para verificar la identidad
    del usuario. Si el token es válido y no ha expirado, activa la cuenta del
    usuario y lo redirige a la página de login. En caso contrario, muestra
    un mensaje de error.

    :param request: Objeto HttpRequest.
    :param token: El token de verificación enviado por correo.
    :return: HttpResponse que redirige a 'login' o 'registro'.
    """
    signer = TimestampSigner()
    try:
        email = signer.unsign(token, max_age=86400)
        usuario = get_object_or_404(User, email=email)
        usuario.is_active = True
        usuario.save()
        messages.success(request, "Correo verificado correctamente. Ya puedes iniciar sesión.")
        return redirect('login')
    except (BadSignature, SignatureExpired):
        messages.error(request, "El enlace de verificación no es válido o ha expirado.")
        return redirect('registro')


def login_view(request):
    """
    Vista para el inicio de sesión de usuarios.

    Esta función autentica a los usuarios basándose en su correo electrónico y contraseña.
    Si la autenticación es exitosa y la cuenta está activa, inicia la sesión y redirige
    al usuario a la página de inicio según su grupo de permisos (admin, operador o cliente).
    En caso de credenciales incorrectas o cuenta inactiva, muestra un mensaje de error.

    :param request: Objeto HttpRequest.
    :return: HttpResponse que renderiza la plantilla 'login.html' o redirige a 'inicio'.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)

                # 🚀 Redirección según el grupo
                grupos = list(user.groups.values_list('name', flat=True))

                if "admin" in grupos:
                    messages.success(request, "Inicio de sesión como Administrador exitoso.")
                    return redirect('inicio')
                elif "operador" in grupos:
                    messages.success(request, "Inicio de sesión como Operador exitoso.")
                    return redirect('inicio')
                elif "cliente" in grupos:
                    messages.success(request, "Inicio de sesión como Cliente exitoso.")
                    return redirect('inicio')
                else:
                    messages.warning(request, "No tienes un grupo asignado. Contacta con un administrador.")
                    return redirect('inicio')

            else:
                messages.error(request, 'Tu cuenta no ha sido activada.')
        else:
            messages.error(request, 'Correo o contraseña incorrectos.')

    return render(request, 'login.html')