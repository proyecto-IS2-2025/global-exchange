"""
Vistas para asociación cliente-usuario.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib import messages

from clientes.models import Cliente, AsignacionCliente

User = get_user_model()


@login_required
@user_passes_test(lambda u: u.is_staff)
def asociar_clientes_usuarios_view(request):
    """Vista para asociar clientes a usuarios del sistema."""
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario')
        clientes_ids = request.POST.getlist('clientes')
        
        usuario = get_object_or_404(User, id=usuario_id)
        registered_group, _ = Group.objects.get_or_create(name='usuario_registrado')
        associated_group, _ = Group.objects.get_or_create(name='cliente')
        
        for cliente_id in clientes_ids:
            try:
                cliente = Cliente.objects.get(id=cliente_id)
                
                if not AsignacionCliente.objects.filter(usuario=usuario, cliente=cliente).exists():
                    AsignacionCliente.objects.create(usuario=usuario, cliente=cliente)
                    messages.success(
                        request, 
                        f'Se asoció el usuario {usuario.email} con el cliente {cliente.nombre_completo}.'
                    )
                else:
                    messages.info(
                        request, 
                        f'La asociación entre {usuario.email} y {cliente.nombre_completo} ya existe.'
                    )
            except Cliente.DoesNotExist:
                messages.error(request, 'Error: No se pudo encontrar el cliente.')
                return redirect('clientes:asociar_clientes_usuarios')
            
        if AsignacionCliente.objects.filter(usuario=usuario).exists():
            usuario.groups.add(associated_group)
            usuario.groups.remove(registered_group)

        return redirect('clientes:asociar_clientes_usuarios')

    usuarios = User.objects.filter(is_superuser=False)
    clientes = Cliente.objects.all()
    context = {
        'usuarios': usuarios,
        'clientes': clientes,
    }
    return render(request, 'asociar_a_usuario/asociar_clientes_usuarios.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def listar_asociaciones(request):
    """Vista para listar y eliminar asociaciones."""
    if request.method == 'POST' and 'delete_id' in request.POST:
        try:
            asignacion_id = request.POST.get('delete_id')
            asignacion = get_object_or_404(AsignacionCliente, id=asignacion_id)
            usuario = asignacion.usuario
            asignacion.delete()
            messages.success(request, 'Asociación eliminada correctamente.')

            if not AsignacionCliente.objects.filter(usuario=usuario).exists():
                registered_group, _ = Group.objects.get_or_create(name='usuario_registrado')
                associated_group, _ = Group.objects.get_or_create(name='cliente')
                
                usuario.groups.remove(associated_group)
                usuario.groups.add(registered_group)
                messages.info(
                    request, 
                    f'El usuario {usuario.email} ya no tiene clientes asignados.'
                )

        except Exception as e:
            messages.error(request, f'Error al eliminar la asociación: {e}')
        return redirect('clientes:listar_asociaciones')

    asignaciones = AsignacionCliente.objects.all().order_by('usuario__email')
    context = {'asignaciones': asignaciones}
    return render(request, 'asociar_a_usuario/lista_asociaciones.html', context)