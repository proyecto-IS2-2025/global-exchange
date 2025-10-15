"""
Consumer de Django Channels para notificaciones en tiempo real.
Maneja conexiones WebSocket y envía notificaciones instantáneas a los usuarios.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificacionConsumer(AsyncWebsocketConsumer):
    """
    Consumer que maneja las conexiones WebSocket para notificaciones.
    Cada usuario tiene su propio grupo de notificaciones.
    """
    
    async def connect(self):
        """
        Ejecutado cuando un cliente se conecta al WebSocket.
        """
        # Obtener el usuario de la sesión
        self.user = self.scope['user']
        
        # Solo permitir conexiones de usuarios autenticados
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Nombre del grupo: notificaciones_{user_id}
        self.group_name = f'notificaciones_{self.user.id}'
        
        # Unirse al grupo de notificaciones del usuario
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Aceptar la conexión
        await self.accept()
        
        # Enviar mensaje de confirmación
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado al sistema de notificaciones en tiempo real'
        }))
        
        print(f"✓ Usuario {self.user.username} conectado a notificaciones WebSocket")
    
    async def disconnect(self, close_code):
        """
        Ejecutado cuando un cliente se desconecta del WebSocket.
        """
        if hasattr(self, 'group_name'):
            # Salir del grupo de notificaciones
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            print(f"✗ Usuario {self.user.username} desconectado de notificaciones WebSocket")
    
    async def receive(self, text_data):
        """
        Ejecutado cuando se recibe un mensaje del cliente.
        Puede usarse para marcar notificaciones como leídas desde el frontend.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Responder a ping para mantener conexión activa
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
            elif message_type == 'mark_read':
                # Marcar notificación como leída
                notificacion_id = data.get('notificacion_id')
                await self.marcar_notificacion_leida(notificacion_id)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato de mensaje inválido'
            }))
    
    async def notificacion_nueva(self, event):
        """
        Ejecutado cuando se envía una notificación nueva al grupo.
        Este método es llamado por group_send desde las tareas de Celery.
        """
        mensaje = event.get('mensaje', '')
        
        # Obtener el conteo actualizado de notificaciones pendientes
        conteo_pendientes = await self.get_notificaciones_pendientes()
        
        # Enviar notificación al WebSocket
        await self.send(text_data=json.dumps({
            'type': 'nueva_notificacion',
            'mensaje': mensaje,
            'notificaciones_pendientes': conteo_pendientes,
            'timestamp': event.get('timestamp', '')
        }))
    
    async def notificacion_cambio_tasa(self, event):
        """
        Ejecutado cuando hay un cambio de tasa que genera notificación.
        """
        divisa = event.get('divisa', '')
        tipo_operacion = event.get('tipo_operacion', '')
        nuevo_valor = event.get('nuevo_valor', '')
        
        # Obtener el conteo actualizado
        conteo_pendientes = await self.get_notificaciones_pendientes()
        
        # Enviar notificación específica de cambio de tasa
        await self.send(text_data=json.dumps({
            'type': 'cambio_tasa',
            'divisa': divisa,
            'tipo_operacion': tipo_operacion,
            'nuevo_valor': nuevo_valor,
            'notificaciones_pendientes': conteo_pendientes
        }))
    
    @database_sync_to_async
    def get_notificaciones_pendientes(self):
        """
        Obtiene el conteo de notificaciones pendientes del usuario.
        """
        from .models import Notificacion
        return Notificacion.objects.filter(
            usuario=self.user,
            estado_lectura='pendiente'
        ).count()
    
    @database_sync_to_async
    def marcar_notificacion_leida(self, notificacion_id):
        """
        Marca una notificación como leída.
        """
        from .models import Notificacion
        try:
            notif = Notificacion.objects.get(
                id=notificacion_id,
                usuario=self.user
            )
            notif.estado_lectura = 'leida'
            notif.save()
            return True
        except Notificacion.DoesNotExist:
            return False
