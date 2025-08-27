# asociar_clientes_usuarios/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Cliente, AsignacionCliente

User = get_user_model()

@login_required
@user_passes_test(lambda u: u.is_staff)
def asociar_admin_view(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario')
        clientes_ids = request.POST.getlist('clientes')
        
        # Eliminar asignaciones existentes para este usuario
        AsignacionCliente.objects.filter(usuario_id=usuario_id).delete()
        
        # Crear nuevas asignaciones
        for cliente_id in clientes_ids:
            AsignacionCliente.objects.create(usuario_id=usuario_id, cliente_id=cliente_id)

        messages.success(request, 'Asociación de clientes actualizada correctamente.')
        return redirect('asociar_admin')  # Redirige a la misma página para ver el mensaje

    # Si es una solicitud GET
    usuarios = User.objects.all()
    clientes = Cliente.objects.all()
    context = {
        'usuarios': usuarios,
        'clientes': clientes,
    }
    return render(request, 'asociar_clientes_usuarios/admin_asociar.html', context)