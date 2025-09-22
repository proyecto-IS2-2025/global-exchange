# banco/templatetags/banco_tags.py
from django import template

register = template.Library()

@register.simple_tag
def get_banco_styles(entidad):
    if not entidad:
        return {
            'color_principal': '#1d3557',
            'color_secundario': '#457b9d',
            'logo_url': ''
        }
    
    return {
        'color_principal': entidad.color_principal,
        'color_secundario': entidad.color_secundario,
        'logo_url': entidad.logo_url if entidad.logo_url else ''
    }