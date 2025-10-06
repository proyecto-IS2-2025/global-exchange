"""
Vistas para la gestión de clientes.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.conf import settings  # ✅ AGREGAR ESTA LÍNEA
from django.db.models import Q

from clientes.models import Cliente, AsignacionCliente, Segmento
from clientes.forms import ClienteForm
import logging
from roles.decorators import require_permission

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ✅ CORRECCIÓN: Validación manual en dispatch (sin decorador con lista)
# ═══════════════════════════════════════════════════════════════════════════
class ClienteListView(LoginRequiredMixin, ListView):
    """
    Vista para listar clientes.
    - Admin/Observador: Ve todos los clientes
    - Operador: Ve solo clientes asignados
    
    Requiere AL MENOS UNO de estos permisos:
    - clientes.view_all_clientes (ver todos)
    - clientes.view_assigned_clientes (ver asignados)
    """
    model = Cliente
    template_name = "clientes/lista_clientes.html"
    context_object_name = "clientes"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        """
        Validar permisos antes de procesar la vista.
        Usuario debe tener AL MENOS UNO de los permisos.
        """
        user = request.user
        
        # ✅ Bypass para superusuario en desarrollo
        if settings.DEBUG and user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        # ✅ Verificar si tiene alguno de los permisos necesarios
        tiene_permiso = (
            user.has_perm('clientes.view_all_clientes') or
            user.has_perm('clientes.view_assigned_clientes')
        )
        
        if not tiene_permiso:
            raise PermissionDenied(
                "No tienes permisos para ver clientes. "
                "Se requiere: clientes.view_all_clientes o clientes.view_assigned_clientes"
            )
        
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Filtra clientes según permisos del usuario.
        - Admin/Observador (view_all_clientes): Ve todos
        - Operador (view_assigned_clientes): Ve solo asignados
        """
        user = self.request.user
        qs = Cliente.objects.all().select_related("segmento")
        
        # ✅ Filtrar por asignación si NO tiene permiso global
        if not user.has_perm("clientes.view_all_clientes"):
            if user.has_perm("clientes.view_assigned_clientes"):
                qs = qs.filter(asignacioncliente__usuario=user).distinct()
            else:
                # Sin permisos (no debería llegar aquí por dispatch)
                return Cliente.objects.none()
        
        # Aplicar filtros de búsqueda
        tipo_cliente = self.request.GET.get("tipo_cliente")
        segmento_id = self.request.GET.get("segmento_id")

        if tipo_cliente:
            qs = qs.filter(tipo_cliente__iexact=tipo_cliente)
        if segmento_id:
            qs = qs.filter(segmento_id=segmento_id)

        return qs.order_by("nombre_completo")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segmentos"] = Segmento.objects.all()
        context["viewing_assigned_only"] = (
            not self.request.user.has_perm("clientes.view_all_clientes") and
            self.request.user.has_perm("clientes.view_assigned_clientes")
        )
        context["puede_crear_cliente"] = self.request.user.has_perm("clientes.add_cliente")
        context["puede_editar_cliente"] = self.request.user.has_perm("clientes.change_cliente")
        return context


# ═══════════════════════════════════════════════════════════════════════════
# ✅ CORRECTO: Usar change_cliente (permiso nativo)
# ═══════════════════════════════════════════════════════════════════════════
@method_decorator(
    require_permission("clientes.change_cliente"),
    name="dispatch"
)
class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar un cliente.
    Requiere permiso: clientes.change_cliente (permiso nativo de Django)
    """
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/form.html"
    success_url = reverse_lazy("clientes:lista_clientes")

    def form_valid(self, form):
        messages.success(self.request, "Cliente actualizado correctamente.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el cliente.")
        return super().form_invalid(form)


# ═══════════════════════════════════════════════════════════════════════════
# ✅ CORRECTO: Usar add_cliente (permiso nativo)
# ═══════════════════════════════════════════════════════════════════════════
@login_required
@require_permission("clientes.add_cliente")
def crear_cliente_view(request):
    """
    Vista para crear un nuevo cliente.
    Requiere permiso: clientes.add_cliente (permiso nativo de Django)
    """
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f"Cliente {cliente.nombre_completo} creado correctamente.")
            return redirect('clientes:lista_clientes')
        else:
            messages.error(request, "Error al crear el cliente. Verifica los datos ingresados.")
    else:
        form = ClienteForm()

    return render(request, 'clientes/crear_cliente.html', {'form': form})


# ═══════════════════════════════════════════════════════════════════════════
# ✅ CORRECTO: No requiere permisos especiales
# ═══════════════════════════════════════════════════════════════════════════
@login_required
def seleccionar_cliente_view(request):
    """
    Vista para seleccionar cliente activo.
    No requiere permisos especiales: cada usuario solo ve sus clientes asignados.
    """
    asignaciones = AsignacionCliente.objects.filter(
        usuario=request.user
    ).select_related("cliente__segmento")
    clientes_asignados = [a.cliente for a in asignaciones]

    cliente_activo_id = request.session.get("cliente_id")
    logger.debug(f"cliente_activo_id en sesión: {cliente_activo_id}")

    if request.method == "POST":
        cliente_id = request.POST.get("cliente_id")
        cliente = get_object_or_404(
            Cliente, 
            id=cliente_id, 
            asignacioncliente__usuario=request.user
        )
        request.session["cliente_id"] = cliente.id
        logger.debug(f"Nuevo cliente_id guardado en sesión: {cliente.id}")
        request.session.modified = True
        request.user.ultimo_cliente_id = cliente.id
        request.user.save(update_fields=["ultimo_cliente_id"])

        return redirect("inicio")

    return render(request, "clientes/seleccionar_cliente.html", {
        "clientes_asignados": clientes_asignados,
        "cliente_activo_id": cliente_activo_id,
    })