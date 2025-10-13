"""
Routing de Django Channels para WebSockets.
Define las rutas WebSocket de la aplicación.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notificaciones/$', consumers.NotificacionConsumer.as_asgi()),
]
