"""
Vistas para gestión de transacciones Stripe
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import StripeTransaction
from .services import get_transaction_history
import logging

logger = logging.getLogger(__name__)


class TransactionListView(LoginRequiredMixin, ListView):
    """Vista para listar transacciones de Stripe del usuario"""
    model = StripeTransaction
    template_name = 'stripe/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        """Filtrar transacciones por usuario actual"""
        queryset = StripeTransaction.objects.filter(
            cliente=self.request.user
        ).order_by('-created_at')
        
        # Filtros opcionales
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        transaction_type = self.request.GET.get('type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas
        all_transactions = StripeTransaction.objects.filter(cliente=self.request.user)
        context['stats'] = {
            'total': all_transactions.count(),
            'succeeded': all_transactions.filter(status='succeeded').count(),
            'failed': all_transactions.filter(status='failed').count(),
            'pending': all_transactions.filter(status__in=['pending', 'processing', 'requires_action']).count(),
        }
        
        # Filtros activos
        context['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'type': self.request.GET.get('type', ''),
        }
        
        return context


class TransactionDetailView(LoginRequiredMixin, DetailView):
    """Vista para ver detalle de una transacción"""
    model = StripeTransaction
    template_name = 'stripe/transaction_detail.html'
    context_object_name = 'transaction'
    pk_url_kwarg = 'transaction_id'

    def get_queryset(self):
        """Solo permitir ver transacciones propias"""
        return StripeTransaction.objects.filter(cliente=self.request.user)


@login_required
def transaction_receipt(request, transaction_id):
    """Vista para mostrar recibo de transacción"""
    transaction = get_object_or_404(
        StripeTransaction,
        id=transaction_id,
        cliente=request.user
    )
    
    return render(request, 'stripe/transaction_receipt.html', {
        'transaction': transaction
    })


@login_required
def transaction_status_ajax(request, transaction_id):
    """Vista AJAX para obtener estado actual de una transacción"""
    try:
        transaction = StripeTransaction.objects.get(
            id=transaction_id,
            cliente=request.user
        )
        
        return JsonResponse({
            'success': True,
            'status': transaction.status,
            'status_display': transaction.get_status_display(),
            'is_successful': transaction.is_successful,
            'is_pending': transaction.is_pending,
            'is_failed': transaction.is_failed,
            'error_message': transaction.error_message,
        })
        
    except StripeTransaction.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Transacción no encontrada'
        }, status=404)
    except Exception as e:
        logger.error(f"Error en transaction_status_ajax: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno'
        }, status=500)
