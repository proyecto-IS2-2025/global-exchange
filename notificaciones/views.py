from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # Opcional: Para mostrar mensajes de éxito/error
from clientes.models import Cliente
from .models import Notificacion

# ASUMIMOS que estos modelos y forms están definidos en notificaciones/models.py y notificaciones/forms.py
from .models import NotificacionTasa, ConfiguracionGeneral
from .forms import NotificacionTasaForm, ConfiguracionGeneralForm


# VISTA PRINCIPAL (CBV)
class GestionNotificacionesView(LoginRequiredMixin, View):
    # Nota: Ajusta la ruta del template si es necesario (ej: 'notificaciones/gestion.html')
    template_name = 'gestion.html'

    def get_context_data(self, **kwargs):
        user = self.request.user

        # Lógica para Configuración General y Listado
        config_general, created = ConfiguracionGeneral.objects.get_or_create(usuario=user)
        form_general = ConfiguracionGeneralForm(instance=config_general)
        notificaciones = NotificacionTasa.objects.filter(usuario=user).order_by('-id')
        form_nueva_alerta = NotificacionTasaForm()

        return {
            'form_general': form_general,
            'notificaciones': notificaciones,
            'form_nueva_alerta': form_nueva_alerta,
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        user = request.user

        # 1. Lógica para guardar la CONFIGURACIÓN GENERAL
        if 'guardar_general' in request.POST:
            config_general = get_object_or_404(ConfiguracionGeneral, usuario=user)
            form_general = ConfiguracionGeneralForm(request.POST, instance=config_general)

            if form_general.is_valid():
                form_general.save()
                messages.success(request, "Configuración general guardada con éxito.")
            else:
                messages.error(request, "Error al guardar la configuración general.")

            return redirect('notificaciones:gestion_notificaciones')

        # 2. Lógica para guardar la NUEVA ALERTA
        elif 'guardar_alerta' in request.POST:

            # 1. OBTENER EL CONTEXTO NECESARIO
            cliente_id = request.session.get('cliente_id')
            if not cliente_id:
                # Manejo de error si no hay cliente en sesión
                messages.error(request, "Error: No se encontró el cliente activo en la sesión.")
                return redirect('notificaciones:gestion_notificaciones')

            cliente = get_object_or_404(Cliente, id=cliente_id, esta_activo=True)

            form_nueva_alerta = NotificacionTasaForm(request.POST)

            if form_nueva_alerta.is_valid():
                alerta = form_nueva_alerta.save(commit=False)

                # 2. INYECTAR LAS CLAVES FORÁNEAS FALTANTES
                alerta.usuario = request.user  # El usuario logueado
                alerta.cliente_asociado = cliente  # El cliente seleccionado en la sesión

                # 3. VALIDAR DUPLICADOS antes de guardar
                duplicados = NotificacionTasa.objects.filter(
                    usuario=request.user,
                    cliente_asociado=cliente,
                    divisa=alerta.divisa,
                    tipo_alerta=alerta.tipo_alerta,
                    tipo_operacion=alerta.tipo_operacion
                )
                
                # Si es umbral, también verificar condición y monto
                if alerta.tipo_alerta == 'umbral':
                    duplicados = duplicados.filter(
                        condicion_umbral=alerta.condicion_umbral,
                        monto_umbral=alerta.monto_umbral
                    )
                
                if duplicados.exists():
                    messages.error(request, "Ya existe una notificación idéntica con esta configuración.")
                    
                    # Obtenemos el contexto base
                    context = self.get_context_data()
                    
                    # Sobreescribimos el formulario limpio con la instancia que contiene el error
                    context['form_nueva_alerta'] = form_nueva_alerta
                    context['alerta_form_error'] = True
                    
                    return render(request, self.template_name, context)

                alerta.save()
                messages.success(request, "Nueva notificación creada con éxito.")

                return redirect('notificaciones:gestion_notificaciones')
            # Si el formulario de ALERTA FALLA la validación:
            else:
                messages.error(request, "Por favor, corrija los errores en la nueva notificación.")

                # Obtenemos el contexto base
                context = self.get_context_data()

                # Sobreescribimos el formulario limpio con la instancia que contiene errores
                context['form_nueva_alerta'] = form_nueva_alerta

                # Bandera para que el template reabra el modal y muestre los errores
                context['alerta_form_error'] = True

                # Re-renderizar la plantilla con los errores y el contexto completo
                return render(request, self.template_name, context)

        # 3. Redirección por defecto si la petición POST no fue reconocida (o si falló guardado general)
        return redirect('notificaciones:gestion_notificaciones')


# VISTAS DE ACCIÓN (FBVs)
@login_required
def toggle_notificacion(request, pk):
    """
    Invierte el estado (Activa/Inactiva) de una notificación específica.
    """
    alerta = get_object_or_404(NotificacionTasa, pk=pk, usuario=request.user)
    alerta.activa = not alerta.activa
    alerta.save()
    messages.info(request, f"La alerta de {alerta.divisa} ha sido {'ACTIVADA' if alerta.activa else 'DESACTIVADA'}.")
    return redirect('notificaciones:gestion_notificaciones')


@login_required
def eliminar_notificacion(request, pk):
    """
    Elimina una notificación específica del cliente.
    """
    if request.method == 'POST':
        alerta = get_object_or_404(NotificacionTasa, pk=pk, usuario=request.user)
        alerta.delete()
        messages.warning(request, f"Alerta de {alerta.divisa} eliminada con éxito.")
    return redirect('notificaciones:gestion_notificaciones')


@login_required
def editar_notificacion(request, pk):
    """
    Permite editar una notificación existente.
    No se puede editar notificaciones del tipo 'transaccion_cancelada'.
    """
    alerta = get_object_or_404(NotificacionTasa, pk=pk, usuario=request.user)
    
    # Prevenir edición de notificaciones auto-generadas
    if alerta.tipo_alerta == 'transaccion_cancelada':
        messages.error(request, "No se puede editar una notificación generada automáticamente.")
        return redirect('notificaciones:gestion_notificaciones')
    
    if request.method == 'POST':
        form = NotificacionTasaForm(request.POST, instance=alerta)
        if form.is_valid():
            form.save()
            messages.success(request, f"Alerta de {alerta.divisa} actualizada con éxito.")
            return redirect('notificaciones:gestion_notificaciones')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = NotificacionTasaForm(instance=alerta)
    
    return render(request, 'editar_notificacion.html', {
        'form': form,
        'alerta': alerta,
    })

from django.views.decorators.http import require_POST

@login_required
@require_POST
def marcar_leida(request, pk):
    """
    Marca una notificación como leída.
    Si es petición AJAX, retorna JSON. Si no, redirige.
    """
    from django.http import JsonResponse
    
    notif = get_object_or_404(Notificacion, id=pk, usuario=request.user)
    notif.estado_lectura = 'leida'
    notif.save()
    
    # Si es petición AJAX, retornar JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'status': 'success', 'message': 'Notificación marcada como leída'})
    
    # Si no es AJAX, redirigir (comportamiento anterior)
    return redirect(request.META.get('HTTP_REFERER', 'inicio'))

@login_required
@require_POST
def limpiar_todas(request):
    """
    Marca todas las notificaciones pendientes del usuario como leídas.
    Si es petición AJAX, retorna JSON. Si no, redirige.
    """
    from django.http import JsonResponse
    
    cantidad = Notificacion.objects.filter(
        usuario=request.user,
        estado_lectura='pendiente'
    ).update(estado_lectura='leida')
    
    # Si es petición AJAX, retornar JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'status': 'success', 'message': f'{cantidad} notificaciones limpiadas'})
    
    # Si no es AJAX, redirigir (comportamiento anterior)
    messages.success(request, "Todas las notificaciones han sido limpiadas.")
    return redirect(request.META.get('HTTP_REFERER', 'inicio'))

@login_required
def historial_notificaciones(request):
    """
    Vista para mostrar todas las notificaciones del usuario con filtros.
    Similar al panel de notificaciones de Jira.
    """
    from django.core.paginator import Paginator
    from datetime import datetime, timedelta
    from django.utils import timezone
    from django.db.models import Q
    
    # Obtener parámetros de filtrado
    filtro_estado = request.GET.get('estado', '')
    filtro_periodo = request.GET.get('periodo', '')
    
    # Query base
    notificaciones_qs = Notificacion.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    
    # Aplicar filtro por estado
    if filtro_estado == 'pendiente':
        notificaciones_qs = notificaciones_qs.filter(estado_lectura='pendiente')
    elif filtro_estado == 'leida':
        notificaciones_qs = notificaciones_qs.filter(estado_lectura='leida')
    
    # Aplicar filtro por período
    if filtro_periodo == 'hoy':
        # Obtener el inicio del día de hoy en la zona horaria LOCAL del servidor
        from django.utils.timezone import localtime
        ahora_local = localtime(timezone.now())
        hoy_inicio = ahora_local.replace(hour=0, minute=0, second=0, microsecond=0)
        notificaciones_qs = notificaciones_qs.filter(fecha_creacion__gte=hoy_inicio)
        
    elif filtro_periodo == 'semana':
        hace_semana = timezone.now() - timedelta(days=7)
        notificaciones_qs = notificaciones_qs.filter(fecha_creacion__gte=hace_semana)
    elif filtro_periodo == 'mes':
        hace_mes = timezone.now() - timedelta(days=30)
        notificaciones_qs = notificaciones_qs.filter(fecha_creacion__gte=hace_mes)
    
    # Contadores para el sidebar
    total_todas = Notificacion.objects.filter(usuario=request.user).count()
    total_pendientes = Notificacion.objects.filter(usuario=request.user, estado_lectura='pendiente').count()
    total_leidas = Notificacion.objects.filter(usuario=request.user, estado_lectura='leida').count()
    
    # Paginación
    paginator = Paginator(notificaciones_qs, 20)  # 20 notificaciones por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notificaciones': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'filtro_estado': filtro_estado,
        'filtro_periodo': filtro_periodo,
        'total_todas': total_todas,
        'total_pendientes': total_pendientes,
        'total_leidas': total_leidas,
    }
    
    return render(request, 'historial_notificaciones.html', context)

@login_required
@require_POST
def marcar_todas_leidas(request):
    """
    Marca todas las notificaciones del usuario como leídas.
    """
    cantidad = Notificacion.objects.filter(
        usuario=request.user,
        estado_lectura='pendiente'
    ).update(estado_lectura='leida')
    
    messages.success(request, f"{cantidad} notificaciones marcadas como leídas.")
    return redirect('notificaciones:historial')