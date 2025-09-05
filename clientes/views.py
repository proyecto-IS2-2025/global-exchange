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

from .models import Cliente, AsignacionCliente, Comision, Segmento, HistorialComision
from .forms import ClienteForm, ComisionForm

# Asociar clientes-usuarios

User = get_user_model()

# Vista para asociar usuarios y clientes
@login_required
@user_passes_test(lambda u: u.is_staff)
def asociar_clientes_usuarios_view(request):
    """
    Vista para asociar clientes a usuarios del sistema.

    Solo accesible para usuarios de tipo staff. Permite a un usuario con los
    permisos adecuados asignar clientes a otros usuarios.

    :param request: Objeto de solicitud HTTP.
    :type request: django.http.HttpRequest
    :return: Redirección a la URL 'clientes:asociar_clientes_usuarios' o renderiza el formulario.
    :rtype: django.http.HttpResponse
    """
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
    """
    Vista para listar y eliminar asociaciones de clientes con usuarios.

    Permite a los usuarios de tipo staff ver una lista de todas las
    asignaciones existentes y eliminarlas si es necesario.

    :param request: Objeto de solicitud HTTP.
    :type request: django.http.HttpRequest
    :return: Redirección a la URL 'clientes:listar_asociaciones' o renderiza la lista de asignaciones.
    :rtype: django.http.HttpResponse
    """
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
    return render(request, 'asociar_a_usuario/lista_asociaciones.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def crear_cliente_view(request):
    """
    Vista para crear un nuevo cliente.

    Solo accesible para superusuarios. Maneja la lógica de validación
    y guardado del formulario de creación de clientes.

    :param request: Objeto de solicitud HTTP.
    :type request: django.http.HttpRequest
    :return: Redirección a la URL 'clientes:crear_cliente' o renderiza el formulario.
    :rtype: django.http.HttpResponse
    """
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente creado correctamente.")
            return redirect('clientes:crear_cliente')
    else:
        form = ClienteForm()

    return render(request, 'crear_cliente.html', {'form': form})


@login_required
def lista_clientes(request):
    """
    Vista para listar los clientes asignados a un usuario.

    Solo los usuarios autenticados pueden acceder a esta vista. Muestra los
    clientes que han sido asignados al usuario actual.
    
    :param request: Objeto de solicitud HTTP.
    :type request: django.http.HttpRequest
    :return: Renderiza la lista de clientes del usuario.
    :rtype: django.http.HttpResponse
    """
    return render(request, 'clientes/lista_clientes.html')


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
    permission_required = "clientes.change_cliente"# Nuevas vistas para la gestión de comisiones
@method_decorator(login_required, name='dispatch')
class ComisionListView(UserPassesTestMixin, ListView):
    model = Comision
    template_name = 'comisiones/lista_comisiones.html'
    context_object_name = 'comisiones'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for segmento in Segmento.objects.all():
            Comision.objects.get_or_create(
                segmento=segmento,
                defaults={'valor_compra': 0.0, 'valor_venta': 0.0}
            )
        return context

@method_decorator(login_required, name='dispatch')
class ComisionUpdateView(UserPassesTestMixin, UpdateView):
    model = Comision
    form_class = ComisionForm
    template_name = 'comisiones/editar_comision.html'
    success_url = reverse_lazy('clientes:lista_comisiones')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def form_valid(self, form):
        # 1. Obtener los valores del objeto ANTES de guardar el formulario.
        #    'self.object' es el objeto que se está editando, con los valores originales.
            # 1. Obtener una copia de la instancia actual desde la BD para asegurar
            #    que leemos los valores anteriores exactamente como están persistidos.
            pk = self.get_object().pk
            anterior = Comision.objects.get(pk=pk)

            # 2. Dejar que la vista haga el guardado normal (super().form_valid) y
            #    así `self.object` quedará con los nuevos valores.
            response = super().form_valid(form)

            # 3. Crear el registro en el historial usando los valores leídos antes
            #    y los valores actuales ya guardados en `self.object`.
            HistorialComision.objects.create(
                comision=self.object,
                valor_compra_anterior=anterior.valor_compra,
                valor_venta_anterior=anterior.valor_venta,
                valor_compra_nuevo=self.object.valor_compra,
                valor_venta_nuevo=self.object.valor_venta,
                modificado_por=self.request.user
            )

            messages.success(self.request, f"Comisión para {self.object.segmento.name} actualizada correctamente.")

            return response


@method_decorator(login_required, name='dispatch')
class HistorialComisionListView(UserPassesTestMixin, ListView):
    model = HistorialComision
    template_name = 'comisiones/historial_comisiones.html'
    context_object_name = 'historial_comisiones'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser