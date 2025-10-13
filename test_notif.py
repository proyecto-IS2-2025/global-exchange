#!/usr/bin/env python
"""Script para probar el envío de notificaciones periódicas"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from notificaciones.models import NotificacionTasa, Notificacion
from notificaciones.tasks import enviar_reporte_periodico

# Obtener la notificación periódica
notif = NotificacionTasa.objects.filter(tipo_alerta='periodica', activa=True).first()

if notif:
    print(f"=== Probando notificación {notif.id} ===")
    print(f"Usuario: {notif.usuario.username}")
    print(f"Divisa: {notif.divisa}")
    print(f"Cliente: {notif.cliente_asociado}")
    print(f"Segmento: {notif.cliente_asociado.segmento}")
    print(f"Periodicidad: {notif.periodicidad}")
    print(f"Hora: {notif.hora_envio}")
    print()
    
    count_before = Notificacion.objects.count()
    print(f"Notificaciones antes: {count_before}")
    
    try:
        enviar_reporte_periodico(notif)
        print("✓ Función ejecutada sin errores")
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    count_after = Notificacion.objects.count()
    print(f"Notificaciones después: {count_after}")
    print(f"Nuevas notificaciones: {count_after - count_before}")
    
    if count_after > count_before:
        latest = Notificacion.objects.latest('fecha_creacion')
        print(f"\n=== Última notificación creada ===")
        print(f"Título: {latest.titulo}")
        print(f"Tipo: {latest.tipo}")
        print(f"Usuario: {latest.usuario.username}")
        print(f"Mensaje:\n{latest.mensaje}")
else:
    print("No se encontraron notificaciones periódicas activas")
