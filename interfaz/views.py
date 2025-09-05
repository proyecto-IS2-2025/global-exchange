from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from users.models import CustomUser
from clientes.models import Cliente
from clientes.forms import ClienteForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from divisas.models import Divisa, TasaCambio
from django.db.models import OuterRef, Subquery

User = get_user_model()

def inicio(request):
    grupo_cliente = request.user.groups.filter(name="cliente").exists() if request.user.is_authenticated else False
    grupo_operador = request.user.groups.filter(name="operador").exists() if request.user.is_authenticated else False
    grupo_admin = request.user.groups.filter(name="admin").exists() if request.user.is_authenticated else False

    # Subquery: última fila (por fecha) de TasaCambio para cada divisa
    latest = TasaCambio.objects.filter(divisa=OuterRef('pk')).order_by('-fecha')

    divisas = (
        Divisa.objects
        .filter(is_active=True)
        .annotate(
            ultima_fecha=Subquery(latest.values('fecha')[:1]),
            ultima_compra=Subquery(latest.values('valor_compra')[:1]),
            ultima_venta=Subquery(latest.values('valor_venta')[:1]),
        )
        .order_by('code')
    )

    context = {
        "grupo_cliente": grupo_cliente,
        "grupo_operador": grupo_operador,
        "grupo_admin": grupo_admin,
        "divisas": divisas,  # 👈 acá agregamos las divisas
    }
    return render(request, "inicio.html", context)


def contacto(request):
    return render(request, 'contacto.html')


@login_required
def cliente_dashboard(request):
    return render(request, 'cliente/dashboard.html')


#Redirect
@login_required
def redireccion_por_grupo(request):
    grupos = list(request.user.groups.values_list('name', flat=True))
    print("Grupos del usuario:", grupos)  # Esto se verá en la consola del servidor

    if 'admin' in grupos:
        return redirect('admin_dashboard')
    elif 'operador' in grupos:
        return redirect('cambista_dashboard')
    elif 'cliente' in grupos:
        return redirect('cliente_dashboard')
    else:
        messages.warning(request, "Tu cuenta no tiene un grupo asignado.")
        return redirect('inicio')


@login_required
def asociar_clientes_usuarios(request):
    return render(request, "admin/asociar_clientes_usuarios.html")
