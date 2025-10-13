import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from notificaciones.models import NotificacionTasa
from django.utils import timezone

now = timezone.localtime(timezone.now())
print(f"Hora actual: {now.strftime('%H:%M')}")
print()

nots = NotificacionTasa.objects.filter(tipo_alerta='periodica', activa=True)
print(f"Total notificaciones periódicas: {nots.count()}")
print()

for n in nots:
    print(f"ID: {n.id}")
    print(f"Divisa: {n.divisa}")
    print(f"Periodicidad: {n.periodicidad}")
    print(f"Hora: {n.hora_envio}")
    print(f"Usuario: {n.usuario.username}")
    print(f"Última ejecución: {n.ultima_ejecucion}")
    print("-" * 40)
