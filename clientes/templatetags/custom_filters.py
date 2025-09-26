# clientes/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filtro para acceder a elementos de diccionario o formulario por clave dinámica
    Uso: {{ form|get_item:field_name }}
    """
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    elif hasattr(dictionary, '__getitem__'):
        try:
            return dictionary[key]
        except (KeyError, IndexError):
            return None
    return None

@register.filter
def add_class(field, css_class):
    """
    Agrega una clase CSS a un campo de formulario
    Uso: {{ field|add_class:"form-control" }}
    """
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        existing_classes = field.field.widget.attrs.get('class', '')
        if css_class not in existing_classes:
            field.field.widget.attrs['class'] = f"{existing_classes} {css_class}".strip()
    return field

@register.filter
def stringformat(value, arg):
    """
    Aplica formato de string de Python
    Uso: {{ campo.id|stringformat:"s" }}
    """
    try:
        return (f"%{arg}") % value
    except:
        return value