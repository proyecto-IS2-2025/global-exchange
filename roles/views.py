from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group
from .forms import GroupForm

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
def group_detail(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == "POST":
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            group = form.save()  # guarda name + permisos
            # 👇 actualizar los usuarios
            group.user_set.set(form.cleaned_data['users'])
            group.save()
            return redirect('group_detail', pk=group.pk)  # refresca interfaz
    else:
        form = GroupForm(instance=group)

    return render(request, "groups/group_detail.html", {
        "group": group,
        "form": form
    })