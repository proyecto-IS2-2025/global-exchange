from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from .utils import enviar_verificacion
User = get_user_model()

def registro_usuario(request):
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