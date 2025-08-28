from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from .models import PerfilUsuario
from .utils import enviar_verificacion
from users.models import CustomUser, Segmento
from clientes.models import Cliente
from clientes.forms import ClienteForm
from asociar_clientes_usuarios.models import AsignacionCliente
from django.http import HttpResponseForbidden

User = get_user_model()

def inicio(request):
    return render(request, 'inicio.html')

def contacto(request):
    return render(request, 'contacto.html')

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
                
                if user.is_staff:
                    messages.success(request, "Inicio de sesión como Administrador exitoso.")
                    return redirect('admin_dashboard')
                elif hasattr(user, 'is_cambista') and user.is_cambista:
                    messages.success(request, "Inicio de sesión como Cambista exitoso.")
                    return redirect('cambista_dashboard')
                else:
                    messages.success(request, "Inicio de sesión exitoso. Bienvenido.")
                    return redirect('cliente_dashboard')
            else:
                messages.error(request, 'Tu cuenta no ha sido activada.')
        else:
            messages.error(request, 'Correo o contraseña incorrectos.')
            
    return render(request, 'login.html')

@login_required
def cliente_dashboard(request):
    return render(request, 'cliente/dashboard.html')


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('cliente_dashboard')
    
    # MODIFICACIÓN: Obtener solo usuarios que NO son superusuarios.
    usuarios = CustomUser.objects.exclude(is_superuser=True)
    clientes = Cliente.objects.all()
    
    context = {
        'usuarios': usuarios,
        'clientes': clientes,
    }
    return render(request, 'admin/dashboard.html', context)


@login_required
def dashboard(request):
    if request.user.rol != "admin":   # o request.user.is_staff
        return HttpResponseForbidden("No tienes permiso para ver esta página.")
    return render(request, "admin/dashboard.html")
    
@login_required
def cambista_dashboard(request):
    if not hasattr(request.user, 'is_cambista') or not request.user.is_cambista:
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('cliente_dashboard')
    return render(request, 'cambista/dashboard.html')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def crear_cliente_admin(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente creado correctamente.")
            return redirect('crear_cliente_admin')
    else:
        form = ClienteForm()

    return render(request, 'admin/crear_cliente.html', {'form': form})