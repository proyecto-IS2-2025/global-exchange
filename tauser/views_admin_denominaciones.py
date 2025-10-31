"""
Vistas administrativas adicionales para gestión de inventario por denominaciones.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Count, Sum
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Terminal, InventarioDenominacionTerminal
from divisas.models import Denominacion
from .forms_denominaciones import InventarioDenominacionTerminalForm
import logging

logger = logging.getLogger(__name__)


class GestionInventarioDenominacionesView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista de SOLO LECTURA para consultar inventario de denominaciones del terminal.
    VERSIÓN ACTUALIZADA: Solo permite visualizar el stock, sin permitir modificaciones.
    Para recargas, usar el sistema externo de reabastecimiento.
    """
    permission_required = 'tauser.view_inventariodenominacionterminal'
    template_name = 'tauser/admin/gestion_inventario_denominaciones_readonly.html'
    
    def get(self, request, terminal_pk):
        terminal = get_object_or_404(Terminal, pk=terminal_pk)
        
        # Obtener inventario actual agrupado por divisa
        inventarios = InventarioDenominacionTerminal.objects.filter(
            terminal=terminal
        ).select_related('denominacion__divisa').order_by(
            'denominacion__divisa__code',
            '-denominacion__valor'
        )
        
        # Agrupar por divisa
        inventarios_por_divisa = {}
        totales_globales = {
            'total_billetes': 0,
            'total_alertas': 0,
            'divisas_count': 0
        }
        
        for inv in inventarios:
            divisa_code = inv.denominacion.divisa.code
            if divisa_code not in inventarios_por_divisa:
                inventarios_por_divisa[divisa_code] = {
                    'divisa': inv.denominacion.divisa,
                    'inventarios': [],
                    'valor_total': 0,
                    'total_billetes': 0,
                    'alertas': 0
                }
                totales_globales['divisas_count'] += 1
            
            inventarios_por_divisa[divisa_code]['inventarios'].append(inv)
            inventarios_por_divisa[divisa_code]['valor_total'] += inv.valor_total
            inventarios_por_divisa[divisa_code]['total_billetes'] += inv.cantidad
            totales_globales['total_billetes'] += inv.cantidad
            
            if inv.necesita_reposicion:
                inventarios_por_divisa[divisa_code]['alertas'] += 1
                totales_globales['total_alertas'] += 1
        
        # Obtener denominaciones NO configuradas (disponibles para agregar)
        denominaciones_configuradas_ids = inventarios.values_list('denominacion_id', flat=True)
        denominaciones_disponibles = Denominacion.objects.filter(
            is_active=True
        ).exclude(
            id__in=denominaciones_configuradas_ids
        ).select_related('divisa').order_by('divisa__code', '-valor')
        
        context = {
            'terminal': terminal,
            'inventario_por_divisa': inventarios_por_divisa,
            'inventario_alertas': [inv for inv in inventarios if inv.necesita_reposicion],
            'denominaciones_disponibles': denominaciones_disponibles,
            'totales_globales': totales_globales,
            'tiene_inventario': inventarios.exists(),
        }
        
        return render(request, self.template_name, context)


class AgregarDenominacionInventarioView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Agregar una nueva denominación al inventario del terminal.
    """
    model = InventarioDenominacionTerminal
    form_class = InventarioDenominacionTerminalForm
    template_name = 'tauser/admin/agregar_denominacion_inventario.html'
    permission_required = 'tauser.add_inventariodenominacionterminal'
    
    def get_form_kwargs(self):
        """Pasar el terminal al formulario para validación"""
        kwargs = super().get_form_kwargs()
        terminal_pk = self.kwargs.get('terminal_pk')
        kwargs['terminal'] = get_object_or_404(Terminal, pk=terminal_pk)
        return kwargs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        terminal_pk = self.kwargs['terminal_pk']
        context['terminal'] = get_object_or_404(Terminal, pk=terminal_pk)
        return context
    
    def form_valid(self, form):
        terminal_pk = self.kwargs['terminal_pk']
        terminal = get_object_or_404(Terminal, pk=terminal_pk)
        
        form.instance.terminal = terminal
        form.instance.actualizado_por = self.request.user
        
        # Verificar que no exista ya
        denominacion = form.instance.denominacion
        if InventarioDenominacionTerminal.objects.filter(
            terminal=terminal,
            denominacion=denominacion
        ).exists():
            messages.error(
                self.request,
                f'La denominación {denominacion} ya existe en el inventario de este terminal.'
            )
            return self.form_invalid(form)
        
        messages.success(
            self.request,
            f'✓ Denominación {denominacion} agregada al inventario.'
        )
        
        logger.info(
            f"[ADMIN] Denominación agregada - Terminal: {terminal.codigo}, "
            f"Denominación: {denominacion}, Cantidad: {form.instance.cantidad}, "
            f"Usuario: {self.request.user.username}"
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy(
            'tauser:gestion_inventario_denominaciones',
            kwargs={'terminal_pk': self.kwargs['terminal_pk']}
        )


class AjustarInventarioDenominacionAdminView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Ajustar cantidad de una denominación existente en el inventario (admin).
    """
    permission_required = 'tauser.change_inventariodenominacionterminal'
    
    def post(self, request, terminal_pk, inventario_pk):
        terminal = get_object_or_404(Terminal, pk=terminal_pk)
        inventario = get_object_or_404(
            InventarioDenominacionTerminal,
            pk=inventario_pk,
            terminal=terminal
        )
        
        accion = request.POST.get('accion')  # 'agregar' o 'establecer'
        cantidad_str = request.POST.get('cantidad', '0')
        motivo = request.POST.get('motivo', 'Ajuste administrativo')
        
        try:
            cantidad = int(cantidad_str)
            if cantidad < 0:
                raise ValueError("La cantidad no puede ser negativa")
            
            cantidad_anterior = inventario.cantidad
            
            if accion == 'agregar':
                # Agregar a la cantidad existente
                inventario.cantidad += cantidad
                operacion = f'Agregados {cantidad} billetes'
            elif accion == 'establecer':
                # Establecer cantidad absoluta
                inventario.cantidad = cantidad
                diferencia = cantidad - cantidad_anterior
                signo = '+' if diferencia > 0 else ''
                operacion = f'Ajustado a {cantidad} billetes ({signo}{diferencia})'
            else:
                raise ValueError("Acción inválida")
            
            inventario.actualizado_por = request.user
            inventario.save()
            
            # Registrar ajuste
            from .models import RegistroTransaccionTerminal
            RegistroTransaccionTerminal.objects.create(
                terminal=terminal,
                tipo_operacion='AJUSTE',
                divisa=inventario.denominacion.divisa,
                fue_exitoso=True,
                mensaje_error=(
                    f'{operacion} de {inventario.denominacion}. '
                    f'Anterior: {cantidad_anterior}, Nueva: {inventario.cantidad}. '
                    f'Motivo: {motivo}. Usuario: {request.user.username}'
                )
            )
            
            messages.success(
                request,
                f'✓ {operacion} para {inventario.denominacion}'
            )
            
            logger.info(
                f"[ADMIN] Inventario ajustado - Terminal: {terminal.codigo}, "
                f"Denominación: {inventario.denominacion}, "
                f"Anterior: {cantidad_anterior}, Nueva: {inventario.cantidad}, "
                f"Motivo: {motivo}, Usuario: {request.user.username}"
            )
            
        except ValueError as e:
            messages.error(request, f'Error: {str(e)}')
            logger.error(f"[ADMIN] Error en ajuste: {e}")
        
        return redirect(
            'tauser:gestion_inventario_denominaciones',
            terminal_pk=terminal_pk
        )


class EliminarInventarioDenominacionView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Eliminar una denominación del inventario del terminal.
    """
    model = InventarioDenominacionTerminal
    template_name = 'tauser/admin/eliminar_inventario_denominacion.html'
    permission_required = 'tauser.delete_inventariodenominacionterminal'
    
    def get_object(self):
        terminal_pk = self.kwargs['terminal_pk']
        inventario_pk = self.kwargs['inventario_pk']
        return get_object_or_404(
            InventarioDenominacionTerminal,
            pk=inventario_pk,
            terminal__pk=terminal_pk
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['terminal'] = self.object.terminal
        return context
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        terminal = self.object.terminal
        denominacion = self.object.denominacion
        
        messages.warning(
            request,
            f'⚠️ Denominación {denominacion} eliminada del inventario.'
        )
        
        logger.warning(
            f"[ADMIN] Inventario eliminado - Terminal: {terminal.codigo}, "
            f"Denominación: {denominacion}, Usuario: {request.user.username}"
        )
        
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy(
            'tauser:gestion_inventario_denominaciones',
            kwargs={'terminal_pk': self.kwargs['terminal_pk']}
        )


class DashboardInventarioView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Dashboard mejorado con alertas críticas, estadísticas y recomendaciones.
    """
    permission_required = 'tauser.view_inventariodenominacionterminal'
    template_name = 'tauser/admin/dashboard_inventario.html'
    
    def get(self, request, terminal_pk):
        terminal = get_object_or_404(Terminal, pk=terminal_pk)
        
        # Inventario actual
        inventarios = InventarioDenominacionTerminal.objects.filter(
            terminal=terminal
        ).select_related('denominacion__divisa').order_by(
            'denominacion__divisa__code',
            '-denominacion__valor'
        )
        
        # Clasificar alertas por criticidad
        alertas_criticas = []  # <= 10% del máximo
        alertas_moderadas = []  # <= 25% del máximo
        inventarios_ok = []  # > 25% del máximo
        
        for inv in inventarios:
            porcentaje = (inv.cantidad / inv.cantidad_maxima * 100) if inv.cantidad_maxima > 0 else 0
            
            if porcentaje <= 10:
                alertas_criticas.append({
                    'inventario': inv,
                    'porcentaje': porcentaje,
                    'nivel': 'CRÍTICO',
                    'color': 'danger'
                })
            elif porcentaje <= 25:
                alertas_moderadas.append({
                    'inventario': inv,
                    'porcentaje': porcentaje,
                    'nivel': 'ADVERTENCIA',
                    'color': 'warning'
                })
            else:
                inventarios_ok.append({
                    'inventario': inv,
                    'porcentaje': porcentaje,
                    'nivel': 'NORMAL',
                    'color': 'success'
                })
        
        # Últimas recargas
        from .models import LogRecargaInventario
        ultimas_recargas = LogRecargaInventario.objects.filter(
            terminal=terminal
        ).select_related(
            'denominacion__divisa',
            'usuario'
        ).order_by('-fecha')[:10]
        
        # Estadísticas de recargas (últimos 30 días)
        desde = timezone.now() - timezone.timedelta(days=30)
        recargas_mes = LogRecargaInventario.objects.filter(
            terminal=terminal,
            fecha__gte=desde
        )
        
        total_recargas = recargas_mes.count()
        valor_total_recargado = sum(r.valor_total_agregado for r in recargas_mes)
        
        # Denominaciones más recargadas
        from django.db.models import Count, Sum
        denominaciones_frecuentes = recargas_mes.values(
            'denominacion__divisa__code',
            'denominacion__valor'
        ).annotate(
            total_recargas=Count('id'),
            total_cantidad=Sum('cantidad_agregada')
        ).order_by('-total_recargas')[:5]
        
        context = {
            'terminal': terminal,
            'alertas_criticas': alertas_criticas,
            'alertas_moderadas': alertas_moderadas,
            'inventarios_ok': inventarios_ok,
            'ultimas_recargas': ultimas_recargas,
            'total_recargas_mes': total_recargas,
            'valor_total_recargado': valor_total_recargado,
            'denominaciones_frecuentes': denominaciones_frecuentes,
            'total_denominaciones': inventarios.count(),
        }
        
        return render(request, self.template_name, context)


class RecargaMasivaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Formulario para recargar múltiples denominaciones simultáneamente.
    """
    permission_required = 'tauser.change_inventariodenominacionterminal'
    template_name = 'tauser/admin/recarga_masiva.html'
    
    def get(self, request, terminal_pk):
        terminal = get_object_or_404(Terminal, pk=terminal_pk)
        
        # Obtener inventario actual
        inventarios = InventarioDenominacionTerminal.objects.filter(
            terminal=terminal
        ).select_related('denominacion__divisa').order_by(
            'denominacion__divisa__code',
            '-denominacion__valor'
        )
        
        # Agrupar por divisa
        inventarios_por_divisa = {}
        for inv in inventarios:
            divisa_code = inv.denominacion.divisa.code
            if divisa_code not in inventarios_por_divisa:
                inventarios_por_divisa[divisa_code] = {
                    'divisa': inv.denominacion.divisa,
                    'inventarios': []
                }
            inventarios_por_divisa[divisa_code]['inventarios'].append(inv)
        
        context = {
            'terminal': terminal,
            'inventarios_por_divisa': inventarios_por_divisa,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, terminal_pk):
        terminal = get_object_or_404(Terminal, pk=terminal_pk)
        observaciones_generales = request.POST.get('observaciones', '').strip()
        
        recargas_realizadas = []
        errores = []
        
        # Procesar cada denominación
        with transaction.atomic():
            for key, value in request.POST.items():
                if key.startswith('cantidad_') and value:
                    try:
                        inventario_id = key.replace('cantidad_', '')
                        cantidad = int(value)
                        
                        if cantidad <= 0:
                            continue  # Saltar si no hay cantidad
                        
                        inventario = InventarioDenominacionTerminal.objects.select_for_update().get(
                            id=inventario_id,
                            terminal=terminal
                        )
                        
                        # Guardar valores anteriores
                        cantidad_anterior = inventario.cantidad
                        
                        # Actualizar cantidad
                        inventario.cantidad += cantidad
                        inventario.actualizado_por = request.user
                        inventario.save()
                        
                        # Crear log de recarga
                        from .models import LogRecargaInventario
                        log = LogRecargaInventario.objects.create(
                            terminal=terminal,
                            usuario=request.user,
                            denominacion=inventario.denominacion,
                            cantidad_agregada=cantidad,
                            cantidad_anterior=cantidad_anterior,
                            cantidad_nueva=inventario.cantidad,
                            observaciones=observaciones_generales or 'Recarga masiva'
                        )
                        
                        recargas_realizadas.append({
                            'denominacion': inventario.denominacion,
                            'cantidad': cantidad,
                            'valor_total': log.valor_total_agregado
                        })
                        
                        logger.info(
                            f"[RECARGA MASIVA] Terminal: {terminal.codigo}, "
                            f"Denominación: {inventario.denominacion}, "
                            f"Cantidad: {cantidad}, Usuario: {request.user.username}"
                        )
                        
                    except InventarioDenominacionTerminal.DoesNotExist:
                        errores.append(f"Inventario ID {inventario_id} no encontrado")
                    except ValueError:
                        errores.append(f"Cantidad inválida para inventario {inventario_id}")
                    except Exception as e:
                        errores.append(f"Error procesando inventario {inventario_id}: {str(e)}")
                        logger.error(f"[RECARGA MASIVA ERROR] {e}")
        
        # Mensajes de resultado
        if recargas_realizadas:
            total_recargas = len(recargas_realizadas)
            valor_total = sum(r['valor_total'] for r in recargas_realizadas)
            messages.success(
                request,
                f'✓ Se realizaron {total_recargas} recargas exitosamente. Valor total: ${valor_total:,.2f}'
            )
        
        if errores:
            for error in errores:
                messages.error(request, f'❌ {error}')
        
        if not recargas_realizadas and not errores:
            messages.warning(request, '⚠️ No se ingresaron cantidades para recargar')
        
        return redirect('tauser:dashboard_inventario', terminal_pk=terminal_pk)


class HistorialRecargasView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista de historial completo de recargas con filtros.
    """
    permission_required = 'tauser.view_inventariodenominacionterminal'
    template_name = 'tauser/admin/historial_recargas.html'
    
    def get(self, request, terminal_pk):
        terminal = get_object_or_404(Terminal, pk=terminal_pk)
        
        from .models import LogRecargaInventario
        
        # Obtener todos los logs
        logs = LogRecargaInventario.objects.filter(
            terminal=terminal
        ).select_related(
            'denominacion__divisa',
            'usuario'
        ).order_by('-fecha')
        
        # Filtros opcionales
        divisa_filtro = request.GET.get('divisa')
        usuario_filtro = request.GET.get('usuario')
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        if divisa_filtro:
            logs = logs.filter(denominacion__divisa__code=divisa_filtro)
        
        if usuario_filtro:
            logs = logs.filter(usuario__id=usuario_filtro)
        
        if fecha_desde:
            from datetime import datetime
            logs = logs.filter(fecha__date__gte=datetime.strptime(fecha_desde, '%Y-%m-%d').date())
        
        if fecha_hasta:
            from datetime import datetime
            logs = logs.filter(fecha__date__lte=datetime.strptime(fecha_hasta, '%Y-%m-%d').date())
        
        # Estadísticas del período filtrado
        from django.db.models import Sum, Count
        estadisticas = logs.aggregate(
            total_recargas=Count('id'),
            total_billetes=Sum('cantidad_agregada'),
            valor_total=Sum('valor_total_agregado')
        )
        
        # Paginación
        from django.core.paginator import Paginator
        paginator = Paginator(logs, 25)  # 25 registros por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Obtener listas para filtros
        divisas_disponibles = Denominacion.objects.filter(
            inventarios_terminal__terminal=terminal
        ).values_list('divisa__code', flat=True).distinct()
        
        usuarios_disponibles = User.objects.filter(
            recargas_realizadas__terminal=terminal
        ).distinct()
        
        context = {
            'terminal': terminal,
            'page_obj': page_obj,
            'estadisticas': estadisticas,
            'divisas_disponibles': divisas_disponibles,
            'usuarios_disponibles': usuarios_disponibles,
            # Mantener valores de filtros
            'divisa_filtro': divisa_filtro,
            'usuario_filtro': usuario_filtro,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        }
        
        return render(request, self.template_name, context)
