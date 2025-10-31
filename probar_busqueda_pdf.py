#!/usr/bin/env python
"""
Script para probar la búsqueda automática de PDFs
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/jose/proyecto_is2/global-exchange')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from facturacion_electronica.models import FacturaElectronica
from facturacion_electronica.utils import buscar_y_actualizar_pdf

def probar_busqueda_pdf():
    """
    Prueba la búsqueda automática de PDFs para facturas aprobadas
    """
    print("=" * 70)
    print("🔍 PRUEBA DE BÚSQUEDA AUTOMÁTICA DE PDFs")
    print("=" * 70)
    
    # Buscar facturas aprobadas sin PDF
    facturas_sin_pdf = FacturaElectronica.objects.filter(
        estado='aprobado'
    ).exclude(
        cdc__isnull=True
    ).exclude(
        cdc='0'
    ).exclude(
        url_kude_pdf__contains='.pdf'
    )
    
    print(f"\n📊 Facturas aprobadas sin PDF completo: {facturas_sin_pdf.count()}")
    
    if not facturas_sin_pdf.exists():
        print("\n✅ Todas las facturas aprobadas tienen su PDF")
        
        # Mostrar algunas facturas con PDF
        facturas_con_pdf = FacturaElectronica.objects.filter(
            estado='aprobado',
            url_kude_pdf__contains='.pdf'
        )[:5]
        
        if facturas_con_pdf.exists():
            print("\n📄 Facturas con PDF encontrado:")
            for f in facturas_con_pdf:
                print(f"  ✓ {f.numero_factura} → {f.url_kude_pdf}")
        
        return
    
    print("\n🔄 Buscando PDFs en el filesystem...\n")
    
    resultados = {
        'encontrados': [],
        'no_encontrados': [],
        'errores': []
    }
    
    for factura in facturas_sin_pdf:
        print(f"📋 {factura.numero_factura} (Estado: {factura.estado}, CDC: {factura.cdc[:20] if factura.cdc else 'N/A'}...)")
        
        try:
            encontrado = buscar_y_actualizar_pdf(factura)
            
            if encontrado:
                factura.refresh_from_db()
                resultados['encontrados'].append(factura)
                print(f"   ✅ PDF ENCONTRADO: {factura.url_kude_pdf}")
            else:
                resultados['no_encontrados'].append(factura)
                print(f"   ⏳ PDF no generado aún")
                
        except Exception as e:
            resultados['errores'].append((factura, str(e)))
            print(f"   ❌ ERROR: {e}")
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN")
    print("=" * 70)
    print(f"✅ PDFs encontrados y actualizados: {len(resultados['encontrados'])}")
    print(f"⏳ PDFs aún no generados: {len(resultados['no_encontrados'])}")
    print(f"❌ Errores: {len(resultados['errores'])}")
    
    if resultados['encontrados']:
        print("\n📄 Facturas con PDF actualizado:")
        for f in resultados['encontrados']:
            print(f"  • {f.numero_factura}")
    
    if resultados['no_encontrados']:
        print("\n⏳ Facturas esperando PDF:")
        for f in resultados['no_encontrados']:
            fecha_str = f.fecha_emision.strftime('%Y%m')
            print(f"  • {f.numero_factura} (Buscar en: /kude/{fecha_str}/)")
    
    if resultados['errores']:
        print("\n❌ Errores encontrados:")
        for f, error in resultados['errores']:
            print(f"  • {f.numero_factura}: {error}")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    try:
        probar_busqueda_pdf()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
