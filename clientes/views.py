from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, CreateView
#Restringir si no está logueado y no tiene los permisos
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages

from .models import Cliente, AsignacionCliente, Descuento, Segmento, HistorialDescuentos
from .forms import ClienteForm, DescuentoForm

# Asociar clientes-usuarios

User = get_user_model()

# Vista para asociar usuarios y clientes
@login_required
@user_passes_test(lambda u: u.is_staff)
def asociar_clientes_usuarios_view(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario')
        clientes_ids = request.POST.getlist('clientes')
        
        for cliente_id in clientes_ids:
            try:
                usuario = User.objects.get(id=usuario_id)
                cliente = Cliente.objects.get(id=cliente_id)
                
                if not AsignacionCliente.objects.filter(usuario=usuario, cliente=cliente).exists():
                    AsignacionCliente.objects.create(usuario=usuario, cliente=cliente)
                    messages.success(request, f'Se asoció el usuario {usuario.email} con el cliente {cliente.nombre_completo}.')
                else:
                    messages.info(request, f'La asociación entre {usuario.email} y {cliente.nombre_completo} ya existe.')
            except (User.DoesNotExist, Cliente.DoesNotExist):
                messages.error(request, 'Error: No se pudo encontrar el usuario o cliente.')
                return redirect('clientes:asociar_clientes_usuarios')

        return redirect('clientes:asociar_clientes_usuarios')

    usuarios = User.objects.filter(is_superuser=False)
    clientes = Cliente.objects.all()
    context = {
        'usuarios': usuarios,
        'clientes': clientes,
    }
    return render(request, 'asociar_a_usuario/asociar_clientes_usuarios.html', context)

# Vista para listar y eliminar asociaciones
@login_required
@user_passes_test(lambda u: u.is_staff)
def listar_asociaciones(request):
    if request.method == 'POST' and 'delete_id' in request.POST:
        try:
            asignacion_id = request.POST.get('delete_id')
            asignacion = get_object_or_404(AsignacionCliente, id=asignacion_id)
            asignacion.delete()
            messages.success(request, 'Asociación eliminada correctamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la asociación: {e}')
        return redirect('clientes:listar_asociaciones')

    asignaciones = AsignacionCliente.objects.all().order_by('usuario__email')
    context = {'asignaciones': asignaciones}
    return render(request, 'asociar_a_usuario/lista_descuentos.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def crear_cliente_view(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente creado correctamente.")
            return redirect('clientes:crear_cliente')
    else:
        form = ClienteForm()

    return render(request, 'crear_cliente.html', {'form': form})

"""
@login_required
def lista_clientes(request):
    return render(request, 'clientes/lista_clientes.html')
"""

from .models import Segmento

class ClienteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Cliente
    template_name = "clientes/lista_clientes.html"
    context_object_name = "clientes"
    paginate_by = 20
    permission_required = "clientes.view_cliente"

    def get_queryset(self):
        qs = Cliente.objects.all().select_related("segmento")

        # filtros
        tipo_cliente = self.request.GET.get("tipo_cliente")
        segmento_id = self.request.GET.get("segmento_id")

        if tipo_cliente:
            qs = qs.filter(tipo_cliente__iexact=tipo_cliente)
        if segmento_id:
            qs = qs.filter(segmento_id=segmento_id)

        return qs.order_by("nombre_completo")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segmentos"] = Segmento.objects.all()  # 👈 ahora se pasan al template
        return context



class ClienteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/form.html"
    success_url = reverse_lazy("clientes:lista_clientes")
    permission_required = "clientes.change_cliente"


# -------------------------------
# NUEVAS VISTAS PARA DESCUENTOS
# -------------------------------

@method_decorator(login_required, name='dispatch')
class DescuentoListView(UserPassesTestMixin, ListView):
    model = Descuento
    template_name = 'descuentos/lista_descuentos.html'
    context_object_name = 'descuentos'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_queryset(self):
        """
        Asegura que cada segmento tenga un registro de Descuento.
        """
        for segmento in Segmento.objects.all():
            Descuento.objects.get_or_create(
                segmento=segmento,
                defaults={'porcentaje_descuento': 0.00, 'modificado_por': self.request.user}
            )
        return Descuento.objects.all()


@method_decorator(login_required, name='dispatch')
class DescuentoUpdateView(UserPassesTestMixin, UpdateView):
    model = Descuento
    form_class = DescuentoForm
    template_name = 'descuentos/editar_descuento.html'
    success_url = reverse_lazy('clientes:lista_descuentos')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def form_valid(self, form):
        # Obtener valores anteriores
        pk = self.get_object().pk
        anterior = Descuento.objects.get(pk=pk)

        # Guardar normalmente
        response = super().form_valid(form)

        # Registrar en historial
        HistorialDescuentos.objects.create(
            descuento=self.object,
            porcentaje_descuento_anterior=anterior.porcentaje_descuento,
            porcentaje_descuento_nuevo=self.object.porcentaje_descuento,
            modificado_por=self.request.user
        )

        messages.success(self.request, f"Descuento para {self.object.segmento.name} actualizado correctamente.")

        return response


@method_decorator(login_required, name='dispatch')
class HistorialDescuentoListView(UserPassesTestMixin, ListView):
    model = HistorialDescuentos
    template_name = 'descuentos/historial_descuentos.html'
    context_object_name = 'historial_descuentos'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser