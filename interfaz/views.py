from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model # <-- Importación correcta

from .models import PerfilUsuario
from .utils import enviar_verificacion

# Obtiene el modelo de usuario configurado en settings.py
User = get_user_model()


def menu_principal(request):
    return render(request, "menu.html")

def inicio(request):
    return render(request, 'inicio.html')

def login_view(request):
    return render(request, 'login.html')

def registro_view(request):
    return render(request, 'registro.html')

def contacto(request):
    return render(request, 'contacto.html')

# Registro de usuario
def registro_usuario(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        password = request.POST.get('password')

        if User.objects.filter(email=email).exists(): # <-- Uso de la variable User
            messages.error(request, "Ya existe un usuario con ese correo.")
            return render(request, 'registro.html')

        # Crear usuario desactivado hasta que verifique el correo
        usuario = User.objects.create_user(username=email, email=email, password=password)
        usuario.is_active = False
        usuario.save()

        # Crear perfil
        PerfilUsuario.objects.create(usuario=usuario, nombre_completo=nombre, telefono=telefono)

        # Enviar correo de verificación
        enviar_verificacion(email)

        messages.success(request, "Registro exitoso. Verificá tu correo para activar tu cuenta.")
        return redirect('login')

    return render(request, 'registro.html')

def verificar_correo(request, token):
    signer = TimestampSigner()
    try:
        email = signer.unsign(token, max_age=86400)  # 24 horas
        usuario = User.objects.get(email=email) # <-- Uso de la variable User
        usuario.is_active = True
        usuario.save()
        messages.success(request, "Correo verificado correctamente.")
        return redirect('login')
    except (BadSignature, SignatureExpired):
        messages.error(request, "El enlace de verificación no es válido o ha expirado.")
        return redirect('registro')

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')