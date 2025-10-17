"""
Vistas para gestión de límites diarios y mensuales.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, time

from clientes.models import LimiteDiario, LimiteMensual
from clientes.forms import LimiteDiarioForm, LimiteMensualForm


@login_required
def lista_limites_diarios(request):
    limites = LimiteDiario.objects.all()
    return render(request, "clientes/limites_diarios.html", {"limites": limites})


@login_required
def lista_limites_mensuales(request):
    limites = LimiteMensual.objects.all()
    return render(request, "clientes/limites_mensuales.html", {"limites": limites})


@login_required
def crear_limite_diario(request):
    if request.method == "POST":
        form = LimiteDiarioForm(request.POST)
        if form.is_valid():
            limite = form.save(commit=False)
            hoy = timezone.localdate()

            if limite.fecha == hoy:
                limite.inicio_vigencia = timezone.now()
            else:
                limite.inicio_vigencia = datetime.combine(
                    limite.fecha,
                    time.min,
                    tzinfo=timezone.get_current_timezone()
                )

            limite.save()
            return redirect("clientes:lista_limites_diarios")
    else:
        form = LimiteDiarioForm()
    return render(request, "clientes/crear_limite_diario.html", {"form": form})


@login_required
def crear_limite_mensual(request):
    if request.method == "POST":
        form = LimiteMensualForm(request.POST)
        if form.is_valid():
            limite = form.save()
            messages.success(request, "Límite mensual guardado correctamente.")
            return redirect("clientes:lista_limites_mensuales")
    else:
        form = LimiteMensualForm()

    return render(request, "clientes/nuevo_limite_mensual.html", {"form": form})


class LimiteDiarioUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = LimiteDiario
    form_class = LimiteDiarioForm 
    template_name = 'clientes/editar_limite_diario.html'
    success_url = reverse_lazy('clientes:lista_limites_diarios')

    def test_func(self):
        return self.request.user.is_staff


class LimiteMensualUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = LimiteMensual
    form_class = LimiteMensualForm
    template_name = 'clientes/editar_limite_mensual.html'
    success_url = reverse_lazy('clientes:lista_limites_mensuales')

    def test_func(self):
        return self.request.user.is_staff