from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import AsignacionCliente
from clientes.models import Cliente

User = get_user_model()


# Vista para asociar usuarios y clientes
@login_required
@user_passes_test(lambda u: u.is_staff)
def asociar_admin_view(request):
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
                return redirect('asociar_admin')

        return redirect('asociar_admin')

    usuarios = User.objects.filter(is_superuser=False)
    clientes = Cliente.objects.all()
    context = {
        'usuarios': usuarios,
        'clientes': clientes,
    }
    # 🔴 Antes: 'asociar_clientes_usuarios/admin_asociar.html'
    # ✅ Ahora: usamos el template unificado
    return render(request, 'admin/dashboard.html', context)


# Vista para listar y eliminar asociaciones
@login_required
@user_passes_test(lambda u: u.is_staff)
def listar_asociaciones(request):
    if request.method == 'POST' and 'delete_id' in request.POST:
        try:
            asignacion_id = request.POST.get('delete_id')
            asignacion = get_object_or_404(AsignacionCliente, id=asignacion_id)
            asignacion.delete()
            messages.success(request, 'Asociación eliminada correctamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la asociación: {e}')
        return redirect('listar_asociaciones')

    asignaciones = AsignacionCliente.objects.all().order_by('usuario__email')
    context = {'asignaciones': asignaciones}
    return render(request, 'asociar_clientes_usuarios/lista_asociaciones.html', context)
