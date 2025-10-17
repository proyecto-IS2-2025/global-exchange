from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.db import models
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.crypto import get_random_string
import logging
from django.views.decorators.http import require_http_methods
from .models import Terminal, PinAcceso

from .models import (
    Terminal, 
    InventarioDivisaTerminal, 
    RegistroTransaccionTerminal,
    PINTerminalCliente
)
from .forms import TerminalForm, InventarioDivisaTerminalForm
from transacciones.models import Transaccion, HistorialTransaccion
from clientes.models import Cliente
from divisas.models import Divisa

logger = logging.getLogger(__name__)


# ==================== TERMINAL DE AUTOSERVICIO (PÚBLICO) ====================

class TerminalInicioView(View):
    """Pantalla de inicio de la terminal: Ingreso de PIN"""
    template_name = 'inicio_tauser.html'
    
    def get(self, request, terminal_codigo):
        """Muestra la pantalla de ingreso de PIN"""
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
        
        context = {
            'terminal': terminal,
        }
        return render(request, self.template_name, context)

    def post(self, request, terminal_codigo):
        """Valida el PIN ingresado"""
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
        pin = request.POST.get('pin_ingresado', '').strip()
        
        if not pin:
            messages.error(request, "Debe ingresar un PIN.")
            return redirect('tauser:0990', terminal_codigo=terminal_codigo)
        
        try:
            # Buscar PIN válido
            pin_obj = PINTerminalCliente.objects.select_related('cliente').get(
                pin=pin,
                usado=False,
                fecha_expiracion__gt=timezone.now()
            )
            
            # Marcar PIN como usado
            pin_obj.marcar_usado(terminal)
            
            # Guardar información en sesión
            request.session['terminal_id'] = terminal.id
            request.session['cliente_terminal_id'] = pin_obj.cliente.id
            request.session['pin_id'] = pin_obj.id
            
            logger.info(f"Acceso exitoso a terminal {terminal.codigo} - Cliente: {pin_obj.cliente.nombre_completo}")
            
            return redirect('tauser:transacciones_cliente', 
                          terminal_codigo=terminal_codigo, 
                          cliente_id=pin_obj.cliente.id)
            
        except PINTerminalCliente.DoesNotExist:
            messages.error(request, "PIN inválido o expirado.")
            logger.warning(f"Intento de acceso fallido a terminal {terminal.codigo} con PIN: {pin}")
            
            # Registrar intento fallido
            RegistroTransaccionTerminal.objects.create(
                terminal=terminal,
                cliente=None,
                tipo_operacion='CONSULTA',
                fue_exitoso=False,
                mensaje_error=f"PIN inválido: {pin}"
            )
            
            return redirect('tauser:inicio', terminal_codigo=terminal_codigo)


class TransaccionesClienteView(View):
    """Muestra las transacciones pendientes del cliente"""
    template_name = 'transacciones_cliente.html'

    def get(self, request, terminal_codigo, cliente_id):
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
        cliente = get_object_or_404(Cliente, pk=cliente_id, esta_activo=True)
        
        # Verificar que el cliente en sesión coincida
        cliente_sesion = request.session.get('cliente_terminal_id')
        if str(cliente_sesion) != str(cliente_id):
            messages.error(request, "Acceso no autorizado.")
            return redirect('tauser:inicio', terminal_codigo=terminal_codigo)
        
        # Obtener transacciones pendientes
        # RETIRO: Cliente compró divisa extranjera y debe retirarla
        transacciones_retiro = Transaccion.objects.filter(
            cliente=cliente,
            tipo_operacion='compra',
            estado='pagada'  # Ya pagó, falta que retire la divisa
        ).exclude(
            divisa_destino__code='PYG'  # Excluir guaraníes
        ).select_related('divisa_origen', 'divisa_destino').order_by('-fecha_creacion')
        
        # PAGO: Cliente vendió divisa y debe recibir el pago en guaraníes
        transacciones_pago = Transaccion.objects.filter(
            cliente=cliente,
            tipo_operacion='venta',
            estado='pagada',  # Transacción aprobada
            divisa_destino__code='PYG'  # Debe recibir guaraníes
        ).select_related('divisa_origen', 'divisa_destino').order_by('-fecha_creacion')
        
        # Verificar disponibilidad en terminal
        transacciones_retiro_disponibles = []
        for trans in transacciones_retiro:
            disponible = terminal.tiene_inventario_suficiente(
                trans.divisa_destino, 
                trans.monto_destino
            )
            transacciones_retiro_disponibles.append({
                'transaccion': trans,
                'disponible': disponible
            })
        
        context = {
            'terminal': terminal,
            'cliente': cliente,
            'transacciones_retiro': transacciones_retiro_disponibles,
            'transacciones_pago': transacciones_pago,
        }
        
        # Registrar consulta
        RegistroTransaccionTerminal.objects.create(
            terminal=terminal,
            cliente=cliente,
            tipo_operacion='CONSULTA',
            fue_exitoso=True,
            pin_usado_id=request.session.get('pin_id')
        )
        
        return render(request, self.template_name, context)


class EjecutarOperacionView(View):
    """Procesa el retiro o pago de una transacción"""

    def post(self, request, terminal_codigo, transaccion_id):
        terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_activa=True)
        transaccion = get_object_or_404(
            Transaccion.objects.select_related('cliente', 'divisa_origen', 'divisa_destino'),
            numero_transaccion=transaccion_id
        )
        
        # Verificar que el cliente en sesión coincida
        cliente_sesion = request.session.get('cliente_terminal_id')
        if str(cliente_sesion) != str(transaccion.cliente.id):
            messages.error(request, "Acceso no autorizado.")
            return redirect('tauser:inicio', terminal_codigo=terminal_codigo)
        
        tipo_operacion = request.POST.get('tipo_operacion')
        
        try:
            with transaction.atomic():
                if tipo_operacion == 'RETIRO':
                    # Cliente retira divisa extranjera (compra completada)
                    self._procesar_retiro(terminal, transaccion, request)
                    
                elif tipo_operacion == 'PAGO':
                    # Cliente recibe pago en guaraníes (venta completada)
                    self._procesar_pago(terminal, transaccion, request)
                    
                else:
                    raise ValueError("Tipo de operación inválido")
                
                messages.success(request, f"¡Operación de {tipo_operacion} completada con éxito!")
                
        except ValueError as e:
            messages.error(request, str(e))
            logger.error(f"Error en operación {tipo_operacion}: {e}")
            
            # Registrar operación fallida
            RegistroTransaccionTerminal.objects.create(
                terminal=terminal,
                transaccion_original=transaccion,
                cliente=transaccion.cliente,
                tipo_operacion=tipo_operacion,
                divisa=transaccion.divisa_destino if tipo_operacion == 'RETIRO' else transaccion.divisa_origen,
                monto_operacion=transaccion.monto_destino if tipo_operacion == 'RETIRO' else transaccion.monto_origen,
                fue_exitoso=False,
                mensaje_error=str(e),
                pin_usado_id=request.session.get('pin_id')
            )
        
        return redirect('tauser:transacciones_cliente', 
                       terminal_codigo=terminal_codigo, 
                       cliente_id=transaccion.cliente.id)
    
    def _procesar_retiro(self, terminal, transaccion, request):
        """Procesa el retiro de divisa extranjera"""
        if transaccion.tipo_operacion != 'compra':
            raise ValueError("Esta transacción no es una compra.")
        
        if transaccion.estado != 'pagada':
            raise ValueError("Esta transacción no está lista para retiro.")
        
        divisa_a_retirar = transaccion.divisa_destino
        monto_a_retirar = transaccion.monto_destino
        
        # Verificar inventario
        try:
            inventario = InventarioDivisaTerminal.objects.select_for_update().get(
                terminal=terminal,
                divisa=divisa_a_retirar
            )
            
            if inventario.cantidad < monto_a_retirar:
                raise ValueError(
                    f"Inventario insuficiente. Disponible: {inventario.cantidad} {divisa_a_retirar.code}"
                )
            
            # Descontar del inventario
            inventario.descontar(monto_a_retirar)
            inventario.actualizado_por = request.user if request.user.is_authenticated else None
            inventario.save()
            
        except InventarioDivisaTerminal.DoesNotExist:
            raise ValueError(f"No hay inventario de {divisa_a_retirar.code} en esta terminal.")
        
        # Actualizar estado de la transacción
        transaccion.estado = 'completado'
        transaccion.save()
        
        # Registrar en historial
        HistorialTransaccion.objects.create(
            transaccion=transaccion,
            estado_anterior='pagada',
            estado_nuevo='completado',
            observacion=f'Divisa retirada en terminal {terminal.nombre}',
            usuario=request.user if request.user.is_authenticated else None
        )
        
        # Registrar operación exitosa
        RegistroTransaccionTerminal.objects.create(
            terminal=terminal,
            transaccion_original=transaccion,
            cliente=transaccion.cliente,
            tipo_operacion='RETIRO',
            divisa=divisa_a_retirar,
            monto_operacion=monto_a_retirar,
            fue_exitoso=True,
            pin_usado_id=request.session.get('pin_id')
        )
        
        logger.info(
            f"Retiro completado - Terminal: {terminal.nombre}, "
            f"Cliente: {transaccion.cliente.nombre_completo}, "
            f"Monto: {monto_a_retirar} {divisa_a_retirar.code}"
        )
    
    def _procesar_pago(self, terminal, transaccion, request):
        """Procesa el pago en guaraníes por venta de divisa"""
        if transaccion.tipo_operacion != 'venta':
            raise ValueError("Esta transacción no es una venta.")
        
        if transaccion.estado != 'pagada':
            raise ValueError("Esta transacción no está lista para pago.")
        
        divisa_pago = transaccion.divisa_destino  # Debe ser PYG
        monto_pago = transaccion.monto_destino
        
        if divisa_pago.code != 'PYG':
            raise ValueError("El pago debe ser en Guaraníes (PYG).")
        
        # Verificar inventario de guaraníes
        try:
            inventario = InventarioDivisaTerminal.objects.select_for_update().get(
                terminal=terminal,
                divisa=divisa_pago
            )
            
            if inventario.cantidad < monto_pago:
                raise ValueError(
                    f"Inventario insuficiente de efectivo. Disponible: ₲{inventario.cantidad:,.0f}"
                )
            
            # Descontar del inventario
            inventario.descontar(monto_pago)
            inventario.actualizado_por = request.user if request.user.is_authenticated else None
            inventario.save()
            
        except InventarioDivisaTerminal.DoesNotExist:
            raise ValueError("No hay inventario de efectivo en esta terminal.")
        
        # Actualizar estado de la transacción
        transaccion.estado = 'completado'
        transaccion.save()
        
        # Registrar en historial
        HistorialTransaccion.objects.create(
            transaccion=transaccion,
            estado_anterior='pagada',
            estado_nuevo='completado',
            observacion=f'Pago realizado en terminal {terminal.nombre}',
            usuario=request.user if request.user.is_authenticated else None
        )
        
        # Registrar operación exitosa
        RegistroTransaccionTerminal.objects.create(
            terminal=terminal,
            transaccion_original=transaccion,
            cliente=transaccion.cliente,
            tipo_operacion='PAGO',
            divisa=divisa_pago,
            monto_operacion=monto_pago,
            fue_exitoso=True,
            pin_usado_id=request.session.get('pin_id')
        )
        
        logger.info(
            f"Pago completado - Terminal: {terminal.nombre}, "
            f"Cliente: {transaccion.cliente.nombre_completo}, "
            f"Monto: ₲{monto_pago:,.0f}"
        )


class CerrarSesionTerminalView(View):
    """Cierra la sesión del cliente en la terminal"""
    
    def post(self, request, terminal_codigo):
        # Limpiar sesión
        request.session.pop('terminal_id', None)
        request.session.pop('cliente_terminal_id', None)
        request.session.pop('pin_id', None)
        
        messages.success(request, "Sesión cerrada correctamente.")
        return redirect('tauser:inicio', terminal_codigo=terminal_codigo)


# ==================== CRUD DE TERMINALES (ADMIN) ====================

class TerminalListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista todas las terminales del sistema"""
    model = Terminal
    template_name = 'terminal_list.html'
    context_object_name = 'terminales'
    permission_required = 'tauser.view_terminal'
    paginate_by = 20

    def get_queryset(self):
        queryset = Terminal.objects.select_related('usuario_responsable').prefetch_related('inventario__divisa')
        
        # Filtros
        buscar = self.request.GET.get('buscar')
        if buscar:
            queryset = queryset.filter(
                models.Q(nombre__icontains=buscar) |
                models.Q(codigo__icontains=buscar) |
                models.Q(ubicacion__icontains=buscar)
            )
        
        estado = self.request.GET.get('estado')
        if estado == 'activas':
            queryset = queryset.filter(is_activa=True)
        elif estado == 'inactivas':
            queryset = queryset.filter(is_activa=False)
        
        return queryset.order_by('-is_activa', 'nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_terminales'] = Terminal.objects.count()
        context['terminales_activas'] = Terminal.objects.filter(is_activa=True).count()
        return context


class TerminalCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Crea una nueva terminal"""
    model = Terminal
    form_class = TerminalForm
    template_name = 'terminal_form.html'
    success_url = reverse_lazy('tauser:terminal_list')
    permission_required = 'tauser.add_terminal'

    def form_valid(self, form):
        messages.success(self.request, f'Terminal "{form.instance.nombre}" creada exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nueva Terminal'
        context['boton_texto'] = 'Crear Terminal'
        return context


class TerminalUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Actualiza una terminal existente"""
    model = Terminal
    form_class = TerminalForm
    template_name = 'terminal_form.html'
    success_url = reverse_lazy('tauser:terminal_list')
    permission_required = 'tauser.change_terminal'

    def form_valid(self, form):
        messages.success(self.request, f'Terminal "{form.instance.nombre}" actualizada exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Terminal: {self.object.nombre}'
        context['boton_texto'] = 'Guardar Cambios'
        return context


class TerminalDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Elimina una terminal (soft delete - marca como inactiva)"""
    model = Terminal
    template_name = 'terminal_confirm_delete.html'
    success_url = reverse_lazy('tauser:terminal_list')
    permission_required = 'tauser.delete_terminal'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Soft delete: marcar como inactiva en lugar de eliminar
        self.object.is_activa = False
        self.object.save()
        messages.warning(request, f'Terminal "{self.object.nombre}" desactivada.')
        return redirect(self.success_url)


class TerminalDetailView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Detalle de una terminal con su inventario"""
    permission_required = 'tauser.view_terminal'
    template_name = 'terminal_detail.html'

    def get(self, request, pk):
        terminal = get_object_or_404(Terminal.objects.prefetch_related('inventario__divisa'), pk=pk)
        
        # Obtener inventario con alertas
        inventarios = terminal.inventario.all()
        inventarios_con_alerta = [inv for inv in inventarios if inv.necesita_reposicion]
        
        # Obtener últimas operaciones
        ultimas_operaciones = RegistroTransaccionTerminal.objects.filter(
            terminal=terminal
        ).select_related('cliente', 'divisa', 'transaccion_original').order_by('-fecha_operacion')[:20]
        
        # Estadísticas
        operaciones_exitosas = RegistroTransaccionTerminal.objects.filter(
            terminal=terminal,
            fue_exitoso=True
        ).count()
        
        operaciones_fallidas = RegistroTransaccionTerminal.objects.filter(
            terminal=terminal,
            fue_exitoso=False
        ).count()
        
        context = {
            'terminal': terminal,
            'inventarios': inventarios,
            'inventarios_con_alerta': inventarios_con_alerta,
            'ultimas_operaciones': ultimas_operaciones,
            'operaciones_exitosas': operaciones_exitosas,
            'operaciones_fallidas': operaciones_fallidas,
        }
        
        return render(request, self.template_name, context)


# ==================== GESTIÓN DE INVENTARIO ====================

class InventarioTerminalView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Gestiona el inventario de divisas de una terminal"""
    permission_required = 'tauser.change_inventariodivisaterminal'
    template_name = 'inventario_terminal.html'

    def get(self, request, terminal_pk):
        terminal = get_object_or_404(Terminal, pk=terminal_pk)
        
        # Crear formset para el inventario existente
        from django.forms import inlineformset_factory
        InventarioFormSet = inlineformset_factory(
            Terminal,
            InventarioDivisaTerminal,
            form=InventarioDivisaTerminalForm,
            extra=1,
            can_delete=False
        )
        
        formset = InventarioFormSet(instance=terminal)
        
        context = {
            'terminal': terminal,
            'formset': formset,
        }
        
        return render(request, self.template_name, context)

    def post(self, request, terminal_pk):
        terminal = get_object_or_404(Terminal, pk=terminal_pk)
        
        from django.forms import inlineformset_factory
        InventarioFormSet = inlineformset_factory(
            Terminal,
            InventarioDivisaTerminal,
            form=InventarioDivisaTerminalForm,
            extra=1,
            can_delete=False
        )
        
        formset = InventarioFormSet(request.POST, instance=terminal)
        
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.actualizado_por = request.user
                instance.save()
            
            messages.success(request, 'Inventario actualizado correctamente.')
            return redirect('tauser:terminal_detail', pk=terminal.pk)
        
        context = {
            'terminal': terminal,
            'formset': formset,
        }
        
        return render(request, self.template_name, context)


@login_required
@user_passes_test(lambda u: u.has_perm('tauser.change_terminal'))
def toggle_terminal_activa(request, pk):
    """Activa/desactiva una terminal"""
    terminal = get_object_or_404(Terminal, pk=pk)
    terminal.is_activa = not terminal.is_activa
    terminal.save()
    
    estado = "activada" if terminal.is_activa else "desactivada"
    messages.success(request, f'Terminal "{terminal.nombre}" {estado}.')
    
    return redirect('tauser:terminal_list')


# ==================== GENERACIÓN DE PINES ====================

@login_required
@user_passes_test(lambda u: u.has_perm('clientes.view_cliente'))
def generar_pin_cliente(request, cliente_id):
    """Genera un PIN temporal para un cliente"""
    cliente = get_object_or_404(Cliente, pk=cliente_id, esta_activo=True)
    
    if request.method == 'POST':
        # Generar PIN de 6 dígitos
        pin = get_random_string(length=6, allowed_chars='0123456789')
        
        # Verificar que no exista (muy improbable, pero por seguridad)
        while PINTerminalCliente.objects.filter(pin=pin, usado=False, fecha_expiracion__gt=timezone.now()).exists():
            pin = get_random_string(length=6, allowed_chars='0123456789')
        
        # Calcular fecha de expiración (24 horas por defecto)
        duracion_horas = int(request.POST.get('duracion_horas', 24))
        fecha_expiracion = timezone.now() + timedelta(hours=duracion_horas)
        
        # Crear PIN
        pin_obj = PINTerminalCliente.objects.create(
            cliente=cliente,
            pin=pin,
            fecha_expiracion=fecha_expiracion
        )
        
        messages.success(
            request, 
            f'PIN generado exitosamente: <strong>{pin}</strong> (válido hasta {fecha_expiracion.strftime("%d/%m/%Y %H:%M")})'
        )
        
        # TODO: Enviar PIN por correo electrónico
        # from django.core.mail import send_mail
        # send_mail(...)
        
        logger.info(f"PIN generado para cliente {cliente.nombre_completo}: {pin}")
        
        return redirect('clientes:detalle_cliente', pk=cliente.id)
    
    context = {
        'cliente': cliente,
    }

    return render(request, 'generar_pin.html', context)

def es_cliente(user):
    """Verifica si el usuario pertenece al grupo 'cliente'"""
    return user.is_authenticated and user.groups.filter(name='cliente').exists()


@login_required
@user_passes_test(es_cliente, login_url='inicio')
def lista_terminales(request):
    """
    Vista para mostrar la lista de terminales activos disponibles.
    Solo accesible para usuarios del grupo 'cliente'.
    """
    terminales = Terminal.objects.filter(is_active=True).order_by('orden', 'nombre')
    
    context = {
        'terminales': terminales,
        'titulo': 'Seleccionar Terminal TAUSER'
    }
    
    return render(request, 'tauser/lista_terminales.html', context)


@login_required
@user_passes_test(es_cliente, login_url='inicio')
def seleccionar_terminal(request, terminal_codigo):
    """
    Vista para seleccionar un terminal y mostrar la pantalla de ingreso de PIN.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_active=True)
    
    # Guardar el terminal seleccionado en la sesión
    request.session['terminal_codigo'] = terminal.codigo
    request.session['terminal_nombre'] = terminal.nombre
    
    # Redirigir a la vista de inicio del terminal
    return redirect('tauser:inicio_tauser', terminal_codigo=terminal.codigo)


@login_required
@require_http_methods(["GET", "POST"])
def inicio_tauser(request, terminal_codigo):
    """
    Vista principal del terminal TAUSER donde se ingresa el PIN.
    """
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_active=True)
    
    if request.method == 'POST':
        pin_ingresado = request.POST.get('pin_ingresado', '').strip()
        
        if not pin_ingresado:
            messages.error(request, 'Por favor ingrese su PIN.')
            return render(request, 'tauser/inicio.html', {'terminal': terminal})
        
        try:
            # Buscar PIN válido
            pin_acceso = PinAcceso.objects.get(
                pin=pin_ingresado,
                terminal=terminal,
                usado=False,
                fecha_expiracion__gt=timezone.now()
            )
            
            # Marcar el PIN como usado
            pin_acceso.usado = True
            pin_acceso.fecha_uso = timezone.now()
            pin_acceso.save()
            
            # Guardar información en la sesión
            request.session['pin_validado'] = True
            request.session['pin_acceso_id'] = pin_acceso.id
            request.session['cliente_id'] = pin_acceso.cliente.id
            
            messages.success(
                request, 
                f'¡Bienvenido! Acceso autorizado al terminal {terminal.nombre}'
            )
            
            # Redirigir al menú principal del TAUSER
            return redirect('tauser:menu_principal', terminal_codigo=terminal.codigo)
            
        except PinAcceso.DoesNotExist:
            messages.error(
                request, 
                'PIN inválido, expirado o ya utilizado. Por favor verifique e intente nuevamente.'
            )
            return render(request, 'tauser/inicio.html', {'terminal': terminal})
    
    # GET request
    return render(request, 'tauser/inicio.html', {'terminal': terminal})


@login_required
def menu_principal(request, terminal_codigo):
    """
    Vista del menú principal después de validar el PIN.
    """
    # Verificar que el PIN esté validado
    if not request.session.get('pin_validado'):
        messages.warning(request, 'Debe ingresar un PIN válido primero.')
        return redirect('tauser:inicio_tauser', terminal_codigo=terminal_codigo)
    
    terminal = get_object_or_404(Terminal, codigo=terminal_codigo, is_active=True)
    
    # Obtener información del cliente desde la sesión
    cliente_id = request.session.get('cliente_id')
    
    context = {
        'terminal': terminal,
        'cliente_id': cliente_id,
    }
    
    return render(request, 'tauser/menu_principal.html', context)


@login_required
def cerrar_sesion_tauser(request, terminal_codigo):
    """
    Cierra la sesión del TAUSER y limpia la sesión.
    """
    # Limpiar variables de sesión relacionadas con TAUSER
    request.session.pop('pin_validado', None)
    request.session.pop('pin_acceso_id', None)
    request.session.pop('cliente_id', None)
    request.session.pop('terminal_codigo', None)
    request.session.pop('terminal_nombre', None)
    
    messages.info(request, 'Sesión del terminal cerrada exitosamente.')
    
    return redirect('tauser:lista_terminales')