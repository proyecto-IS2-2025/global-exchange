from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from clientes.decorators import require_permission
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

CustomUser = get_user_model()


# ═══════════════════════════════════════════════════════════════════
# VISTAS CRUD DE USUARIOS (SOLO ADMIN)
# ═══════════════════════════════════════════════════════════════════

@method_decorator(login_required, name='dispatch')
@method_decorator(
    require_permission('users.manage_usuarios', check_client_assignment=False),
    name='dispatch'
)
class CustomUserListView(ListView):
    """
    📋 Lista todos los usuarios del sistema
    
    Requiere: users.manage_usuarios
    Acceso: Solo administradores
    """
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        """Ordenar por fecha de creación (más reciente primero)"""
        return CustomUser.objects.all().order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_usuarios'] = CustomUser.objects.count()
        context['usuarios_activos'] = CustomUser.objects.filter(is_active=True).count()
        context['usuarios_staff'] = CustomUser.objects.filter(is_staff=True).count()
        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(
    require_permission('users.manage_usuarios', check_client_assignment=False),
    name='dispatch'
)
class CustomUserCreateView(CreateView):
    """
    ➕ Crea un nuevo usuario
    
    Requiere: users.manage_usuarios
    Acceso: Solo administradores
    """
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    
    def form_valid(self, form):
        """Validar que no se cree un superusuario sin permisos"""
        user = form.save(commit=False)
        
        # Solo superusuarios pueden crear superusuarios
        if user.is_superuser and not self.request.user.is_superuser:
            messages.error(
                self.request,
                "❌ No tienes permisos para crear superusuarios"
            )
            return self.form_invalid(form)
        
        user.save()
        form.save_m2m()  # Guardar grupos/permisos
        
        messages.success(
            self.request,
            f"✅ Usuario '{user.username}' creado exitosamente"
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            "❌ Error al crear usuario. Verifica los datos ingresados."
        )
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(
    require_permission('users.manage_usuarios', check_client_assignment=False),
    name='dispatch'
)
class CustomUserUpdateView(UpdateView):
    """
    ✏️  Edita un usuario existente
    
    Requiere: users.manage_usuarios
    Acceso: Solo administradores
    Restricción: No se puede editar superusuarios sin ser superusuario
    """
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Validar permisos antes de procesar"""
        user_to_edit = self.get_object()
        
        # No se puede editar superusuarios sin ser superusuario
        if user_to_edit.is_superuser and not request.user.is_superuser:
            messages.error(
                request,
                "❌ No tienes permisos para editar superusuarios"
            )
            return redirect('users:user_list')
        
        # No se puede editar la propia cuenta desde aquí
        if user_to_edit == request.user:
            messages.warning(
                request,
                "⚠️  Usa la vista de perfil para editar tu propia cuenta"
            )
            return redirect('users:perfil_usuario')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f"✅ Usuario '{form.instance.username}' actualizado correctamente"
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            "❌ Error al actualizar usuario. Verifica los datos."
        )
        return super().form_invalid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(
    require_permission('users.manage_usuarios', check_client_assignment=False),
    name='dispatch'
)
class CustomUserDeleteView(DeleteView):
    """
    🗑️  Elimina un usuario
    
    Requiere: users.manage_usuarios
    Acceso: Solo administradores
    Restricción: No se puede eliminar superusuarios ni la propia cuenta
    """
    model = CustomUser
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user_list')
    
    def dispatch(self, request, *args, **kwargs):
        """Validar restricciones antes de eliminar"""
        user_to_delete = self.get_object()
        
        # No se puede eliminar superusuarios
        if user_to_delete.is_superuser:
            messages.error(
                request,
                "❌ No se pueden eliminar superusuarios por seguridad"
            )
            return redirect('users:user_list')
        
        # No se puede eliminar la propia cuenta
        if user_to_delete == request.user:
            messages.error(
                request,
                "❌ No puedes eliminar tu propia cuenta"
            )
            return redirect('users:user_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Sobrescribir para agregar mensaje de confirmación"""
        user = self.get_object()
        username = user.username
        
        messages.success(
            request,
            f"✅ Usuario '{username}' eliminado correctamente"
        )
        return super().delete(request, *args, **kwargs)


# ═══════════════════════════════════════════════════════════════════
# VISTA DE PERFIL (CUALQUIER USUARIO AUTENTICADO)
# ═══════════════════════════════════════════════════════════════════

@login_required
def perfil_usuario(request):
    """
    👤 Perfil del usuario autenticado
    
    Permite que cualquier usuario vea y edite su propio perfil.
    Los campos editables se limitan según el rol del usuario.
    """
    user = request.user
    
    # Solo el usuario puede editar su propio perfil (no staff general)
    puede_editar = True  # Siempre puede editar su propio perfil
    
    if request.method == 'POST' and puede_editar:
        form = CustomUserChangeForm(request.POST, instance=user)
        
        # Validar que no se autoasigne permisos
        if 'is_staff' in form.changed_data and not user.is_superuser:
            messages.error(
                request,
                "❌ No puedes modificar tu estado de staff"
            )
            return redirect('users:perfil_usuario')
        
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Perfil actualizado correctamente")
            return redirect('users:perfil_usuario')
        else:
            messages.error(request, "❌ Error al actualizar perfil")
    else:
        form = CustomUserChangeForm(instance=user)
    
    # Información del rol
    grupo = user.groups.first().name if user.groups.exists() else "Sin grupo"
    
    # Cliente activo desde la sesión
    cliente_activo = None
    cliente_id = request.session.get("cliente_activo_id")
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
        "cliente_activo": cliente_activo,
        # Estadísticas adicionales
        "es_admin": user.groups.filter(name='admin').exists(),
        "es_operador": user.groups.filter(name='operador').exists(),
        "es_cliente": user.groups.filter(name='cliente').exists(),
    }
    
    return render(request, "perfil_usuario.html", context)

