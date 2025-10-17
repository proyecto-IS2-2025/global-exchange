from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from roles.decorators import require_permission
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
def perfil_usuario_view(request):
    """
    👤 Perfil del usuario autenticado
    
    ✅ NO pasa contexto - Django automáticamente aplica los context processors
    que inyectan: cliente_activo, tipo_usuario, permisos_clave, etc.
    """
    # ✅ IMPORTANTE: NO pasar contexto para que los context processors funcionen
    return render(request, 'perfil_usuario.html')

