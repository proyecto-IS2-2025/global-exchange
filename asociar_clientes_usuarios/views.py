# asociar_clientes_usuarios/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from .models import Cliente, AsignacionCliente

User = get_user_model()

def asociar_admin_view(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario')
        clientes_ids = request.POST.getlist('clientes')

        usuario = User.objects.get(id=usuario_id)

        # Eliminar asignaciones existentes para este usuario
        usuario.asociar_clientes_usuarios_asignaciones.all().delete()

        # Crear nuevas asignaciones
        for cliente_id in clientes_ids:
            cliente = Cliente.objects.get(id=cliente_id)
            AsignacionCliente.objects.create(usuario=usuario, cliente=cliente)

        return redirect('home')  # Redirigir a la página de inicio o a donde sea necesario

    # Si es una solicitud GET, renderizar el formulario
    usuarios = User.objects.all()
    clientes = Cliente.objects.all()
    context = {
        'usuarios': usuarios,
        'clientes': clientes
    }
    return render(request, 'asociar_clientes_usuarios/asociar_admin.html', context)


# Placeholder views to satisfy the URLs
def seleccion_cliente_view(request):
    return render(request, 'asociar_clientes_usuarios/seleccionar_cliente.html')

def guardar_seleccion_cliente(request, cliente_id):
    return redirect('home')

def home_view(request):
    return render(request, 'asociar_clientes_usuarios/home.html')