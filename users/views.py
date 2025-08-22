from django.shortcuts import render, redirect, get_object_or_404
from .models import Cliente
from .forms import ClienteForm

# vista para la lsita de clientes (READ)
def cliente_list(request):
    clientes = Cliente.objects.all()
    return render(request, 'users/cliente_list.html', {'clientes': clientes})

# vista para crear un nuevo cliente (CREATE)
def cliente_create(request):
    form = ClienteForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('cliente_list')
    return render(request, 'users/cliente_form.html', {'form': form, 'action': 'Crear'})

# vista para actualizar un cliente (UPDATE)
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente)
    if form.is_valid():
        form.save()
        return redirect('cliente_list')
    return render (request, 'users/cliente_form.html', {'form': form, 'action':'Actualizar'})

# vista para eliminar un cliente (DELETE)
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('cliente_list')
    return render(request,'users/cliente_confirm_delete.html', {'cliente':cliente})

