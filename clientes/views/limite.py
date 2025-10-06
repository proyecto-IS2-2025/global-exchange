"""
Vistas para gestión de límites diarios y mensuales.
VERSIÓN CORREGIDA - Sin select_related inválido
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, time

from clientes.models import LimiteDiario, LimiteMensual
from clientes.forms import LimiteDiarioForm, LimiteMensualForm
from roles.decorators import require_permission


@login_required
@require_permission("clientes.view_limites_operacion", check_client_assignment=False)
def lista_limites_diarios(request):
    """
    Lista todos los límites diarios del sistema.
    Requiere permiso: clientes.view_limites_operacion
    """
    limites = LimiteDiario.objects.all().order_by('-fecha')
    return render(request, "clientes/limites_diarios.html", {"limites": limites})


@login_required
@require_permission("clientes.view_limites_operacion", check_client_assignment=False)
def lista_limites_mensuales(request):
    """
    Lista todos los límites mensuales del sistema.
    Requiere permiso: clientes.view_limites_operacion
    """
    limites = LimiteMensual.objects.all().order_by('-mes', '-año')
    return render(request, "clientes/limites_mensuales.html", {"limites": limites})


@login_required
@require_permission("clientes.manage_limites_operacion", check_client_assignment=False)
def crear_limite_diario(request):
    """
    Crea un nuevo límite diario.
    Requiere permiso: clientes.manage_limites_operacion
    """
    if request.method == "POST":
        form = LimiteDiarioForm(request.POST)
        if form.is_valid():
            limite = form.save(commit=False)
            hoy = timezone.localdate()

            # Establecer inicio de vigencia
            if limite.fecha == hoy:
                limite.inicio_vigencia = timezone.now()
            else:
                limite.inicio_vigencia = datetime.combine(
                    limite.fecha,
                    time.min,
                    tzinfo=timezone.get_current_timezone()
                )

            limite.save()
            messages.success(request, "Límite diario creado correctamente.")
            return redirect("clientes:lista_limites_diarios")
        else:
            messages.error(request, "Error al crear el límite. Verifica los datos ingresados.")
    else:
        form = LimiteDiarioForm()
    
    return render(request, "clientes/crear_limite_diario.html", {"form": form})


@login_required
@require_permission("clientes.manage_limites_operacion", check_client_assignment=False)
def crear_limite_mensual(request):
    """
    Crea un nuevo límite mensual.
    Requiere permiso: clientes.manage_limites_operacion
    """
    if request.method == "POST":
        form = LimiteMensualForm(request.POST)
        if form.is_valid():
            limite = form.save()
            messages.success(request, "Límite mensual guardado correctamente.")
            return redirect("clientes:lista_limites_mensuales")
        else:
            messages.error(request, "Error al crear el límite mensual. Verifica los datos ingresados.")
    else:
        form = LimiteMensualForm()

    return render(request, "clientes/nuevo_limite_mensual.html", {"form": form})


@method_decorator(
    require_permission("clientes.manage_limites_operacion", check_client_assignment=False), 
    name="dispatch"
)
class LimiteDiarioUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar un límite diario existente.
    Requiere permiso: clientes.manage_limites_operacion
    """
    model = LimiteDiario
    form_class = LimiteDiarioForm 
    template_name = 'clientes/editar_limite_diario.html'
    success_url = reverse_lazy('clientes:lista_limites_diarios')

    def form_valid(self, form):
        messages.success(self.request, "Límite diario actualizado correctamente.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el límite diario.")
        return super().form_invalid(form)


@method_decorator(
    require_permission("clientes.manage_limites_operacion", check_client_assignment=False), 
    name="dispatch"
)
class LimiteMensualUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar un límite mensual existente.
    Requiere permiso: clientes.manage_limites_operacion
    """
    model = LimiteMensual
    form_class = LimiteMensualForm
    template_name = 'clientes/editar_limite_mensual.html'
    success_url = reverse_lazy('clientes:lista_limites_mensuales')

    def form_valid(self, form):
        messages.success(self.request, "Límite mensual actualizado correctamente.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el límite mensual.")
        return super().form_invalid(form)