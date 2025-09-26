# transacciones/templatetags/transacciones_filters.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def formatear_divisa(valor, codigo_divisa):
    """
    Filtro para formatear montos según el código de divisa.
    - PYG: sin decimales
    - Otras divisas: 2 decimales
    """
    try:
        # Convertir a Decimal si es necesario
        if isinstance(valor, (int, float, str)):
            valor_decimal = Decimal(str(valor))
        else:
            valor_decimal = valor
        
        # Determinar formato según código de divisa
        if str(codigo_divisa).upper() == 'PYG':
            # Guaraníes: sin decimales
            return f"{valor_decimal:.0f}"
        else:
            # Otras divisas: 2 decimales
            return f"{valor_decimal:.2f}"
            
    except (ValueError, TypeError, AttributeError):
        # En caso de error, devolver el valor original
        return str(valor)