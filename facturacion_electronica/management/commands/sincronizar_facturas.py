"""
Management command para sincronizar facturas automáticamente
Uso:
    python manage.py sincronizar_facturas
    
Para ejecutar en bucle cada 30 segundos:
    python manage.py sincronizar_facturas --loop
"""
import time
import glob
import os
from django.core.management.base import BaseCommand
from facturacion_electronica.models import FacturaElectronica
from facturacion_electronica.utils import actualizar_estado_factura
from facturacion_electronica.config import SQL_PROXY_CONFIG


class Command(BaseCommand):
    help = 'Sincroniza facturas pendientes con SQL Proxy y actualiza URLs de PDFs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loop',
            action='store_true',
            help='Ejecutar continuamente cada 30 segundos',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Intervalo en segundos entre sincronizaciones (default: 30)',
        )

    def handle(self, *args, **options):
        loop = options['loop']
        interval = options['interval']
        
        if loop:
            self.stdout.write(self.style.SUCCESS(
                f'🔄 Iniciando sincronización automática cada {interval} segundos...'
            ))
            self.stdout.write(self.style.WARNING('Presiona Ctrl+C para detener'))
            
            try:
                while True:
                    self.sincronizar()
                    time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\n⏹️  Sincronización detenida'))
        else:
            self.sincronizar()

    def sincronizar(self):
        """Sincroniza facturas pendientes"""
        # 1. Buscar facturas sin CDC o en estado confirmado
        facturas_pendientes = FacturaElectronica.objects.filter(
            estado__in=['confirmado', 'borrador']
        ) | FacturaElectronica.objects.filter(cdc__isnull=True)
        
        # 2. Buscar facturas aprobadas sin URL de PDF
        facturas_sin_pdf = FacturaElectronica.objects.filter(
            estado='aprobado',
            cdc__isnull=False
        ).exclude(
            url_kude_pdf__contains='.pdf'
        )
        
        total_pendientes = facturas_pendientes.count()
        total_sin_pdf = facturas_sin_pdf.count()
        
        if total_pendientes == 0 and total_sin_pdf == 0:
            self.stdout.write(self.style.SUCCESS('✅ Todas las facturas están sincronizadas'))
            return
        
        self.stdout.write(f'\n📊 Facturas pendientes: {total_pendientes}')
        self.stdout.write(f'📄 Facturas sin PDF: {total_sin_pdf}\n')
        
        actualizadas = 0
        pdfs_encontrados = 0
        
        # Sincronizar estados
        for factura in facturas_pendientes:
            try:
                resultado = actualizar_estado_factura(factura)
                if resultado:
                    factura.refresh_from_db()
                    if factura.estado == 'aprobado':
                        self.stdout.write(self.style.SUCCESS(
                            f'✅ {factura.numero_factura} - APROBADA'
                        ))
                        actualizadas += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'❌ Error en {factura.numero_factura}: {e}'
                ))
        
        # Buscar PDFs
        for factura in list(facturas_pendientes) + list(facturas_sin_pdf):
            if factura.estado == 'aprobado':
                if self.buscar_y_actualizar_pdf(factura):
                    pdfs_encontrados += 1
        
        if actualizadas > 0 or pdfs_encontrados > 0:
            self.stdout.write(self.style.SUCCESS(
                f'\n📊 Resumen: {actualizadas} aprobadas, {pdfs_encontrados} PDFs encontrados'
            ))

    def buscar_y_actualizar_pdf(self, factura):
        """Busca el PDF en el sistema de archivos y actualiza la URL"""
        fecha_str = factura.fecha_emision.strftime('%Y%m')
        pdf_pattern = f'/home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/{fecha_str}/{factura.numero_factura}_*.pdf'
        pdfs = glob.glob(pdf_pattern)
        
        if pdfs:
            pdf_file = os.path.basename(pdfs[0])
            nueva_url = f"http://localhost:40080/kude/{fecha_str}/{pdf_file}"
            
            if factura.url_kude_pdf != nueva_url:
                factura.url_kude_pdf = nueva_url
                factura.save(update_fields=['url_kude_pdf'])
                self.stdout.write(self.style.SUCCESS(
                    f'📄 PDF encontrado: {factura.numero_factura}'
                ))
                return True
        
        return False
