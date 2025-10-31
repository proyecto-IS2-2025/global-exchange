#!/usr/bin/env python3
"""
Script para registrar manualmente la factura que se creó en SQL Proxy
pero no se guardó en Django debido al error de configuración
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from transacciones.models import Transaccion
from facturacion_electronica.models import FacturaElectronica
from facturacion_electronica.config import TIMBRADO_CONFIG, SQL_PROXY_CONFIG

# Datos de la factura creada
numero_transaccion = 'TRX-20251030-422D39'
de_id = 8
numero_documento = '0000058'

try:
    # Buscar la transacción
    transaccion = Transaccion.objects.get(numero_transaccion=numero_transaccion)
    print(f"✓ Transacción encontrada: {transaccion.numero_transaccion}")
    print(f"  Cliente: {transaccion.cliente.nombre_completo}")
    print(f"  Monto: Gs. {transaccion.monto_origen:,.0f}")
    
    # Verificar si ya tiene factura
    if hasattr(transaccion, 'factura_electronica'):
        print(f"⚠️  La transacción ya tiene factura: {transaccion.factura_electronica.numero_factura}")
    else:
        # Crear la factura
        numero_completo = f"{TIMBRADO_CONFIG['establecimiento']}-{TIMBRADO_CONFIG['punto_expedicion']}-{numero_documento}"
        
        factura = FacturaElectronica.objects.create(
            transaccion=transaccion,
            numero_factura=numero_completo,
            establecimiento=TIMBRADO_CONFIG['establecimiento'],
            punto_expedicion=TIMBRADO_CONFIG['punto_expedicion'],
            numero_documento=numero_documento,
            de_id=de_id,
            estado='confirmado',
            estado_sifen='Procesando',
            descripcion_sifen='Factura enviada al SIFEN para procesamiento',
            url_kude_pdf=f"{SQL_PROXY_CONFIG['kude_url']}/{numero_documento}.pdf",
            url_kude_xml=f"{SQL_PROXY_CONFIG['kude_url']}/{numero_documento}.xml",
            datos_factura={
                'cliente_ruc': '0',
                'cliente_dv': '0',
                'cliente_nombre': transaccion.cliente.nombre_completo,
                'cliente_email': transaccion.cliente.email or 'sin_email@globalexchange.com',
                'items': [{
                    'descripcion': f'Compra de {transaccion.monto_destino} {transaccion.divisa_destino.code}',
                    'cantidad': 1,
                    'precio_unitario': float(transaccion.monto_origen)
                }]
            }
        )
        
        print(f"\n✅ Factura registrada exitosamente!")
        print(f"   Número: {factura.numero_factura}")
        print(f"   DE ID: {factura.de_id}")
        print(f"   PDF: {factura.url_kude_pdf}")
        print(f"\n📄 Ahora el cliente puede ver y descargar la factura desde 'Mis Facturas'")

except Transaccion.DoesNotExist:
    print(f"❌ No se encontró la transacción: {numero_transaccion}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
