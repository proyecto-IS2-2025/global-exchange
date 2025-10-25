"""
Script para eliminar notificaciones duplicadas.
Ejecutar con: python manage.py shell < scripts/limpiar_notificaciones_duplicadas.py
"""

from notificaciones.models import NotificacionTasa
from django.db.models import Count

# Encontrar grupos de notificaciones duplicadas
duplicados = (
    NotificacionTasa.objects
    .values('usuario', 'cliente_asociado', 'divisa', 'tipo_alerta', 'tipo_operacion')
    .annotate(count=Count('id'))
    .filter(count__gt=1)
)

print(f"Encontrados {len(duplicados)} grupos de notificaciones duplicadas")

for dup in duplicados:
    # Obtener todas las notificaciones del grupo duplicado
    notificaciones = NotificacionTasa.objects.filter(
        usuario=dup['usuario'],
        cliente_asociado=dup['cliente_asociado'],
        divisa=dup['divisa'],
        tipo_alerta=dup['tipo_alerta'],
        tipo_operacion=dup['tipo_operacion']
    ).order_by('id')
    
    # Mantener la primera, eliminar las demás
    primera = notificaciones.first()
    duplicadas = notificaciones.exclude(id=primera.id)
    
    count = duplicadas.count()
    if count > 0:
        print(f"Eliminando {count} duplicados de: {primera.divisa} - {primera.get_tipo_alerta_display()}")
        duplicadas.delete()

print("✅ Limpieza completada")
