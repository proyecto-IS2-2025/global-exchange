# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model # Importación corregida
from .models import Cliente, AsignacionCliente

# Obtén el modelo de usuario personalizado
User = get_user_model()

@login_required
def seleccion_cliente_view(request):
    """
    Vista para que el usuario seleccione uno de sus clientes asignados.
    """
    clientes = Cliente.objects.filter(usuarios__id=request.user.id)

    if not clientes.exists():
        # Si el usuario no tiene clientes asignados
        return render(request, 'error.html',
                      {'mensaje': 'No tienes clientes asignados. Por favor, contacta a un administrador.'})

    if clientes.count() == 1:
        # Si solo tiene un cliente, se selecciona automáticamente
        request.session['cliente_id_actual'] = clientes.first().id
        return redirect('home')

    # Si tiene varios clientes, se muestra la lista para elegir
    return render(request, 'asociar_clientes.html', {'clientes': clientes})


@login_required
def asociar_admin_view(request):
    """
    Vista para que el administrador asigne clientes a usuarios.
    """
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        # El admin envía la asociación de clientes a un usuario
        usuario_id = request.POST.get('usuario')
        clientes_ids = request.POST.getlist('clientes')

        try:
            usuario = User.objects.get(id=usuario_id) # <-- Cambio aquí
            # Elimina asociaciones anteriores
            AsignacionCliente.objects.filter(usuario=usuario).delete()

            # Crea las nuevas asociaciones
            for cliente_id in clientes_ids:
                cliente = Cliente.objects.get(id=cliente_id)
                AsignacionCliente.objects.create(usuario=usuario, cliente=cliente)

            return redirect('asociar_admin')

        except (User.DoesNotExist, Cliente.DoesNotExist):
            return render(request, 'error.html', {'mensaje': 'Error: Usuario o cliente no encontrado.'})

    else:
        # Muestra formulario de asignación
        usuarios = User.objects.all() # <-- Cambio aquí
        clientes = Cliente.objects.all()
        return render(request, 'admin_asociar.html', {'usuarios': usuarios, 'clientes': clientes})


# new_app/views.py (Este código debe estar en un archivo separado)
# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth import get_user_model
# from .models import Cliente
# ...
# User = get_user_model()
# ...
# Las correcciones para este archivo ya se dieron en una respuesta anterior.
# Por favor, asegúrate de que el archivo views.py de 'nueva_app' también use 'get_user_model()'.
# ...

def home_view(request):
    """
    Vista de inicio para redirigir a la selección de cliente
    o mostrar la página principal si ya hay un cliente en sesión.
    """
    if request.user.is_authenticated:
        if 'cliente_id_actual' not in request.session:
            return redirect('seleccionar_cliente')

        try:
            # Intentamos obtener el cliente.
            cliente_actual = Cliente.objects.get(id=request.session['cliente_id_actual'])
            return render(request, 'home.html', {'cliente_actual': cliente_actual})

        except Cliente.DoesNotExist:
            # Si el cliente no se encuentra, lo borramos de la sesión
            # y lo redirigimos a la página de selección para que elija uno nuevo.
            del request.session['cliente_id_actual']
            return redirect('seleccionar_cliente')

    return render(request, 'landing_page.html')


def guardar_seleccion_cliente(request, cliente_id):
    """
    Guarda en la sesión el cliente seleccionado por el usuario.
    """
    if request.user.is_authenticated:
        try:
            cliente = Cliente.objects.get(id=cliente_id, usuarios__id=request.user.id)
            request.session['cliente_id_actual'] = cliente.id
            return redirect('home')
        except Cliente.DoesNotExist:
            return render(request, 'error.html', {'mensaje': 'El cliente seleccionado no es válido.'})

    return redirect('login')