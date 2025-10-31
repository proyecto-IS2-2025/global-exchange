# operacion_divisas/views_seleccionar_tauser.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from decimal import Decimal
import logging

from tauser.models import Terminal
from divisas.models import Divisa
from roles.decorators import require_permission
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)


@method_decorator(require_permission("divisas.realizar_operacion", check_client_assignment=True), name="dispatch")
class SeleccionarTauserCompraView(LoginRequiredMixin, TemplateView):
    """
    Vista para seleccionar el tauser donde se retirará la divisa comprada.
    Solo muestra tausers que tengan stock disponible (considerando reservas).
    """
    template_name = "operaciones/compra/seleccionar_tauser.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # Obtener operación de la sesión
        operacion = self.request.session.get("operacion")
        
        if not operacion:
            messages.error(self.request, "No hay operación activa.")
            return ctx
        
        # Obtener código de divisa y monto
        codigo_divisa = operacion.get('divisa', '').strip().upper()
        monto_divisa_str = operacion.get('monto_divisa', '0')
        
        try:
            monto_divisa = Decimal(str(monto_divisa_str))
        except (ValueError, TypeError):
            logger.error(f"Error al convertir monto_divisa: {monto_divisa_str}")
            messages.error(self.request, "Error en el monto de la operación.")
            return ctx
        
        try:
            divisa = Divisa.objects.get(code__iexact=codigo_divisa, is_active=True)
        except Divisa.DoesNotExist:
            logger.error(f"Divisa no encontrada: {codigo_divisa}")
            messages.error(self.request, f"Divisa {codigo_divisa} no encontrada.")
            return ctx
        
        # Obtener tausers activos
        terminales = Terminal.objects.filter(is_activa=True).prefetch_related(
            'inventario_denominaciones__denominacion'
        ).order_by('nombre')
        
        # Filtrar tausers con stock disponible para el monto
        tausers_disponibles = []
        
        for terminal in terminales:
            # Verificar si tiene stock disponible considerando reservas
            puede_entregar, desglose, disponibilidad = terminal.tiene_denominaciones_disponibles_para_retiro(
                divisa, monto_divisa
            )
            
            if puede_entregar:
                # Calcular stock total disponible
                stock_total = Decimal('0')
                stock_reservado = Decimal('0')
                
                for inv_id, info in disponibilidad.items():
                    inv = desglose[inv_id]['inventario']
                    stock_total += inv.denominacion.valor * info['cantidad_total']
                    cantidad_reservada = info['cantidad_total'] - info['cantidad_disponible']
                    stock_reservado += inv.denominacion.valor * cantidad_reservada
                
                tausers_disponibles.append({
                    'terminal': terminal,
                    'desglose': desglose,
                    'disponibilidad': disponibilidad,
                    'stock_total': stock_total,
                    'stock_reservado': stock_reservado,
                    'stock_disponible': stock_total - stock_reservado,
                })
        
        ctx['operacion'] = operacion
        ctx['divisa'] = divisa
        ctx['monto_divisa'] = monto_divisa
        ctx['tausers_disponibles'] = tausers_disponibles
        
        return ctx

    def post(self, request, *args, **kwargs):
        """Guardar el tauser seleccionado en sesión"""
        terminal_id = request.POST.get('terminal_id')
        
        if not terminal_id:
            messages.error(request, "Debe seleccionar un tauser.")
            return redirect('operacion_divisas:seleccionar_tauser_compra')
        
        try:
            terminal = Terminal.objects.get(id=terminal_id, is_activa=True)
            
            # Guardar en sesión
            request.session['tauser_seleccionado'] = {
                'id': terminal.id,
                'nombre': terminal.nombre,
                'codigo': terminal.codigo,
                'ubicacion': terminal.ubicacion,
            }
            request.session.modified = True
            
            # Redirigir a selección de medio de pago (NUEVO)
            return redirect('clientes:seleccionar_medio_pago')
            
        except Terminal.DoesNotExist:
            messages.error(request, "Terminal no encontrada.")
            return redirect('operacion_divisas:seleccionar_tauser_compra')
