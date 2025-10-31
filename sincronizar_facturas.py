#!/usr/bin/env python
"""
Script para sincronizar facturas pendientes con SQL Proxy
- Actualiza estados desde SIFEN
- Actualiza URLs de PDF/XML cuando están disponibles
"""
import os
import sys
import glob
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
import django
django.setup()

from facturacion_electronica.models import FacturaElectronica
from facturacion_electronica.utils import actualizar_estado_factura
from facturacion_electronica.config import SQL_PROXY_CONFIG


def actualizar_url_pdf(factura):
    """
    Busca el PDF real en el sistema de archivos y actualiza la URL
    """
    if factura.estado != 'aprobado' or not factura.cdc:
        return False
    
    # Formato del archivo: 001-003-0000071_20251030_235521_531975.pdf
    fecha_str = factura.fecha_emision.strftime('%Y%m')
    
    # Buscar el PDF en el directorio
    pdf_pattern = f'/home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/{fecha_str}/{factura.numero_factura}_*.pdf'
    pdfs = glob.glob(pdf_pattern)
    
    if pdfs:
        pdf_file = os.path.basename(pdfs[0])
        nueva_url = f"{SQL_PROXY_CONFIG['kude_url']}/{fecha_str}/{pdf_file}"
        
        if factura.url_kude_pdf != nueva_url:
            factura.url_kude_pdf = nueva_url
            factura.save(update_fields=['url_kude_pdf'])
            print(f"  ✅ URL PDF actualizada: {nueva_url}")
            return True
    
    return False


def main():
    """
    Sincroniza todas las facturas pendientes
    """
    print("╔" + "="*68 + "╗")
    print("║  🔄 SINCRONIZACIÓN DE FACTURAS CON SIFEN                          ║")
    print("╚" + "="*68 + "╝\n")
    
    # Buscar facturas pendientes (sin CDC o en estado confirmado/procesando)
    facturas_pendientes = FacturaElectronica.objects.filter(
        estado__in=['confirmado', 'borrador']
    ) | FacturaElectronica.objects.filter(cdc__isnull=True)
    
    print(f"📊 Facturas pendientes de sincronización: {facturas_pendientes.count()}\n")
    
    actualizadas = 0
    aprobadas = 0
    rechazadas = 0
    
    for factura in facturas_pendientes:
        print(f"🔍 Procesando: {factura.numero_factura}")
        print(f"   Estado actual: {factura.estado}")
        
        try:
            # Actualizar desde SQL Proxy
            resultado = actualizar_estado_factura(factura)
            
            if resultado:
                factura.refresh_from_db()
                print(f"   Nuevo estado: {factura.estado}")
                
                if factura.estado == 'aprobado':
                    aprobadas += 1
                    print(f"   ✅ APROBADA - CDC: {factura.cdc}")
                    
                    # Actualizar URL del PDF
                    if actualizar_url_pdf(factura):
                        print(f"   📄 PDF disponible")
                elif factura.estado == 'rechazado':
                    rechazadas += 1
                    print(f"   ❌ RECHAZADA - {factura.descripcion_sifen}")
                
                actualizadas += 1
            else:
                print(f"   ⏸️  Sin cambios")
                
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
        
        print()
    
    print("╔" + "="*68 + "╗")
    print("║  📊 RESUMEN                                                        ║")
    print("╠" + "="*68 + "╣")
    print(f"║  Total actualizadas: {actualizadas:>2}                                              ║")
    print(f"║  Aprobadas:          {aprobadas:>2}                                              ║")
    print(f"║  Rechazadas:         {rechazadas:>2}                                              ║")
    print("╚" + "="*68 + "╝")


if __name__ == '__main__':
    main()
