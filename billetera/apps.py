from django.apps import AppConfig

class BilleteraConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'billetera'

    def ready(self):
        import billetera.signals  # 👈 Esto activa las señales
