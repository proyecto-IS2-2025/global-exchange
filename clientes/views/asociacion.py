"""
Vistas para asociación cliente-usuario.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib import messages

from clientes.models import Cliente, AsignacionCliente
from clientes.decorators import require_permission

User = get_user_model()


@login_required
@require_permission("clientes.assign_clientes_operadores", check_client_assignment=False)
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
@require_permission("clientes.assign_clientes_operadores", check_client_assignment=False)
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
            
            # Guarda el usuario antes de eliminar la asignación
            usuario = asignacion.usuario
            
            # Elimina la asignación
            asignacion.delete()
            messages.success(request, 'Asociación eliminada correctamente.')

            # Verifica si al usuario le quedan clientes asignados
            if not AsignacionCliente.objects.filter(usuario=usuario).exists():
                # Si no tiene más asignaciones, cambia su grupo
                registered_group, created_reg = Group.objects.get_or_create(name='usuario_registrado')
                associated_group, created_assoc = Group.objects.get_or_create(name='cliente')
                
                usuario.groups.remove(associated_group)
                usuario.groups.add(registered_group)
                messages.info(request, f'El usuario {usuario.email} ya no tiene clientes asignados. Su rol se ha cambiado a "usuario_registrado".')

        except Exception as e:
            messages.error(request, f'Error al eliminar la asociación: {e}')
        return redirect('clientes:listar_asociaciones')

    # --- LÓGICA DE FILTRADO ACTUALIZADA ---
    # Inicialmente, obtiene todas las asignaciones
    asignaciones = AsignacionCliente.objects.all().select_related('usuario', 'cliente')

    # Obtener los parámetros de filtro de la URL
    selected_user_id = request.GET.get('user_id')
    selected_cliente_id = request.GET.get('cliente_id')

    # Aplicar el filtro por usuario (por ID)
    if selected_user_id:
        try:
            user_id = int(selected_user_id)
            asignaciones = asignaciones.filter(usuario__id=user_id)
        except ValueError:
            pass # Ignorar si no es un ID válido

    # Aplicar el filtro por cliente (por ID)
    if selected_cliente_id:
        try:
            cliente_id = int(selected_cliente_id)
            asignaciones = asignaciones.filter(cliente__id=cliente_id)
        except ValueError:
            pass # Ignorar si no es un ID válido

    # Ordenar los resultados filtrados
    asignaciones = asignaciones.order_by('usuario__email', 'cliente__nombre_completo')
    # --- FIN DE LÓGICA DE FILTRADO ---
    
    # --- OBTENER DATOS PARA LOS FILTROS (SELECTS) ---
    # 1. Obtener la lista completa de usuarios (excluyendo superusuarios)
    all_users = User.objects.filter(is_superuser=False).order_by('email')
    # 2. Obtener la lista completa de clientes
    all_clientes = Cliente.objects.all().order_by('nombre_completo')
    
    # Se añade la información de los filtros y las listas al contexto
    context = {
        'asignaciones': asignaciones,
        # Variables de selección actual para mantener el valor seleccionado en el HTML
        'selected_user_id': selected_user_id,
        'selected_cliente_id': selected_cliente_id,
        # Listas para rellenar los selects
        'all_users': all_users,
        'all_clientes': all_clientes,
    }
    return render(request, 'asociar_a_usuario/lista_asociaciones.html', context)
