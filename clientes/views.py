from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator

from .models import Cliente
from .forms import ClienteForm

# Vistas para la gestión de clientes (Refactorizadas a CBV)
@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('users.view_cliente', raise_exception=True), name='dispatch')
class ClienteListView(ListView):
    model = Cliente
    template_name = 'users/cliente_list.html'
    context_object_name = 'clientes'

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('users.add_cliente', raise_exception=True), name='dispatch')
class ClienteCreateView(CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'users/cliente_form.html'
    success_url = reverse_lazy('cliente_list')

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('users.change_cliente', raise_exception=True), name='dispatch')
class ClienteUpdateView(UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'users/cliente_form.html'
    success_url = reverse_lazy('cliente_list')

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('users.delete_cliente', raise_exception=True), name='dispatch')
class ClienteDeleteView(DeleteView):
    model = Cliente
    template_name = 'users/cliente_confirm_delete.html'
    success_url = reverse_lazy('cliente_list')