"""
Comando de administración para generar cotizaciones por segmento.

Este comando regenera todas las cotizaciones para todas las tasas de cambio existentes.
Útil cuando se configuran nuevos segmentos o cuando las cotizaciones no se generaron correctamente.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from divisas.models import TasaCambio, CotizacionSegmento
from divisas.services import generar_cotizaciones_por_segmento


class Command(BaseCommand):
    help = 'Genera cotizaciones por segmento para todas las tasas de cambio existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerar cotizaciones incluso si ya existen',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        usuario = User.objects.filter(is_superuser=True).first()
        
        if not usuario:
            self.stdout.write(self.style.ERROR('No se encontró un superusuario. Cree uno primero.'))
            return

        tasas = TasaCambio.objects.all()
        
        if not tasas.exists():
            self.stdout.write(self.style.WARNING('No hay tasas de cambio registradas.'))
            return

        self.stdout.write(f'Usuario: {usuario}')
        self.stdout.write(f'Tasas encontradas: {tasas.count()}')
        
        if options['force']:
            self.stdout.write(self.style.WARNING('Modo --force activado. Eliminando cotizaciones existentes...'))
            CotizacionSegmento.objects.all().delete()
        
        cotizaciones_antes = CotizacionSegmento.objects.count()
        
        self.stdout.write('Generando cotizaciones...')
        
        for tasa in tasas:
            try:
                generar_cotizaciones_por_segmento(tasa.divisa, tasa, usuario)
                self.stdout.write(f'  ✓ {tasa.divisa.code}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ {tasa.divisa.code}: {str(e)}'))
        
        cotizaciones_despues = CotizacionSegmento.objects.count()
        nuevas = cotizaciones_despues - cotizaciones_antes
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Proceso completado'))
        self.stdout.write(f'Cotizaciones nuevas: {nuevas}')
        self.stdout.write(f'Total cotizaciones: {cotizaciones_despues}')
        
        # Mostrar resumen
        divisas_con_cotizacion = set([c.divisa.code for c in CotizacionSegmento.objects.all()])
        segmentos_con_cotizacion = set([c.segmento.name for c in CotizacionSegmento.objects.all()])
        
        self.stdout.write(f'\nDivisas con cotización: {", ".join(sorted(divisas_con_cotizacion))}')
        self.stdout.write(f'Segmentos con cotización: {", ".join(sorted(segmentos_con_cotizacion))}')
