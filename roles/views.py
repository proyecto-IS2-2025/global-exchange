# users/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group
from django.http import JsonResponse
from .forms import GroupForm, PermissionForm
from django.contrib import messages
from .models import RoleStatus, PermissionMetadata # Importa el nuevo modelo
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models import Q, Value
from django.db.models.functions import Lower
from collections import defaultdict

# Get the custom user model
CustomUser = get_user_model()

# Función auxiliar: solo admin
def is_admin(user):
    """
    Verifica si un usuario es un administrador.

    :param user: El objeto de usuario a verificar.
    :type user: :class:`~django.contrib.auth.models.User`
    :return: `True` si el usuario tiene el estatus de staff o superusuario, `False` en caso contrario.
    :rtype: bool
    """
    return user.is_staff or user.is_superuser

@receiver(post_save, sender=Group)
def create_role_status(sender, instance, created, **kwargs):
    if created:
        RoleStatus.objects.create(group=instance)

@user_passes_test(is_admin)
def group_list(request):
    """
    Vista que muestra la lista de todos los grupos (roles) existentes.

    Solo accesible para usuarios con privilegios de administrador.

    :param request: Objeto de solicitud HTTP.
    :type request: :class:`~django.http.HttpRequest`
    :return: Un objeto de respuesta HTTP que renderiza la plantilla con la lista de grupos.
    :rtype: :class:`~django.http.HttpResponse`
    """
    groups = Group.objects.all()
    return render(request, 'groups/group_list.html', {'groups': groups})

@user_passes_test(is_admin)
def group_create(request):
    """
    Vista para crear un nuevo grupo (rol).

    Solo accesible para usuarios con privilegios de administrador.

    :param request: Objeto de solicitud HTTP.
    :type request: :class:`~django.http.HttpRequest`
    :return: Un objeto de respuesta HTTP que renderiza el formulario de creación o redirige a la lista de grupos.
    :rtype: :class:`~django.http.HttpResponse`
    """
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('group_list')
    else:
        form = GroupForm()
    return render(request, 'groups/group_form.html', {'form': form})

@user_passes_test(is_admin)
def group_update(request, pk):
    """
    Vista para actualizar un grupo (rol) existente.

    Solo accesible para usuarios con privilegios de administrador.

    :param request: Objeto de solicitud HTTP.
    :type request: :class:`~django.http.HttpRequest`
    :param pk: Clave primaria del grupo a actualizar.
    :type pk: int
    :return: Un objeto de respuesta HTTP que renderiza el formulario de actualización o redirige.
    :rtype: :class:`~django.http.HttpResponse`
    """
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect('group_list')
    else:
        form = GroupForm(instance=group)
    return render(request, 'groups/group_form.html', {'form': form})

@user_passes_test(is_admin)
def group_toggle_status(request, pk):
    """
    Vista para activar o desactivar un rol.
    """
    group = get_object_or_404(Group, pk=pk)
    # Crea el RoleStatus si no existe (por si se agregaron grupos antes de este cambio)
    status, created = RoleStatus.objects.get_or_create(group=group)
    status.is_active = not status.is_active
    status.save()

    messages.success(request, f"El rol '{group.name}' ha sido {'activado' if status.is_active else 'desactivado'}.")
    return redirect('group_list')

#Eliminar ya no utilizamos, solo usamos desactivate
@user_passes_test(is_admin)
def group_delete(request, pk):
    """
    Vista para eliminar un grupo (rol).

    Solo accesible para usuarios con privilegios de administrador.

    :param request: Objeto de solicitud HTTP.
    :type request: :class:`~django.http.HttpRequest`
    :param pk: Clave primaria del grupo a eliminar.
    :type pk: int
    :return: Un objeto de respuesta HTTP que redirige a la lista de grupos.
    :rtype: :class:`~django.http.HttpResponse`
    """
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group.delete()
        return redirect('group_list')
    return render(request, 'groups/group_confirm_delete.html', {'group': group})

@user_passes_test(is_admin)
# roles/views.py - MODIFICAR

@user_passes_test(is_admin)
def group_detail_permissions(request, pk):
    """
    Vista mejorada con permisos categorizados por módulo
    """
    group = get_object_or_404(Group, pk=pk)
    
    if request.method == 'POST':
        # Mantener lógica existente
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
        
        selected_permission_ids = request.POST.getlist('permissions')
        group.permissions.set(selected_permission_ids)
        
        messages.success(request, f'Permisos del rol "{group.name}" actualizados correctamente.')
        return redirect('group_detail_permissions', pk=group.pk)
    
    # NUEVO: Obtener permisos agrupados por módulo
    permisos_por_modulo = {}
    
    # Obtener permisos con metadata
    permisos_con_metadata = Permission.objects.select_related('metadata').filter(
        metadata__isnull=False
    ).order_by('metadata__modulo', 'metadata__orden')
    
    for permiso in permisos_con_metadata:
        modulo = permiso.metadata.modulo
        modulo_display = permiso.metadata.get_modulo_display()
        
        if modulo not in permisos_por_modulo:
            permisos_por_modulo[modulo] = {
                'nombre': modulo_display,
                'permisos': []
            }
        
        permisos_por_modulo[modulo]['permisos'].append({
            'id': permiso.id,
            'nombre': permiso.name,
            'codename': permiso.codename,
            'descripcion': permiso.metadata.descripcion_detallada,
            'ejemplo': permiso.metadata.ejemplo_uso,
            'nivel_riesgo': permiso.metadata.nivel_riesgo,
            'nivel_riesgo_display': permiso.metadata.get_nivel_riesgo_display(),
            'seleccionado': permiso in group.permissions.all()
        })
    
    # Permisos actuales
    permisos_actuales = group.permissions.all()
    
    context = {
        'group': group,
        'form': GroupForm(instance=group),
        'current_permissions': permisos_actuales,
        'permisos_por_modulo': permisos_por_modulo,
        'total_permisos': permisos_con_metadata.count(),
        'total_asignados': permisos_actuales.count(),
    }
    
    return render(request, 'groups/group_detail_permissions.html', context)

@user_passes_test(is_admin)
def group_detail_users(request, pk):
    group = get_object_or_404(Group, pk=pk)
    
    if request.method == 'POST':
        selected_user_ids = request.POST.getlist('users')
        users_to_add = CustomUser.objects.filter(id__in=selected_user_ids)
        group.user_set.set(users_to_add)
        messages.success(request, f"Usuarios del grupo '{group.name}' actualizados correctamente.")
        return redirect('group_detail_users', pk=group.pk)
    
    current_users = group.user_set.all()
    return render(request, 'groups/group_detail_users.html', {
        'group': group,
        'current_users': current_users,
    })

@user_passes_test(is_admin)
def search_permissions(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse([], safe=False)

    permisos = (
        Permission.objects.select_related('metadata')
        .filter(metadata__isnull=False)
        .filter(
            Q(name__icontains=query)
            | Q(codename__icontains=query)
            | Q(metadata__descripcion_detallada__icontains=query)
            | Q(metadata__ejemplo_uso__icontains=query)
        )
        .order_by('metadata__modulo', 'metadata__orden', 'name')[:20]
    )

    data = [
        {
            'id': p.id,
            'name': p.name,
            'codename': p.codename,
            'modulo': p.metadata.get_modulo_display() if p.metadata else '',
            'descripcion': p.metadata.descripcion_detallada if p.metadata else '',
            'ejemplo': p.metadata.ejemplo_uso if p.metadata else '',
        }
        for p in permisos
    ]
    return JsonResponse(data, safe=False)

@user_passes_test(is_admin)
def search_users(request):
    """
    Vista para buscar usuarios por nombre de usuario o email.

    Devuelve una lista de usuarios en formato JSON.
    Esta vista es utilizada por las llamadas AJAX.

    :param request: Objeto de solicitud HTTP con el parámetro GET 'q'.
    :type request: :class:`~django.http.HttpRequest`
    :return: Un objeto de respuesta JSON con una lista de usuarios.
    :rtype: :class:`~django.http.JsonResponse`
    """
    query = request.GET.get('q', '')
    if query:
        # Busca usuarios que coincidan con la consulta en el email
        users = CustomUser.objects.filter(email__icontains=query).distinct()
        data = [{'id': u.id, 'email': u.email, 'username': u.username} for u in users]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)

# Nueva vista para crear permisos
@user_passes_test(is_admin)
def permission_create(request):
    """
    Vista para crear un nuevo permiso.

    Solo accesible para usuarios con privilegios de administrador.
    Permite crear un permiso personalizado en la base de datos.

    :param request: Objeto de solicitud HTTP.
    :type request: :class:`~django.http.HttpRequest`
    :return: Un objeto de respuesta HTTP que renderiza el formulario o redirige.
    :rtype: :class:`~django.http.HttpResponse`
    """
    if request.method == 'POST':
        form = PermissionForm(request.POST)
        if form.is_valid():
            content_type = form.cleaned_data.get('content_type')
            codename = form.cleaned_data.get('codename')
            name = form.cleaned_data.get('name')
            
            # Crea el permiso
            Permission.objects.create(
                codename=codename,
                name=name,
                content_type=content_type,
            )
            messages.success(request, f"Permiso '{name}' creado exitosamente.")
            return redirect('permission_create')  # Redirige para limpiar el formulario
    else:
        form = PermissionForm()
    
    return render(request, 'permissions/permission_create.html', {'form': form})

@user_passes_test(is_admin)
def permission_matrix(request):
    module_filter = request.GET.get("module", "").strip()
    app_filter = request.GET.get("app", "").strip()
    search = request.GET.get("search", "").strip()

    permisos = (
        Permission.objects.select_related("metadata", "content_type")
        .filter(metadata__isnull=False)
        .order_by("metadata__modulo", "metadata__orden", "codename")
    )

    if module_filter:
        permisos = permisos.filter(metadata__modulo=module_filter)

    if app_filter:
        permisos = permisos.filter(content_type__app_label=app_filter)

    if search:
        permisos = permisos.filter(
            Q(name__icontains=search)
            | Q(codename__icontains=search)
            | Q(metadata__descripcion_detallada__icontains=search)
        )

    modules_qs = (
        PermissionMetadata.objects.order_by("modulo")
        .values_list("modulo", flat=True)
        .distinct()
    )
    modulo_choices_map = dict(PermissionMetadata._meta.get_field("modulo").choices)
    module_choices = [
        (value, modulo_choices_map.get(value, value.title()))
        for value in modules_qs
    ]

    apps = (
        permisos.values_list("content_type__app_label", flat=True)
        .distinct()
        .order_by("content_type__app_label")
    )

    matrix = []
    for perm in permisos:
        metadata = perm.metadata
        matrix.append(
            {
                "id": perm.id,
                "modulo": metadata.get_modulo_display(),
                "modulo_value": metadata.modulo,
                "app": perm.content_type.app_label,
                "modelo": perm.content_type.model,
                "codename": perm.codename,
                "nombre": perm.name,
                "riesgo": metadata.get_nivel_riesgo_display()
                if metadata.nivel_riesgo
                else "",
                "orden": metadata.orden,
                "descripcion": metadata.descripcion_detallada,
            }
        )

    grouped = defaultdict(list)
    for row in matrix:
        grouped[row["modulo"]].append(row)

    matrix_grouped = [
        {"modulo": modulo, "rows": rows, "count": len(rows)}
        for modulo, rows in sorted(grouped.items(), key=lambda item: item[0])
    ]

    context = {
        "group": None,
        "matrix": matrix,
        "matrix_grouped": matrix_grouped,
        "module_filter": module_filter,
        "modules": module_choices,
        "app_filter": app_filter,
        "apps": apps,
        "search": search,
        "total": len(matrix),
    }
    return render(request, "permissions/permission_matrix.html", context)