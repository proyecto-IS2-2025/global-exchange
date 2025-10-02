"""
Funciones utilitarias para la app de clientes.
Helpers y utilidades compartidas.
"""
from decimal import Decimal, InvalidOperation


def safe_decimal(value, default=Decimal('0.00')):
    """Convierte un valor a Decimal de forma segura."""
    try:
        return Decimal(str(value))
    except (ValueError, InvalidOperation, TypeError):
        return default


def validate_cedula(cedula):
    """Valida formato básico de cédula."""
    if not cedula:
        return False
    cedula = cedula.strip()
    return cedula.isdigit() and len(cedula) >= 6


def format_currency(amount, currency='PYG'):
    """Formatea un monto como moneda."""
    try:
        return f"{currency} {amount:,.2f}"
    except (ValueError, InvalidOperation):
        return f"{currency} 0.00"