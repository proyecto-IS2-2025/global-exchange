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
                alerta.usuario = user  # El usuario logueado
                alerta.cliente_asociado = cliente  # El cliente seleccionado en la sesión

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

from django.views.decorators.http import require_POST

@login_required
@require_POST
def marcar_leida(request, pk):
    """
    Marca una notificación como leída y recarga la página.
    """
    notif = get_object_or_404(Notificacion, id=pk, usuario=request.user)
    notif.estado_lectura = 'leida'
    notif.save()
    return redirect(request.META.get('HTTP_REFERER', 'inicio'))