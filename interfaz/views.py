from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from users.models import CustomUser
from clientes.models import Cliente
from clientes.forms import ClienteForm
from django.contrib.auth import get_user_model

User = get_user_model()

def inicio(request):
    return render(request, 'inicio.html')

def contacto(request):
    return render(request, 'contacto.html')


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