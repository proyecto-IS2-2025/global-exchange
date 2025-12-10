from django.core.management.base import BaseCommand
from transacciones.models import Transaccion
from ganancias.models import RegistroGanancia, ResumenGananciaDiaria, ResumenGananciaMensual
from django.utils import timezone


class Command(BaseCommand):
    help = 'Calcula las ganancias de todas las transacciones completadas y actualiza los resúmenes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recalcular',
            action='store_true',
            help='Recalcula ganancias incluso si ya existen registros',
        )

    def handle(self, *args, **options):
        recalcular = options['recalcular']
        
        self.stdout.write('Iniciando cálculo de ganancias...')
        
        # Obtener transacciones completadas
        if recalcular:
            transacciones = Transaccion.objects.filter(estado__in=['completado', 'pagada'])
            self.stdout.write(f'Modo recalcular: Procesando {transacciones.count()} transacciones completadas/pagadas')
        else:
            transacciones = Transaccion.objects.filter(
                estado__in=['completado', 'pagada']
            ).exclude(
                ganancia__isnull=False
            )
            self.stdout.write(f'Procesando {transacciones.count()} transacciones sin registro de ganancia')
        
        registros_creados = 0
        registros_actualizados = 0
        errores = 0
        
        for transaccion in transacciones:
            try:
                registro = RegistroGanancia.calcular_ganancia_transaccion(transaccion)
                if registro:
                    if hasattr(registro, '_state') and registro._state.adding:
                        registros_creados += 1
                    else:
                        registros_actualizados += 1
                    
                    if (registros_creados + registros_actualizados) % 100 == 0:
                        self.stdout.write(f'Procesadas {registros_creados + registros_actualizados} transacciones...')
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error al procesar transacción {transaccion.numero_transaccion}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nRegistros creados: {registros_creados}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Registros actualizados: {registros_actualizados}'
            )
        )
        if errores > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'Errores: {errores}'
                )
            )
        
        # Actualizar resúmenes diarios y mensuales
        self.stdout.write('\nActualizando resúmenes diarios y mensuales...')
        
        fechas = RegistroGanancia.objects.values_list('fecha_transaccion__date', flat=True).distinct()
        
        for fecha in fechas:
            ResumenGananciaDiaria.actualizar_resumen(fecha)
            ResumenGananciaMensual.actualizar_resumen(fecha.year, fecha.month)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Proceso completado exitosamente'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'  - Registros de ganancia: {registros_creados + registros_actualizados}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'  - Resúmenes actualizados: {len(fechas)} días'
            )
        )
