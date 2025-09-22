from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, CreateView
#Restringir si no está logueado y no tiene los permisos
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth.models import Group

from .models import Cliente, AsignacionCliente, Descuento, Segmento, HistorialDescuentos
from .forms import ClienteForm, DescuentoForm

# Asociar clientes-usuarios

User = get_user_model()

# Vista para asociar usuarios y clientes
@login_required
@user_passes_test(lambda u: u.is_staff)
def asociar_clientes_usuarios_view(request):
    """
    Vista para asociar clientes a usuarios del sistema.

    Solo accesible para usuarios de tipo staff. Permite a un usuario con los
    permisos adecuados asignar clientes a otros usuarios.

    :param request: Objeto de solicitud HTTP.
    :type request: django.http.HttpRequest
    :return: Redirección a la URL 'clientes:asociar_clientes_usuarios' o renderiza el formulario.
    :rtype: django.http.HttpResponse
    """
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario')
        clientes_ids = request.POST.getlist('clientes')
        
         # Obtener el usuario y los grupos
        usuario = get_object_or_404(User, id=usuario_id)
        registered_group, created_reg = Group.objects.get_or_create(name='usuario_registrado')
        associated_group, created_assoc = Group.objects.get_or_create(name='cliente')
        
        for cliente_id in clientes_ids:
            try:
                usuario = User.objects.get(id=usuario_id)
                cliente = Cliente.objects.get(id=cliente_id)
                
                if not AsignacionCliente.objects.filter(usuario=usuario, cliente=cliente).exists():
                    AsignacionCliente.objects.create(usuario=usuario, cliente=cliente)
                    messages.success(request, f'Se asoció el usuario {usuario.email} con el cliente {cliente.nombre_completo}.')
                else:
                    messages.info(request, f'La asociación entre {usuario.email} y {cliente.nombre_completo} ya existe.')
            except (User.DoesNotExist, Cliente.DoesNotExist):
                messages.error(request, 'Error: No se pudo encontrar el usuario o cliente.')
                return redirect('clientes:asociar_clientes_usuarios')
            
        # Lógica para cambiar el grupo del usuario
        # Si tiene asignaciones, se convierte en 'cliente'
        if AsignacionCliente.objects.filter(usuario=usuario).exists():
            usuario.groups.add(associated_group)
            usuario.groups.remove(registered_group)

        return redirect('clientes:asociar_clientes_usuarios')

    usuarios = User.objects.filter(is_superuser=False)
    clientes = Cliente.objects.all()
    context = {
        'usuarios': usuarios,
        'clientes': clientes,
    }
    return render(request, 'asociar_a_usuario/asociar_clientes_usuarios.html', context)

# Vista para listar y eliminar asociaciones
@login_required
@user_passes_test(lambda u: u.is_staff)
def listar_asociaciones(request):
    """
    Vista para listar y eliminar asociaciones de clientes con usuarios.

    Permite a los usuarios de tipo staff ver una lista de todas las
    asignaciones existentes y eliminarlas si es necesario.

    :param request: Objeto de solicitud HTTP.
    :type request: django.http.HttpRequest
    :return: Redirección a la URL 'clientes:listar_asociaciones' o renderiza la lista de asignaciones.
    :rtype: django.http.HttpResponse
    """
    if request.method == 'POST' and 'delete_id' in request.POST:
        try:
            asignacion_id = request.POST.get('delete_id')
            asignacion = get_object_or_404(AsignacionCliente, id=asignacion_id)
            
            # Guarda el usuario antes de eliminar la asignación
            usuario = asignacion.usuario
            
            # Elimina la asignación
            asignacion.delete()
            messages.success(request, 'Asociación eliminada correctamente.')

            # Verifica si al usuario le quedan clientes asignados
            if not AsignacionCliente.objects.filter(usuario=usuario).exists():
                # Si no tiene más asignaciones, cambia su grupo
                registered_group, created_reg = Group.objects.get_or_create(name='usuario_registrado')
                associated_group, created_assoc = Group.objects.get_or_create(name='cliente')
                
                usuario.groups.remove(associated_group)
                usuario.groups.add(registered_group)
                messages.info(request, f'El usuario {usuario.email} ya no tiene clientes asignados. Su rol se ha cambiado a "usuario_registrado".')

        except Exception as e:
            messages.error(request, f'Error al eliminar la asociación: {e}')
        return redirect('clientes:listar_asociaciones')

    asignaciones = AsignacionCliente.objects.all().order_by('usuario__email')
    context = {'asignaciones': asignaciones}
    return render(request, 'asociar_a_usuario/lista_asociaciones.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def crear_cliente_view(request):
    """
    Vista para crear un nuevo cliente.

    Solo accesible para superusuarios. Maneja la lógica de validación
    y guardado del formulario de creación de clientes.

    :param request: Objeto de solicitud HTTP.
    :type request: django.http.HttpRequest
    :return: Redirección a la URL 'clientes:crear_cliente' o renderiza el formulario.
    :rtype: django.http.HttpResponse
    """
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
def lista_clientes(request):
    """
    Vista para listar los clientes asignados a un usuario.

    Solo los usuarios autenticados pueden acceder a esta vista. Muestra los
    clientes que han sido asignados al usuario actual.
    
    :param request: Objeto de solicitud HTTP.
    :type request: django.http.HttpRequest
    :return: Renderiza la lista de clientes del usuario.
    :rtype: django.http.HttpResponse
    """
    return render(request, 'clientes/lista_clientes.html')


from .models import Segmento

class ClienteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Cliente
    template_name = "clientes/lista_clientes.html"
    context_object_name = "clientes"
    paginate_by = 20
    permission_required = "clientes.view_cliente"

    def get_queryset(self):
        qs = Cliente.objects.all().select_related("segmento")

        # filtros
        tipo_cliente = self.request.GET.get("tipo_cliente")
        segmento_id = self.request.GET.get("segmento_id")

        if tipo_cliente:
            qs = qs.filter(tipo_cliente__iexact=tipo_cliente)
        if segmento_id:
            qs = qs.filter(segmento_id=segmento_id)

        return qs.order_by("nombre_completo")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["segmentos"] = Segmento.objects.all()  # 👈 ahora se pasan al template
        return context



class ClienteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/form.html"
    success_url = reverse_lazy("clientes:lista_clientes")
    permission_required = "clientes.change_cliente"


# -------------------------------
# NUEVAS VISTAS PARA DESCUENTOS
# -------------------------------

@method_decorator(login_required, name='dispatch')
class DescuentoListView(UserPassesTestMixin, ListView):
    model = Descuento
    template_name = 'descuentos/lista_descuentos.html'
    context_object_name = 'descuentos'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_queryset(self):
        """
        Asegura que cada segmento tenga un registro de Descuento.
        """
        for segmento in Segmento.objects.all():
            Descuento.objects.get_or_create(
                segmento=segmento,
                defaults={'porcentaje_descuento': 0.00, 'modificado_por': self.request.user}
            )
        return Descuento.objects.all()


@method_decorator(login_required, name='dispatch')
class DescuentoUpdateView(UserPassesTestMixin, UpdateView):
    model = Descuento
    form_class = DescuentoForm
    template_name = 'descuentos/editar_descuento.html'
    success_url = reverse_lazy('clientes:lista_descuentos')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def form_valid(self, form):
        anterior_descuento = self.get_object().porcentaje_descuento
        #print("DEBUG >>> valor anterior:", anterior_descuento)

        response = super().form_valid(form)

        #print("DEBUG >>> valor nuevo:", self.object.porcentaje_descuento)

        if anterior_descuento != self.object.porcentaje_descuento:
            HistorialDescuentos.objects.create(
                descuento=self.object,
                porcentaje_descuento_anterior=anterior_descuento,
                porcentaje_descuento_nuevo=self.object.porcentaje_descuento,
                modificado_por=self.request.user
            )
            #print("DEBUG >>> historial creado")

        return response


@method_decorator(login_required, name='dispatch')
class HistorialDescuentoListView(UserPassesTestMixin, ListView):
    model = HistorialDescuentos
    template_name = 'descuentos/historial_descuentos.html'
    context_object_name = 'historial_descuentos'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
#Seleccionar Cliente
# En seleccionar_cliente_view
import logging
logger = logging.getLogger(__name__)

@login_required
def seleccionar_cliente_view(request):
    asignaciones = AsignacionCliente.objects.filter(usuario=request.user).select_related("cliente__segmento")
    clientes_asignados = [a.cliente for a in asignaciones]

    cliente_activo_id = request.session.get("cliente_id")
    logger.debug(f"cliente_activo_id en sesión: {cliente_activo_id}")

    if request.method == "POST":
        cliente_id = request.POST.get("cliente_id")
        cliente = get_object_or_404(Cliente, id=cliente_id, asignacioncliente__usuario=request.user)
        request.session["cliente_id"] = cliente.id

        # Log para verificar que se guarda correctamente
        logger.debug(f"Nuevo cliente_id guardado en sesión: {cliente.id}")
    
        request.session.modified = True
        request.user.ultimo_cliente_id = cliente.id
        request.user.save(update_fields=["ultimo_cliente_id"])

        return redirect("inicio")

    return render(request, "seleccionar_cliente.html", {
        "clientes_asignados": clientes_asignados,
        "cliente_activo_id": cliente_activo_id,
    })






# clientes/views.py - Mejoras para medios de pago
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db.models import Count, Q

from medios_pago.models import MedioDePago
from .models import Cliente, ClienteMedioDePago, HistorialClienteMedioDePago, AsignacionCliente
from .forms import ClienteMedioDePagoCompleteForm, SelectMedioDePagoForm

import logging
logger = logging.getLogger(__name__)


def get_cliente_activo(request):
    """
    Función helper para obtener el cliente activo de la sesión
    """
    cliente_id = request.session.get('cliente_activo_id') or request.session.get('cliente_id')
    if not cliente_id:
        return None
    
    try:
        return Cliente.objects.get(
            id=cliente_id,
            asignacioncliente__usuario=request.user,
            esta_activo=True
        )
    except Cliente.DoesNotExist:
        # Limpiar sesión si el cliente ya no es válido
        request.session.pop('cliente_activo_id', None)
        request.session.pop('cliente_id', None)
        return None


class ClienteMedioDePagoListView(LoginRequiredMixin, ListView):
    """
    Vista mejorada para listar los medios de pago asociados al cliente activo
    """
    model = ClienteMedioDePago
    template_name = 'clientes/medios_pago/lista_medios_pago.html'
    context_object_name = 'medios_pago'
    paginate_by = 12

    def dispatch(self, request, *args, **kwargs):
        """Verificar que hay un cliente activo antes de proceder"""
        self.cliente = get_cliente_activo(request)
        if not self.cliente:
            messages.warning(
                request, 
                'Debe seleccionar un cliente para gestionar medios de pago.'
            )
            return redirect('clientes:seleccionar_cliente')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Filtrar medios de pago por cliente activo con optimizaciones"""
        queryset = ClienteMedioDePago.objects.filter(
            cliente=self.cliente
        ).select_related('medio_de_pago', 'creado_por').prefetch_related(
            'medio_de_pago__campos'
        )
        
        # Filtros opcionales
        estado = self.request.GET.get('estado')
        if estado == 'activos':
            queryset = queryset.filter(es_activo=True)
        elif estado == 'inactivos':
            queryset = queryset.filter(es_activo=False)
        
        tipo_medio = self.request.GET.get('tipo_medio')
        if tipo_medio:
            queryset = queryset.filter(medio_de_pago_id=tipo_medio)
            
        return queryset.order_by('-es_principal', '-fecha_actualizacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cliente'] = self.cliente
        
        # Estadísticas
        total_medios = self.get_queryset().count()
        medios_activos = self.get_queryset().filter(es_activo=True).count()
        medio_principal = self.get_queryset().filter(es_principal=True).first()
        
        context['stats'] = {
            'total': total_medios,
            'activos': medios_activos,
            'inactivos': total_medios - medios_activos,
            'principal': medio_principal
        }
        
        # Información adicional para filtros
        context['medios_disponibles'] = MedioDePago.objects.filter(
            is_active=True
        ).values('id', 'nombre')
        
        context['filtro_actual'] = {
            'estado': self.request.GET.get('estado', 'todos'),
            'tipo_medio': self.request.GET.get('tipo_medio', '')
        }
        
        return context


@login_required
def select_medio_pago_view(request):
    """
    Vista mejorada para seleccionar el tipo de medio de pago antes de agregar
    """
    cliente = get_cliente_activo(request)
    if not cliente:
        messages.warning(request, 'Debe seleccionar un cliente primero.')
        return redirect('clientes:seleccionar_cliente')

    if request.method == 'POST':
        form = SelectMedioDePagoForm(cliente=cliente, data=request.POST)
        if form.is_valid():
            medio_de_pago = form.cleaned_data['medio_de_pago']
            return redirect('clientes:agregar_medio_pago', medio_id=medio_de_pago.id)
        else:
            messages.error(request, 'Por favor, seleccione un medio de pago válido.')
    else:
        form = SelectMedioDePagoForm(cliente=cliente)

    # Verificar si quedan medios por asociar
    medios_disponibles = form.fields['medio_de_pago'].queryset
    if not medios_disponibles.exists():
        messages.info(
            request, 
            'Ya tiene todos los medios de pago disponibles asociados a este cliente.'
        )
        return redirect('clientes:medios_pago_cliente')

    return render(request, 'clientes/medios_pago/seleccionar_medio.html', {
        'form': form,
        'cliente': cliente,
        'medios_disponibles': medios_disponibles
    })


class ClienteMedioDePagoCreateView(LoginRequiredMixin, CreateView):
    """
    Vista mejorada para crear un nuevo medio de pago para el cliente
    """
    model = ClienteMedioDePago
    form_class = ClienteMedioDePagoCompleteForm
    template_name = 'clientes/medios_pago/form_medio_pago.html'

    def dispatch(self, request, *args, **kwargs):
        """Verificar cliente y medio de pago antes de proceder"""
        self.cliente = get_cliente_activo(request)
        if not self.cliente:
            messages.warning(request, 'Debe seleccionar un cliente primero.')
            return redirect('clientes:seleccionar_cliente')
            
        # Obtener y validar medio de pago
        medio_id = self.kwargs.get('medio_id')
        try:
            self.medio_de_pago = MedioDePago.objects.get(id=medio_id, is_active=True)
        except MedioDePago.DoesNotExist:
            messages.error(request, 'Medio de pago no encontrado o inactivo.')
            return redirect('clientes:seleccionar_medio_pago')
            
        # Verificar que no esté ya asociado
        if ClienteMedioDePago.objects.filter(
            cliente=self.cliente, 
            medio_de_pago=self.medio_de_pago
        ).exists():
            messages.warning(
                request, 
                f'El medio de pago "{self.medio_de_pago.nombre}" ya está asociado a este cliente.'
            )
            return redirect('clientes:medios_pago_cliente')
            
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['cliente'] = self.cliente
        kwargs['medio_de_pago'] = self.medio_de_pago
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'cliente': self.cliente,
            'medio_de_pago': self.medio_de_pago,
            'action': 'Agregar',
            'campos': self.medio_de_pago.campos.all().order_by('orden', 'id'),
            'breadcrumb': [
                {'name': 'Medios de Pago', 'url': 'clientes:medios_pago_cliente'},
                {'name': 'Seleccionar Medio', 'url': 'clientes:seleccionar_medio_pago'},
                {'name': f'Agregar {self.medio_de_pago.nombre}', 'active': True}
            ]
        })
        return context

    def form_valid(self, form):
        """Procesar formulario válido con manejo de errores mejorado"""
        try:
            with transaction.atomic():
                form.instance.creado_por = self.request.user
                
                # Si es el primer medio de pago, marcarlo como principal automáticamente
                if not ClienteMedioDePago.objects.filter(cliente=self.cliente).exists():
                    form.instance.es_principal = True
                
                response = super().form_valid(form)
                
                # Crear registro de historial
                HistorialClienteMedioDePago.objects.create(
                    cliente_medio_pago=self.object,
                    accion='CREADO',
                    datos_nuevos=self.object.datos_campos,
                    modificado_por=self.request.user,
                    observaciones=f'Medio de pago {self.medio_de_pago.nombre} agregado al cliente {self.cliente.nombre_completo}'
                )
                
                messages.success(
                    self.request, 
                    f'¡Perfecto! El medio de pago "{self.medio_de_pago.nombre}" fue agregado exitosamente.'
                )
                
                # Log para auditoría
                logger.info(
                    f'Usuario {self.request.user.username} agregó medio de pago '
                    f'{self.medio_de_pago.nombre} al cliente {self.cliente.nombre_completo}'
                )
                
                return response
                
        except ValidationError as e:
            messages.error(self.request, f'Error de validación: {e.message_dict}')
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'Error inesperado al guardar: {str(e)}')
            logger.error(f'Error al crear medio de pago: {str(e)}', exc_info=True)
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Manejar formulario inválido con mejor información al usuario"""
        messages.error(
            self.request, 
            'Por favor, revise los campos marcados en rojo y corrija los errores.'
        )
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('clientes:medios_pago_cliente')


class ClienteMedioDePagoUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista mejorada para editar un medio de pago del cliente
    """
    model = ClienteMedioDePago
    form_class = ClienteMedioDePagoCompleteForm
    template_name = 'clientes/medios_pago/form_medio_pago.html'

    def dispatch(self, request, *args, **kwargs):
        """Verificar permisos antes de proceder"""
        self.cliente = get_cliente_activo(request)
        if not self.cliente:
            messages.warning(request, 'Debe seleccionar un cliente primero.')
            return redirect('clientes:seleccionar_cliente')
            
        # Obtener el objeto y verificar permisos
        self.object = self.get_object()
        if self.object.cliente != self.cliente:
            messages.error(request, 'No tiene permisos para editar este medio de pago.')
            return redirect('clientes:medios_pago_cliente')
            
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['cliente'] = self.cliente
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'cliente': self.cliente,
            'medio_de_pago': self.object.medio_de_pago,
            'action': 'Editar',
            'campos': self.object.medio_de_pago.campos.all().order_by('orden', 'id'),
            'breadcrumb': [
                {'name': 'Medios de Pago', 'url': 'clientes:medios_pago_cliente'},
                {'name': f'Editar {self.object.medio_de_pago.nombre}', 'active': True}
            ]
        })
        return context

    def form_valid(self, form):
        """Procesar edición con historial"""
        try:
            with transaction.atomic():
                # Guardar datos anteriores para historial
                datos_anteriores = self.object.datos_campos.copy()
                
                response = super().form_valid(form)
                
                # Crear registro de historial solo si hubo cambios
                if datos_anteriores != self.object.datos_campos or form.has_changed():
                    HistorialClienteMedioDePago.objects.create(
                        cliente_medio_pago=self.object,
                        accion='ACTUALIZADO',
                        datos_anteriores=datos_anteriores,
                        datos_nuevos=self.object.datos_campos,
                        modificado_por=self.request.user,
                        observaciones=f'Datos del medio de pago actualizados. Campos modificados: {", ".join(form.changed_data)}'
                    )
                
                messages.success(
                    self.request,
                    f'El medio de pago "{self.object.medio_de_pago.nombre}" fue actualizado exitosamente.'
                )
                
                logger.info(
                    f'Usuario {self.request.user.username} actualizó medio de pago '
                    f'{self.object.medio_de_pago.nombre} del cliente {self.cliente.nombre_completo}'
                )
                
                return response
                
        except Exception as e:
            messages.error(self.request, f'Error al actualizar: {str(e)}')
            logger.error(f'Error al actualizar medio de pago: {str(e)}', exc_info=True)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('clientes:medios_pago_cliente')


class ClienteMedioDePagoToggleView(LoginRequiredMixin, View):
    """
    Vista mejorada para activar/desactivar un medio de pago del cliente
    """
    def post(self, request, pk):
        cliente = get_cliente_activo(request)
        if not cliente:
            messages.warning(request, 'Debe seleccionar un cliente primero.')
            return redirect('clientes:seleccionar_cliente')

        medio_pago = get_object_or_404(ClienteMedioDePago, pk=pk, cliente=cliente)
        
        # Verificar que no sea el único medio activo si se va a desactivar
        if medio_pago.es_activo:
            medios_activos = ClienteMedioDePago.objects.filter(
                cliente=cliente, 
                es_activo=True
            ).count()
            
            if medios_activos <= 1:
                messages.warning(
                    request,
                    'No puede desactivar el único medio de pago activo. '
                    'Active otro medio primero.'
                )
                return redirect('clientes:medios_pago_cliente')
        
        # Cambiar estado
        estado_anterior = medio_pago.es_activo
        medio_pago.es_activo = not medio_pago.es_activo
        
        # Si se desactiva un medio principal, asignar otro como principal
        if not medio_pago.es_activo and medio_pago.es_principal:
            otro_medio_activo = ClienteMedioDePago.objects.filter(
                cliente=cliente,
                es_activo=True
            ).exclude(pk=medio_pago.pk).first()
            
            if otro_medio_activo:
                otro_medio_activo.es_principal = True
                otro_medio_activo.save()
                medio_pago.es_principal = False
        
        medio_pago.save()
        
        # Registrar en historial
        accion = 'ACTIVADO' if medio_pago.es_activo else 'DESACTIVADO'
        HistorialClienteMedioDePago.objects.create(
            cliente_medio_pago=medio_pago,
            accion=accion,
            modificado_por=request.user,
            observaciones=f'Medio de pago {accion.lower()} por el usuario'
        )
        
        estado_actual = 'activado' if medio_pago.es_activo else 'desactivado'
        messages.success(
            request,
            f'Medio de pago "{medio_pago.medio_de_pago.nombre}" {estado_actual} exitosamente.'
        )
        
        return redirect('clientes:medios_pago_cliente')


@login_required
def medio_pago_detail_ajax(request, pk):
    """
    Vista AJAX mejorada para obtener detalles de un medio de pago
    """
    cliente = get_cliente_activo(request)
    if not cliente:
        return JsonResponse({'error': 'No hay cliente seleccionado'}, status=400)
    
    try:
        medio_pago = ClienteMedioDePago.objects.select_related(
            'medio_de_pago'
        ).prefetch_related(
            'medio_de_pago__campos'
        ).get(pk=pk, cliente=cliente)
        
        # Preparar datos de los campos
        campos_data = []
        for campo in medio_pago.medio_de_pago.campos.all().order_by('orden', 'id'):
            valor = medio_pago.get_dato_campo(campo.nombre_campo)
            campos_data.append({
                'id': campo.id,
                'nombre': campo.nombre_campo,
                'tipo': campo.get_tipo_dato_display(),
                'tipo_codigo': campo.tipo_dato,
                'requerido': campo.is_required,
                'valor': valor,
                'tiene_valor': bool(valor and str(valor).strip())
            })
        
        # Historial reciente (últimos 5 cambios)
        historial_reciente = list(
            medio_pago.historial.select_related('modificado_por')
            .values(
                'accion', 'fecha', 'modificado_por__username', 'observaciones'
            )[:5]
        )
        
        data = {
            'id': medio_pago.id,
            'medio_pago_id': medio_pago.medio_de_pago.id,
            'medio_pago_nombre': medio_pago.medio_de_pago.nombre,
            'comision': float(medio_pago.medio_de_pago.comision_porcentaje),
            'es_activo': medio_pago.es_activo,
            'es_principal': medio_pago.es_principal,
            'fecha_creacion': medio_pago.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'fecha_actualizacion': medio_pago.fecha_actualizacion.strftime('%d/%m/%Y %H:%M'),
            'creado_por': medio_pago.creado_por.username if medio_pago.creado_por else 'Sistema',
            'campos': campos_data,
            'campos_completos': medio_pago.campos_completos,
            'total_campos': len(campos_data),
            'campos_con_datos': len([c for c in campos_data if c['tiene_valor']]),
            'historial_reciente': historial_reciente
        }
        
        return JsonResponse(data)
        
    except ClienteMedioDePago.DoesNotExist:
        return JsonResponse({'error': 'Medio de pago no encontrado'}, status=404)
    except Exception as e:
        logger.error(f'Error en AJAX detail view: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)


class ClienteMedioDePagoDeleteView(LoginRequiredMixin, View):
    """
    Vista mejorada para eliminar un medio de pago del cliente
    """
    def post(self, request, pk):
        cliente = get_cliente_activo(request)
        if not cliente:
            messages.warning(request, 'Debe seleccionar un cliente primero.')
            return redirect('clientes:seleccionar_cliente')

        medio_pago = get_object_or_404(ClienteMedioDePago, pk=pk, cliente=cliente)
        
        # Verificaciones de seguridad antes de eliminar
        total_medios = ClienteMedioDePago.objects.filter(cliente=cliente).count()
        
        if total_medios <= 1:
            messages.error(
                request, 
                'No puede eliminar el único medio de pago del cliente. '
                'Debe tener al menos un medio de pago configurado.'
            )
            return redirect('clientes:medios_pago_cliente')
        
        # Verificar si hay transacciones asociadas (si aplica)
        # if medio_pago.transacciones.exists():
        #     messages.error(
        #         request,
        #         'No se puede eliminar este medio de pago porque tiene transacciones asociadas.'
        #     )
        #     return redirect('clientes:medios_pago_cliente')
        
        # Guardar información antes de eliminar
        nombre_medio = medio_pago.medio_de_pago.nombre
        era_principal = medio_pago.es_principal
        
        try:
            with transaction.atomic():
                # Si era el medio principal, asignar otro como principal
                if era_principal:
                    nuevo_principal = ClienteMedioDePago.objects.filter(
                        cliente=cliente,
                        es_activo=True
                    ).exclude(pk=medio_pago.pk).first()
                    
                    if nuevo_principal:
                        nuevo_principal.es_principal = True
                        nuevo_principal.save()
                
                # Crear registro final en el historial antes de eliminar
                HistorialClienteMedioDePago.objects.create(
                    cliente_medio_pago=medio_pago,
                    accion='ELIMINADO',
                    datos_anteriores=medio_pago.datos_campos,
                    modificado_por=request.user,
                    observaciones=f'Medio de pago eliminado por el usuario'
                )
                
                # Eliminar el medio de pago
                medio_pago.delete()
                
                messages.success(
                    request, 
                    f'Medio de pago "{nombre_medio}" eliminado exitosamente.'
                )
                
                logger.info(
                    f'Usuario {request.user.username} eliminó medio de pago '
                    f'{nombre_medio} del cliente {cliente.nombre_completo}'
                )
                
        except Exception as e:
            messages.error(request, f'Error al eliminar el medio de pago: {str(e)}')
            logger.error(f'Error al eliminar medio de pago: {str(e)}', exc_info=True)
        
        return redirect('clientes:medios_pago_cliente')


@login_required
def dashboard_medios_pago(request):
    """
    Vista dashboard con estadísticas generales de medios de pago
    """
    cliente = get_cliente_activo(request)
    if not cliente:
        return redirect('clientes:seleccionar_cliente')
    
    # Estadísticas generales
    medios = ClienteMedioDePago.objects.filter(cliente=cliente)
    total_medios = medios.count()
    medios_activos = medios.filter(es_activo=True).count()
    medio_principal = medios.filter(es_principal=True).first()
    
    # Medios por tipo
    medios_por_tipo = medios.values(
        'medio_de_pago__nombre'
    ).annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')
    
    # Actividad reciente
    historial_reciente = HistorialClienteMedioDePago.objects.filter(
        cliente_medio_pago__cliente=cliente
    ).select_related(
        'cliente_medio_pago__medio_de_pago',
        'modificado_por'
    ).order_by('-fecha')[:10]
    
    context = {
        'cliente': cliente,
        'stats': {
            'total': total_medios,
            'activos': medios_activos,
            'inactivos': total_medios - medios_activos,
            'principal': medio_principal
        },
        'medios_por_tipo': medios_por_tipo,
        'historial_reciente': historial_reciente,
        'puede_agregar_medios': MedioDePago.objects.filter(
            is_active=True
        ).exclude(
            id__in=medios.values_list('medio_de_pago_id', flat=True)
        ).exists()
    }
    
    return render(request, 'clientes/medios_pago/dashboard.html', context)


@login_required 
def exportar_medios_pago(request):
    """
    Vista para exportar medios de pago del cliente (CSV)
    """
    cliente = get_cliente_activo(request)
    if not cliente:
        return redirect('clientes:seleccionar_cliente')
    
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="medios_pago_{cliente.cedula}_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Encabezados
    headers = [
        'Tipo de Medio',
        'Estado',
        'Principal',
        'Fecha Creación',
        'Creado Por'
    ]
    
    # Agregar campos dinámicos como columnas
    campos_unicos = set()
    medios = ClienteMedioDePago.objects.filter(cliente=cliente).prefetch_related('medio_de_pago__campos')
    
    for medio in medios:
        for campo in medio.medio_de_pago.campos.all():
            campos_unicos.add(campo.nombre_campo)
    
    headers.extend(sorted(campos_unicos))
    writer.writerow(headers)
    
    # Datos
    for medio in medios:
        row = [
            medio.medio_de_pago.nombre,
            'Activo' if medio.es_activo else 'Inactivo',
            'Sí' if medio.es_principal else 'No',
            medio.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            medio.creado_por.username if medio.creado_por else 'Sistema'
        ]
        
        # Agregar valores de campos dinámicos
        for campo_nombre in sorted(campos_unicos):
            valor = medio.get_dato_campo(campo_nombre)
            row.append(valor or '')
        
        writer.writerow(row)
    
    return response