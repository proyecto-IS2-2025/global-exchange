from django.contrib import admin
from .models import StripeTransaction

@admin.register(StripeTransaction)
class StripeTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'payment_intent_id',
        'cliente',
        'transaction_type',
        'amount',
        'currency',
        'status',
        'created_at'
    ]
    list_filter = ['status', 'transaction_type', 'currency', 'created_at']
    search_fields = [
        'payment_intent_id',
        'charge_id',
        'cliente__username',
        'cliente__email'
    ]
    readonly_fields = [
        'payment_intent_id',
        'charge_id',
        'stripe_response',
        'created_at',
        'updated_at'
    ]
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('cliente', 'client_ip')
        }),
        ('Información de la Transacción', {
            'fields': (
                'transaction_type',
                'payment_intent_id',
                'charge_id',
                'status',
                'error_message'
            )
        }),
        ('Montos', {
            'fields': (
                'amount',
                'currency',
                'divisa_code',
                'monto_divisa',
                'tasa_cambio'
            )
        }),
        ('Información de Tarjeta', {
            'fields': ('card_brand', 'card_last4')
        }),
        ('Metadatos', {
            'fields': ('metadata', 'stripe_response'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
