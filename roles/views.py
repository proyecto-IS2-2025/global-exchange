from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group, Permission
from django.http import JsonResponse
from .forms import GroupForm, PermissionForm
from django.contrib import messages
from django.contrib.auth import get_user_model

# Get the custom user model
CustomUser = get_user_model()

# Función auxiliar: solo admin
def is_admin(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_admin)
def group_list(request):
    groups = Group.objects.all()
    return render(request, 'groups/group_list.html', {'groups': groups})

@user_passes_test(is_admin)
def group_create(request):
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
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group.delete()
        return redirect('group_list')
    return render(request, 'groups/group_confirm_delete.html', {'group': group})

@user_passes_test(is_admin)
def group_detail_permissions(request, pk):
    group = get_object_or_404(Group, pk=pk)
    
    if request.method == 'POST':
        # El formulario ahora solo maneja el nombre del grupo
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            
        # Procesa los permisos enviados por la interfaz con la barra de búsqueda
        selected_permission_ids = request.POST.getlist('permissions')
        group.permissions.set(selected_permission_ids)
        
        return redirect('group_detail_permissions', pk=group.pk)
    
    else:
        form = GroupForm(instance=group)
        
    return render(request, 'groups/group_detail_permissions.html', {
        'group': group,
        'form': form,
        'current_permissions': group.permissions.all(),
    })

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
    query = request.GET.get('q', '')
    if query:
        permissions = Permission.objects.filter(codename__icontains=query)[:10]  # Limita los resultados
        data = [{'id': p.id, 'name': p.name, 'codename': p.codename} for p in permissions]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)

@user_passes_test(is_admin)
def search_users(request):
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