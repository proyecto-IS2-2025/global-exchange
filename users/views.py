from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator

from .models import Segmento, CustomUser
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

