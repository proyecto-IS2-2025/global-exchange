from django import template
from decimal import Decimal
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Template filter para acceder a valores de diccionario por clave.
    Uso: {{ mi_diccionario|get_item:clave }}
    """
    if dictionary is None:
        return 0
    return dictionary.get(key, 0)


@register.filter(name='divisa_format')
def divisa_format(valor, codigo_divisa=None):
    """
    Formatea un valor según el tipo de divisa.
    - Todas las divisas: sin decimales (ej: 150.000 PYG, 100 USD)
    
    Uso: {{ monto|divisa_format:divisa.code }}
    O simplemente: {{ monto|divisa_format }}
    """
    try:
        # Validar que el valor no sea None o vacío
        if valor is None or valor == '':
            return '0'
        
        # Si ya es Decimal, usarlo directamente
        if isinstance(valor, Decimal):
            valor_decimal = valor
        else:
            # Intentar convertir a string primero, luego a Decimal
            valor_str = str(valor).strip()
            
            # Si el string está vacío después del strip, retornar 0
            if not valor_str:
                return '0'
            
            # Convertir a Decimal
            valor_decimal = Decimal(valor_str)
        
        # Redondear a entero
        valor_entero = int(round(float(valor_decimal)))
        
        # Formatear con separadores de miles usando intcomma
        return intcomma(valor_entero)
        
    except (ValueError, TypeError, AttributeError, Exception) as e:
        # Si hay cualquier error, intentar retornar el valor original
        # o '0' si no se puede
        try:
            return str(valor) if valor is not None else '0'
        except:
            return '0'


@register.filter(name='divisa_format_with_symbol')
def divisa_format_with_symbol(valor, divisa_obj):
    """
    Formatea un valor con el símbolo de la divisa, SIN decimales.
    
    Uso: {{ monto|divisa_format_with_symbol:divisa }}
    """
    try:
        if not divisa_obj:
            return valor
        
        # Obtener símbolo
        simbolo = getattr(divisa_obj, 'simbolo', None) or getattr(divisa_obj, 'symbol', '$')
        codigo = getattr(divisa_obj, 'code', None)
        
        # Formatear valor sin decimales
        valor_formateado = divisa_format(valor, codigo)
        
        return f"{simbolo}{valor_formateado}"
        
    except (AttributeError, TypeError):
        return valor


@register.filter(name='currency')
def currency(valor):
    """
    Alias simplificado para formatear montos sin decimales.
    Aplicable a todas las divisas en TAUSER.
    
    Uso: {{ monto|currency }}
    """
    if valor is None or valor == '':
        return '0'
    return divisa_format(valor)

