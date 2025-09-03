from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from .models import Divisa
from .forms import DivisaForm



def lista_divisas(request):
    divisas = Divisa.objects.all()
    return render(request, "divisas/lista.html", {"divisas": divisas})

def crear_divisa(request):
    if request.method == "POST":
        form = DivisaForm(request.POST)
        if form.is_valid():
            divisa = form.save(commit=False)
            divisa.estado = False  # por ejemplo: crear deshabilitada
            divisa.save()
            return redirect("divisas:lista")
    else:
        form = DivisaForm()
    return render(request, "divisas/form.html", {"form": form})



class DivisaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'divisas.view_divisa'
    model = Divisa
    template_name = 'divisas/lista.html'
    context_object_name = 'divisas'
    paginate_by = 20

class DivisaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'divisas.add_divisa'
    model = Divisa
    form_class = DivisaForm
    template_name = 'divisas/form.html'
    success_url = reverse_lazy('divisas:lista')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.is_active = False  # nace deshabilitada sí o sí
        obj.save()
        return redirect(self.success_url)

class DivisaToggleActivaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'divisas.change_divisa'
    def post(self, request, pk):
        divisa = get_object_or_404(Divisa, pk=pk)
        divisa.is_active = not divisa.is_active
        divisa.save()
        return redirect('divisas:lista')

class DivisaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'divisas.change_divisa'
    model = Divisa
    form_class = DivisaForm
    template_name = 'divisas/form.html'
    success_url = reverse_lazy('divisas:lista')
