# banco/templatetags/banco_tags.py
from django import template

register = template.Library()

@register.simple_tag
def get_tipo_display(movimiento):
    """Devuelve el tipo de movimiento legible"""
    if hasattr(movimiento, 'cuenta_origen') and hasattr(movimiento, 'cuenta_destino'):
        return "Transferencia"
    elif hasattr(movimiento, 'tipo'):
        return f"Pago {movimiento.get_tipo_display()}"
    return "Movimiento"

@register.simple_tag
def get_movimiento_tipo(movimiento):
    """Determina el tipo de movimiento para el template"""
    if hasattr(movimiento, 'cuenta_origen') and hasattr(movimiento, 'cuenta_destino'):
        return 'TRANSFERENCIA'
    elif hasattr(movimiento, 'tipo'):
        return f'PAGO_{movimiento.tipo}'
    return 'DESCONOCIDO'

@register.filter
def currency_format(value):
    """Formatea el valor como moneda paraguaya"""
    try:
        return f"₲ {float(value):,.2f}".replace(',', '.')
    except (ValueError, TypeError):
        return "₲ 0.00"

@register.filter
def absolute(value):
    """Devuelve el valor absoluto de un número."""
    return abs(value)

@register.filter
def is_transferencia_billetera(movimiento):
    """Comprueba si el objeto de movimiento es una TransferenciaBilleteraABanco."""
    return isinstance(movimiento, TransferenciaBilleteraABanco)