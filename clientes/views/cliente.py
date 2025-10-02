"""
Vistas para la gestión de clientes.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q

from clientes.models import Cliente, AsignacionCliente, Segmento
from clientes.forms import ClienteForm
import logging

logger = logging.getLogger(__name__)


class ClienteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Cliente
    template_name = "clientes/lista_clientes.html"
    context_object_name = "clientes"
    paginate_by = 20
    permission_required = "clientes.view_cliente"

    def get_queryset(self):
        qs = Cliente.objects.all().select_related("segmento")
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
        return context


class ClienteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/form.html"
    success_url = reverse_lazy("clientes:lista_clientes")
    permission_required = "clientes.change_cliente"


@login_required
@user_passes_test(lambda u: u.is_superuser)
def crear_cliente_view(request):
    """Vista para crear un nuevo cliente."""
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
def seleccionar_cliente_view(request):
    """Vista para seleccionar cliente activo."""
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

    return render(request, "seleccionar_cliente.html", {
        "clientes_asignados": clientes_asignados,
        "cliente_activo_id": cliente_activo_id,
    })