"""
URLs para la aplicación Stripe
"""
from django.urls import path
from . import views
from . import webhooks

app_name = 'stripe_payments'

urlpatterns = [
    # Lista de transacciones
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    
    # Detalle de transacción
    path('transactions/<int:transaction_id>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    
    # Recibo de transacción
    path('transactions/<int:transaction_id>/receipt/', views.transaction_receipt, name='transaction_receipt'),
    
    # AJAX: Estado de transacción
    path('transactions/<int:transaction_id>/status/', views.transaction_status_ajax, name='transaction_status'),
    
    # Webhook de Stripe
    path('webhook/', webhooks.stripe_webhook, name='webhook'),
]
