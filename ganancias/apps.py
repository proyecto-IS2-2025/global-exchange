from django.apps import AppConfig


class GananciasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ganancias'
    verbose_name = 'Ganancias'
    
    def ready(self):
        import ganancias.signals
