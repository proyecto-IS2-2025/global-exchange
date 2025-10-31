#!/usr/bin/env python3
"""
Script para generar una nueva factura con los datos corregidos.
Esta factura debería ser aprobada por SIFEN.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/home/jose/proyecto_is2/global-exchange')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from facturacion_electronica.services import generar_factura_automatica
from decimal import Decimal

# Datos de la factura
datos_factura = {
    'transaccion_id': 'TRX-TEST-' + str(int(os.urandom(4).hex(), 16)),
    'monto_total': Decimal('150000.00'),  # 150,000 PYG
    'moneda_origen': 'USD',
    'moneda_destino': 'PYG',
    'monto_origen': Decimal('20.00'),  # 20 USD
    'tasa_cambio': Decimal('7500.00'),
    'cliente_id': 1,
    'cliente_nombre': 'GLOBAL EXCHANGE SA',  # Mismo nombre del emisor para pruebas
    'cliente_email': 'glex.globalexchange@gmail.com',
    'cliente_ruc': '2595733',  # Mismo RUC del emisor
    'cliente_dv': '3',  # Mismo DV del emisor
    'items': [
        {
            'descripcion': 'Compra de USD 20.00 a tasa 7500.00',
            'cantidad': 1,
            'precio_unitario': Decimal('150000.00'),
            'descuento': Decimal('0.00'),
            'afectacion_iva': '1',  # 1 = Gravado IVA
            'proporcion_iva': '100',  # 100%
            'tasa_iva': '10'  # 10%
        }
    ]
}

print("=" * 80)
print("GENERANDO NUEVA FACTURA CON DATOS CORREGIDOS")
print("=" * 80)
print(f"\nTransacción: {datos_factura['transaccion_id']}")
print(f"Monto Total: {datos_factura['monto_total']} PYG")
print(f"Cliente: {datos_factura['cliente_nombre']}")
print(f"RUC: {datos_factura['cliente_ruc']}-{datos_factura['cliente_dv']}")
print("\n" + "=" * 80)

try:
    resultado = generar_factura_automatica(datos_factura)
    
    if resultado['exito']:
        print("\n✅ FACTURA GENERADA EXITOSAMENTE")
        print(f"   Número de factura: {resultado.get('numero_factura', 'N/A')}")
        print(f"   ID en Django: {resultado.get('factura_id', 'N/A')}")
        print(f"   Fecha: {resultado.get('fecha_emision', 'N/A')}")
        
        print("\n📋 DETALLES:")
        print(f"   - Establecimiento: 001")
        print(f"   - Punto: 003")
        print(f"   - Estado inicial: Confirmado")
        print(f"   - Cliente RUC: {datos_factura['cliente_ruc']}-{datos_factura['cliente_dv']}")
        
        print("\n⏳ PRÓXIMOS PASOS:")
        print("   1. El scheduler procesará la factura en ~20 segundos")
        print("   2. La enviará a SIFEN para aprobación")
        print("   3. SIFEN debería APROBAR (no rechazar) porque el RUC es válido")
        print("   4. Espera 1-2 minutos y verifica el estado con:")
        print(f"      docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \"SELECT dnumdoc, estado, estado_sifen, desc_sifen FROM public.de WHERE dnumdoc = '{resultado.get('numero_factura', '')}';\"")
        
        print("\n🎯 OBJETIVO:")
        print("   Estado esperado: 'Aprobado' o 'Sol.Aprobacion'")
        print("   Si es 'Aprobado', el PDF estará disponible en:")
        print(f"   http://localhost:40080/kude/{resultado.get('numero_factura', '')}.pdf")
        
    else:
        print("\n❌ ERROR AL GENERAR FACTURA")
        print(f"   Mensaje: {resultado.get('mensaje', 'Error desconocido')}")
        
except Exception as e:
    print(f"\n❌ EXCEPCIÓN: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
