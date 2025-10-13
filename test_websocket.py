"""
Script de prueba para verificar el envío de notificaciones WebSocket.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from notificaciones.tasks import enviar_notificacion_websocket
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("PRUEBA DE NOTIFICACIÓN WEBSOCKET")
print("=" * 60)
print()

# Obtener el usuario
try:
    user = User.objects.get(username='user1')
    print(f"✓ Usuario encontrado: {user.username} (ID: {user.id})")
    print()
    
    # Enviar notificación de prueba
    print("Enviando notificación de prueba vía WebSocket...")
    enviar_notificacion_websocket(
        user.id,
        "🧪 Esta es una notificación de prueba en tiempo real"
    )
    print("✓ Notificación enviada")
    print()
    print("Si el WebSocket está conectado, deberías ver un toast en el navegador AHORA.")
    print()
    
except User.DoesNotExist:
    print("❌ Usuario 'user1' no encontrado")
    print("Usuarios disponibles:")
    for u in User.objects.all()[:5]:
        print(f"  - {u.username}")

print("=" * 60)
