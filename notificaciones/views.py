"""
Vistas para el módulo de notificaciones.

Este módulo contiene todas las vistas necesarias para gestionar el sistema de
notificaciones de tasas de cambio. Incluye vistas para:
    - Configuración general de notificaciones por usuario
    - Creación, edición y eliminación de reglas de alerta
    - Activación/desactivación de alertas
    - Marcado de lectura de notificaciones individuales
    - Historial completo de notificaciones con filtros y paginación

Vistas principales:
    - GestionNotificacionesView: Vista principal de configuración (CBV)
    - toggle_notificacion: Activar/desactivar alerta
    - eliminar_notificacion: Eliminar alerta permanentemente
    - editar_notificacion: Editar alerta existente
    - marcar_leida: Marcar notificación individual como leída
    - limpiar_todas: Marcar todas las notificaciones como leídas
    - historial_notificaciones: Listado completo con filtros
    - marcar_todas_leidas: Marcar todas como leídas desde historial
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from clientes.models import Cliente
from .models import Notificacion
from .models import NotificacionTasa, ConfiguracionGeneral
from .forms import NotificacionTasaForm, ConfiguracionGeneralForm


class GestionNotificacionesView(LoginRequiredMixin, View):
    """
    Vista principal para gestión de notificaciones de tasas de cambio.

    Esta vista centraliza toda la configuración de notificaciones del usuario,
    permitiendo:
        - Configurar preferencias generales (activar/desactivar, canal)
        - Crear nuevas reglas de alerta
        - Ver listado de todas las alertas configuradas

    Maneja dos tipos de POST:
        - 'guardar_general': Guarda configuración general del usuario
        - 'guardar_alerta': Crea nueva regla de alerta con validación de duplicados

    :ivar template_name: Ruta de la plantilla HTML
    :type template_name: str
    """
    # Nota: Ajusta la ruta del template si es necesario (ej: 'notificaciones/gestion.html')
    template_name = 'gestion.html'

    def get_context_data(self, **kwargs):
        """
        Prepara el contexto necesario para renderizar la vista.

        Obtiene o crea la configuración general del usuario, prepara formularios
        y obtiene todas las notificaciones existentes del usuario ordenadas por ID.

        :param kwargs: Argumentos adicionales de contexto
        :return: Diccionario con el contexto para la plantilla
        :rtype: dict
        """
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
        """
        Maneja peticiones GET mostrando el formulario de configuración.

        :param request: Objeto de petición HTTP
        :return: Respuesta HTTP renderizada
        :rtype: HttpResponse
        """
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        """
        Maneja peticiones POST para guardar configuraciones o crear alertas.

        Procesa dos tipos de acciones según el botón presionado:
            - 'guardar_general': Actualiza la configuración general del usuario
            - 'guardar_alerta': Crea una nueva regla de alerta con validación de duplicados

        La creación de alertas incluye:
            - Validación de formulario
            - Asignación de usuario y cliente desde sesión
            - Validación de duplicados antes de guardar
            - Manejo de errores con re-renderizado del formulario

        :param request: Objeto de petición HTTP
        :return: Redirección o re-renderizado con errores
        :rtype: HttpResponse
        """
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


@login_required
def toggle_notificacion(request, pk):
    """
    Alterna el estado activo/inactivo de una regla de alerta.

    Cambia el campo 'activa' de True a False o viceversa. Una alerta inactiva
    no genera notificaciones hasta que se vuelva a activar.

    :param request: Objeto de petición HTTP
    :param pk: ID de la notificación a alternar
    :type pk: int
    :return: Redirección a la página de gestión de notificaciones
    :rtype: HttpResponseRedirect
    """
    alerta = get_object_or_404(NotificacionTasa, pk=pk, usuario=request.user)
    alerta.activa = not alerta.activa
    alerta.save()
    messages.info(request, f"La alerta de {alerta.divisa} ha sido {'ACTIVADA' if alerta.activa else 'DESACTIVADA'}.")
    return redirect('notificaciones:gestion_notificaciones')


@login_required
def eliminar_notificacion(request, pk):
    """
    Elimina permanentemente una regla de alerta.

    Solo procesa peticiones POST por seguridad. Elimina la regla de alerta
    del usuario especificado por el pk.

    :param request: Objeto de petición HTTP
    :param pk: ID de la notificación a eliminar
    :type pk: int
    :return: Redirección a la página de gestión de notificaciones
    :rtype: HttpResponseRedirect
    """
    if request.method == 'POST':
        alerta = get_object_or_404(NotificacionTasa, pk=pk, usuario=request.user)
        alerta.delete()
        messages.warning(request, f"Alerta de {alerta.divisa} eliminada con éxito.")
    return redirect('notificaciones:gestion_notificaciones')


@login_required
def editar_notificacion(request, pk):
    """
    Permite editar una regla de alerta existente.

    Muestra un formulario pre-poblado con los datos actuales de la alerta.
    No permite editar alertas del tipo 'transaccion_cancelada' ya que son
    generadas automáticamente por el sistema.

    :param request: Objeto de petición HTTP
    :param pk: ID de la notificación a editar
    :type pk: int
    :return: Renderizado del formulario o redirección tras guardar
    :rtype: HttpResponse
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
    Marca una notificación individual como leída.

    Cambia el estado de una notificación de 'pendiente' a 'leida'.
    Soporta peticiones AJAX (retorna JSON) y peticiones normales de navegador.

    :param request: Objeto de petición HTTP
    :param pk: ID de la notificación a marcar como leída
    :type pk: int
    :return: JSON si es AJAX, redirección si no
    :rtype: JsonResponse or HttpResponseRedirect
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

    Actualiza en bulk todas las notificaciones con estado 'pendiente' a 'leida'.
    Útil para limpiar el panel de notificaciones. Soporta peticiones AJAX.

    :param request: Objeto de petición HTTP
    :return: JSON con cantidad de notificaciones limpiadas si es AJAX, redirección si no
    :rtype: JsonResponse or HttpResponseRedirect
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
    Vista para mostrar el historial completo de notificaciones con filtros.

    Muestra todas las notificaciones del usuario con capacidades de filtrado
    por estado (pendiente/leída) y período (hoy/semana/mes), con paginación.
    Similar al panel de notificaciones de Jira.

    Filtros disponibles:
        - estado: 'pendiente', 'leida', o todas
        - periodo: 'hoy', 'semana', 'mes', o todas

    :param request: Objeto de petición HTTP
    :return: Página HTML renderizada con notificaciones paginadas y filtradas
    :rtype: HttpResponse
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
    Marca todas las notificaciones del usuario como leídas desde el historial.

    Actualiza en bulk todas las notificaciones con estado 'pendiente' a 'leida'.
    Muestra un mensaje con la cantidad de notificaciones marcadas.

    :param request: Objeto de petición HTTP
    :return: Redirección a la página de historial de notificaciones
    :rtype: HttpResponseRedirect
    """
    cantidad = Notificacion.objects.filter(
        usuario=request.user,
        estado_lectura='pendiente'
    ).update(estado_lectura='leida')
    
    messages.success(request, f"{cantidad} notificaciones marcadas como leídas.")
    return redirect('notificaciones:historial')