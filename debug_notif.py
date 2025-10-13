#!/usr/bin/env python
"""Script para debuggear notificaciones periódicas"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from django.utils import timezone
from notificaciones.models import NotificacionTasa
from notificaciones.tasks import debe_enviar_notificacion, es_hora_de_enviar
from datetime import timedelta

ahora = timezone.now()
print(f"=== DEBUG NOTIFICACIONES PERIÓDICAS ===")
print(f"Hora actual del servidor: {ahora}")
print(f"Hora local: {ahora.astimezone()}")
print()

notifs = NotificacionTasa.objects.filter(tipo_alerta='periodica', activa=True)
print(f"Total notificaciones periódicas activas: {notifs.count()}\n")

for notif in notifs:
    print(f"--- Notificación ID: {notif.id} ---")
    print(f"Usuario: {notif.usuario.username}")
    print(f"Divisa: {notif.divisa}")
    print(f"Periodicidad: {notif.periodicidad}")
    print(f"Hora configurada: {notif.hora_envio}")
    print(f"Última ejecución: {notif.ultima_ejecucion}")
    
    # Calcular la hora configurada con zona horaria (NUEVA LÓGICA)
    ahora_local = ahora.astimezone()
    hora_configurada = timezone.datetime.combine(ahora_local.date(), notif.hora_envio)
    hora_configurada = timezone.make_aware(hora_configurada, timezone=ahora_local.tzinfo)
    print(f"Hora configurada (aware): {hora_configurada}")
    
    # Calcular ventana
    ventana_inicio = hora_configurada - timedelta(minutes=3)
    ventana_fin = hora_configurada + timedelta(minutes=3)
    print(f"Ventana: {ventana_inicio.strftime('%H:%M:%S')} - {ventana_fin.strftime('%H:%M:%S')}")
    print(f"Ahora está en ventana: {ventana_inicio <= ahora_local <= ventana_fin}")
    
    # Verificar si debe enviar
    es_hora = es_hora_de_enviar(notif, ahora)
    debe_enviar = debe_enviar_notificacion(notif, ahora)
    
    print(f"es_hora_de_enviar(): {es_hora}")
    print(f"debe_enviar_notificacion(): {debe_enviar}")
    print()
