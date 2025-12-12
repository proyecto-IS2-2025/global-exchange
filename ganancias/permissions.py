from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from ganancias.models import RegistroGanancia


def crear_permisos_ganancias():
    """
    Crea permisos personalizados para el módulo de ganancias
    """
    content_type = ContentType.objects.get_for_model(RegistroGanancia)
    
    permisos = [
        {
            'codename': 'view_dashboard_ganancias',
            'name': 'Puede ver el tablero de ganancias',
        },
        {
            'codename': 'view_comparacion_ganancias',
            'name': 'Puede ver comparaciones de ganancias',
        },
        {
            'codename': 'export_reportes_ganancias',
            'name': 'Puede exportar reportes de ganancias',
        },
    ]
    
    for permiso_data in permisos:
        Permission.objects.get_or_create(
            codename=permiso_data['codename'],
            content_type=content_type,
            defaults={'name': permiso_data['name']}
        )
