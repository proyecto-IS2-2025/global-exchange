from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.utils.decorators import method_decorator

from .models import Cliente
from .forms import ClienteForm

from django.contrib import messages
from .models import AsignacionCliente

#Asociar clientes-usuarios

User = get_user_model()


# Vista para asociar usuarios y clientes
@login_required
@user_passes_test(lambda u: u.is_staff)
def asociar_clientes_usuarios_view(request):
    """
    Vista para asociar clientes a usuarios del sistema.

    Solo accesible para usuarios de tipo staff. Permite a un usuario con los
    permisos adecuados asignar clientes a otros usuarios.

    :param request: Objeto de solicitud HTTP.
    :type request: django.http.HttpRequest
    :return: Redirección a la URL 'clientes:asociar_clientes_usuarios' o renderiza el formulario.
    :rtype: django.http.HttpResponse
    """
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario')
        clientes_ids = request.POST.getlist('clientes')
        
        for cliente_id in clientes_ids:
            try:
                usuario = User.objects.get(id=usuario_id)
                cliente = Cliente.objects.get(id=cliente_id)
                
                if not AsignacionCliente.objects.filter(usuario=usuario, cliente=cliente).exists():
                    AsignacionCliente.objects.create(usuario=usuario, cliente=cliente)
                    messages.success(request, f'Se asoció el usuario {usuario.email} con el cliente {cliente.nombre_completo}.')
                else:
                    messages.info(request, f'La asociación entre {usuario.email} y {cliente.nombre_completo} ya existe.')
            except (User.DoesNotExist, Cliente.DoesNotExist):
                messages.error(request, 'Error: No se pudo encontrar el usuario o cliente.')
                return redirect('clientes:asociar_clientes_usuarios')

        return redirect('clientes:asociar_clientes_usuarios')

    usuarios = User.objects.filter(is_superuser=False)
    clientes = Cliente.objects.all()
    context = {
        'usuarios': usuarios,
        'clientes': clientes,
    }
    # 🔴 Antes: 'asociar_clientes_usuarios/admin_asociar.html'
    # ✅ Ahora: usamos el template unificado
    return render(request, 'asociar_a_usuario/asociar_clientes_usuarios.html', context)


# Vista para listar y eliminar asociaciones
@login_required
@user_passes_test(lambda u: u.is_staff)
def listar_asociaciones(request):
    """
    Vista para listar y eliminar asociaciones de clientes con usuarios.

    Permite a los usuarios de tipo staff ver una lista de todas las
    asignaciones existentes y eliminarlas si es necesario.

    :param request: Objeto de solicitud HTTP.
    :type request: django.http.HttpRequest
    :return: Redirección a la URL 'clientes:listar_asociaciones' o renderiza la lista de asignaciones.
    :rtype: django.http.HttpResponse
    """
    if request.method == 'POST' and 'delete_id' in request.POST:
        try:
            asignacion_id = request.POST.get('delete_id')
            asignacion = get_object_or_404(AsignacionCliente, id=asignacion_id)
            asignacion.delete()
            messages.success(request, 'Asociación eliminada correctamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la asociación: {e}')
        return redirect('clientes:listar_asociaciones')

    asignaciones = AsignacionCliente.objects.all().order_by('usuario__email')
    context = {'asignaciones': asignaciones}
    return render(request, 'asociar_a_usuario/lista_asociaciones.html', context)
    #return render(request, 'asociar_clientes_usuarios/test.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def crear_cliente_view(request):
    """
    Vista para crear un nuevo cliente.

    Solo accesible para superusuarios. Maneja la lógica de validación
    y guardado del formulario de creación de clientes.

    :param request: Objeto de solicitud HTTP.
    :type request: django.http.HttpRequest
    :return: Redirección a la URL 'clientes:crear_cliente' o renderiza el formulario.
    :rtype: django.http.HttpResponse
    """
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente creado correctamente.")
            return redirect('clientes:crear_cliente')
    else:
        form = ClienteForm()

    return render(request, 'crear_cliente.html', {'form': form})

@login_required
def lista_clientes(request):
    """
    Vista para listar los clientes asignados a un usuario.

    Solo los usuarios autenticados pueden acceder a esta vista. Muestra los
    clientes que han sido asignados al usuario actual.

    :param request: Objeto de solicitud HTTP.
    :type request: django.http.HttpRequest
    :return: Renderiza la lista de clientes del usuario.
    :rtype: django.http.HttpResponse
    """
    return render(request, 'clientes/lista_clientes.html')

