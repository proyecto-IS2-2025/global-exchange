import os
from celery import Celery
from celery.schedules import crontab

# Establecer el módulo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')

# Crear la aplicación Celery
app = Celery('casa_de_cambios')

# Cargar configuración desde Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrir tasks en las apps de Django
app.autodiscover_tasks()

# Configurar el schedule para Celery Beat
app.conf.beat_schedule = {
    'procesar-notificaciones-periodicas': {
        'task': 'notificaciones.tasks.procesar_notificaciones_periodicas',
        'schedule': crontab(minute='*/5'),  # Ejecutar cada 5 minutos
    },
}

# Configuración de zona horaria
app.conf.timezone = 'America/Asuncion'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
