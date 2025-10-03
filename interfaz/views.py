from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from users.models import CustomUser
from clientes.models import Cliente, Segmento, AsignacionCliente
from clientes.forms import ClienteForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from divisas.models import Divisa, TasaCambio
from django.db.models import OuterRef, Subquery
from divisas.services import ultimas_por_segmento
# interfaz/views.py
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

User = get_user_model()

def inicio(request):
    # Roles
    grupo_cliente = request.user.groups.filter(name="cliente").exists() if request.user.is_authenticated else False
    grupo_operador = request.user.groups.filter(name="operador").exists() if request.user.is_authenticated else False
    grupo_admin = request.user.groups.filter(name="admin").exists() if request.user.is_authenticated else False

    # ---------- detectar cliente en sesión / asignaciones ----------
    cliente_id = request.session.get("cliente_id")
    cliente_activo = None

    if cliente_id:
        try:
            cliente_activo = Cliente.objects.get(id=cliente_id, esta_activo=True)
        except Cliente.DoesNotExist:
            cliente_activo = None

    # Si no hay cliente en sesión, intentar auto-asignar si el usuario tiene una única asignación.
    if request.user.is_authenticated and cliente_activo is None:
        asignaciones = AsignacionCliente.objects.filter(usuario=request.user).select_related('cliente__segmento')
        if asignaciones.count() == 1:
            cliente_activo = asignaciones.first().cliente
            request.session['cliente_id'] = cliente_activo.id

    # Si aún no hay cliente, usamos segmento "general" (creamos si no existe)
    segmento_obj = None
    if cliente_activo and cliente_activo.segmento:
        segmento_obj = cliente_activo.segmento
    else:
        segmento_obj, _ = Segmento.objects.get_or_create(name="general")

    # ---------- construir divisas_data para la plantilla ----------
    divisas_activas = Divisa.objects.filter(is_active=True).order_by('code')
    divisas_data = []
    for divisa in divisas_activas:
        ultimas = ultimas_por_segmento(divisa)   # retorna queryset de CotizacionSegmento (últimas por segmento)
        cotizaciones = [c for c in ultimas if c.segmento_id == getattr(segmento_obj, 'id', None)]
        divisas_data.append({
            'divisa': divisa,
            'cotizaciones': cotizaciones
        })

    # también pasar lista de clientes asignados para que el usuario pueda elegir si tiene >1
    clientes_asignados = []
    if request.user.is_authenticated:
        clientes_asignados = [asig.cliente for asig in AsignacionCliente.objects.filter(usuario=request.user).select_related('cliente')]

    # ----------- CAMBIO: flag para alerta -----------
    mostrar_alerta_sin_clientes = (
        request.user.is_authenticated and len(clientes_asignados) == 0
    )

    context = {
        "grupo_cliente": grupo_cliente,
        "grupo_operador": grupo_operador,
        "grupo_admin": grupo_admin,
        "divisas_data": divisas_data,
        "segmento_activo": segmento_obj,
        "cliente_activo": cliente_activo,
        "clientes_asignados": clientes_asignados,
        "mostrar_alerta_sin_clientes": mostrar_alerta_sin_clientes,  # <--- CAMBIO
    }
    return render(request, "inicio.html", context)

def contacto(request):
    return render(request, 'contacto.html')


@login_required
def cliente_dashboard(request):
    return render(request, 'cliente/dashboard.html')

"""
#Redirect
@login_required
def redireccion_por_grupo(request):
    #Redirige al usuario según su grupo.
    #Como no hay dashboards específicos todavía, todos van a inicio.
    grupos = list(request.user.groups.values_list('name', flat=True))
    print("Grupos del usuario:", grupos)

    # Por ahora, todos los grupos redirigen a inicio
    # La página inicio ya maneja la lógica de mostrar contenido según el rol
    if grupos:
        return redirect('inicio')
    else:
        messages.warning(request, "Tu cuenta no tiene un grupo asignado.")
        return redirect('inicio')
"""

@login_required
def asociar_clientes_usuarios(request):
    return render(request, "admin/asociar_clientes_usuarios.html")
