from django import template

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
