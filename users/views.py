from django.shortcuts import render

# Create your views here.
# En tu_aplicacion/views.py
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    DeleteView
)

# Importa tu formulario de usuario personalizado
# (este formulario lo crearás en forms.py)
from .forms import CustomUserCreationForm

# Obtén el modelo de usuario personalizado
CustomUser = get_user_model()


class CustomUserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')
    permission_required = 'tu_aplicacion.add_customuser'  # Permiso requerido para crear usuarios


class CustomUserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'


class CustomUserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')
    permission_required = 'tu_aplicacion.change_customuser' # Permiso para editar


class CustomUserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = CustomUser
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')
    permission_required = 'tu_aplicacion.delete_customuser' # Permiso para eliminar

