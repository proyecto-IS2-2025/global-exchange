from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from .forms import CustomUserChangeForm

from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

# Obtén el modelo de usuario personalizado
CustomUser = get_user_model()

# Vistas para la gestión de usuarios
@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('users.view_customuser', raise_exception=True), name='dispatch')
class CustomUserListView(ListView):
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('users.add_customuser', raise_exception=True), name='dispatch')
class CustomUserCreateView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('users.change_customuser', raise_exception=True), name='dispatch')
class CustomUserUpdateView(UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('users.delete_customuser', raise_exception=True), name='dispatch')
class CustomUserDeleteView(DeleteView):
    model = CustomUser
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')


#Vista de perfil con edición opcional
@login_required
def perfil_usuario(request):
    user = request.user
    puede_editar = user.is_staff or user.is_cambista

    if request.method == 'POST' and puede_editar:
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('users:perfil_usuario')
    else:
        form = CustomUserChangeForm(instance=user)

    # Grupo y rol
    grupo = user.groups.first().name if user.groups.exists() else "Sin grupo"
    rol = getattr(user, 'role', None)
    rol_nombre = rol.name if rol else "Sin rol"

    # Cliente activo desde la sesión
    cliente_activo = None
    cliente_id = request.session.get("cliente_id")
    if cliente_id:
        from clientes.models import Cliente
        try:
            cliente_activo = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            cliente_activo = None

    context = {
        "form": form,
        "puede_editar": puede_editar,
        "user": user,
        "grupo": grupo,
        "rol": rol_nombre,
        "cliente_activo": cliente_activo,
    }
    return render(request, "perfil_usuario.html", context)

