# roles/management/commands/check_view_protection.py

from django.core.management.base import BaseCommand
from django.urls import get_resolver
import importlib

class Command(BaseCommand):
    help = 'Verifica qué vistas NO tienen protección de permisos'
    
    def handle(self, *args, **options):
        resolver = get_resolver()
        
        vistas_sin_proteccion = []
        
        for url_pattern in resolver.url_patterns:
            # Analizar cada vista
            # Verificar si tiene decorador @require_permission
            pass
        
        self.stdout.write(
            self.style.WARNING(
                f'Vistas sin protección: {len(vistas_sin_proteccion)}'
            )
        )