#!/usr/bin/env python
"""
Script de prueba para generar factura con número específico (051)
Esto permite probar la funcionalidad sin consumir números nuevos del rango asignado
"""
import os
import sys
import django
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Configurar Django
project_dir = Path(__file__).resolve().parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from facturacion_electronica.services import SQLProxyService
from facturacion_electronica.config import (
    EMISOR_CONFIG,
    TIMBRADO_CONFIG,
    ESI_CONFIG,
    ACTIVIDADES_ECONOMICAS
)
from clientes.models import Cliente

# Colores
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

print(f"\n{CYAN}{'='*70}{RESET}")
print(f"{BOLD}{CYAN}  TEST DE FACTURACIÓN - NÚMERO FIJO 051{RESET}")
print(f"{CYAN}{'='*70}{RESET}\n")

# Datos de prueba
NUMERO_FACTURA_TEST = 51
MONTO_TEST = Decimal('50000.00')  # 50,000 PYG

print(f"{BOLD}📋 Datos de la Factura de Prueba:{RESET}")
print(f"  Número: {GREEN}001-003-{NUMERO_FACTURA_TEST:07d}{RESET}")
print(f"  Monto: {YELLOW}{MONTO_TEST:,.2f} PYG{RESET}")
print(f"  Cliente: Cliente General")
print()

# Obtener cliente
try:
    cliente = Cliente.objects.get(nombre_completo='Cliente General')
    print(f"✅ Cliente encontrado: {cliente.nombre_completo}")
except Cliente.DoesNotExist:
    print(f"❌ Error: Cliente 'Cliente General' no encontrado")
    sys.exit(1)

# Datos del receptor (cliente)
receptor_data = {
    'tipo_contribuyente': 2,  # Persona Jurídica
    'ruc': '80000000',  # RUC genérico para pruebas
    'razon_social': cliente.nombre_completo,
    'pais': '239',  # Paraguay
    'tipo_documento_receptor': 1,  # CI
    'numero_documento_receptor': cliente.documento if hasattr(cliente, 'documento') else '1234567',
    'email': 'cliente@test.com'
}

# Items de la factura
items = [
    {
        'codigo': '001',
        'descripcion': 'Servicio de Cambio de Divisas - TEST',
        'cantidad': 1,
        'precio_unitario': float(MONTO_TEST),
        'ivaTipo': 1,  # Gravado IVA 10%
        'ivaMonto': float(MONTO_TEST * Decimal('0.10') / Decimal('1.10')),
        'montoTotal': float(MONTO_TEST)
    }
]

# Conectar al SQL Proxy
print(f"\n{BOLD}🔌 Conectando al SQL Proxy...{RESET}")
service = SQLProxyService()

if not service.conectar():
    print(f"{RED}❌ No se pudo conectar al SQL Proxy{RESET}")
    sys.exit(1)

print(f"{GREEN}✅ Conectado al SQL Proxy{RESET}")

# Preparar datos de la factura
print(f"\n{BOLD}📝 Preparando datos de la factura...{RESET}")

fecha_actual = datetime.now()
numero_factura_formateado = f"{NUMERO_FACTURA_TEST:07d}"

datos_factura = {
    'establecimiento': TIMBRADO_CONFIG['establecimiento'],
    'punto_expedicion': TIMBRADO_CONFIG['punto_expedicion'],
    'numero_factura': numero_factura_formateado,
    'fecha_emision': fecha_actual.strftime('%Y-%m-%d'),
    'tipo_factura': 1,  # Factura electrónica
    'tipo_emision': 1,  # Normal
    'tipo_transaccion': 1,  # Venta de mercaderías
    'tipo_impuesto': 1,  # IVA
    'moneda': 'PYG',
    'condicion_operacion': 1,  # Contado
    
    # Emisor
    'emisor_ruc': EMISOR_CONFIG['ruc'],
    'emisor_razon_social': EMISOR_CONFIG['nombre'],
    'emisor_nombre_fantasia': 'Global Exchange',
    'emisor_direccion': EMISOR_CONFIG['direccion'],
    'emisor_numero_casa': EMISOR_CONFIG['numero_casa'],
    'emisor_departamento': EMISOR_CONFIG['departamento'],
    'emisor_departamento_desc': EMISOR_CONFIG['departamento_desc'],
    'emisor_ciudad': EMISOR_CONFIG['ciudad'],
    'emisor_ciudad_desc': EMISOR_CONFIG['ciudad_desc'],
    'emisor_telefono': EMISOR_CONFIG['telefono'],
    'emisor_email': EMISOR_CONFIG['email'],
    
    # Receptor
    'receptor_tipo_contribuyente': receptor_data['tipo_contribuyente'],
    'receptor_ruc': receptor_data['ruc'],
    'receptor_razon_social': receptor_data['razon_social'],
    'receptor_pais': receptor_data['pais'],
    'receptor_tipo_documento': receptor_data['tipo_documento_receptor'],
    'receptor_numero_documento': receptor_data['numero_documento_receptor'],
    'receptor_email': receptor_data['email'],
    
    # Timbrado
    'numero_timbrado': TIMBRADO_CONFIG['numero'],
    'fecha_inicio_timbrado': TIMBRADO_CONFIG['fecha_inicio'],
    
    # Totales
    'total_operacion': float(MONTO_TEST),
    'total_iva': float(MONTO_TEST * Decimal('0.10') / Decimal('1.10')),
    'total_a_pagar': float(MONTO_TEST),
    
    # Items
    'items': items
}

print(f"  Establecimiento-Punto: {datos_factura['establecimiento']}-{datos_factura['punto_expedicion']}")
print(f"  Número: {datos_factura['numero_factura']}")
print(f"  Fecha: {datos_factura['fecha_emision']}")
print(f"  Total: {GREEN}{datos_factura['total_a_pagar']:,.2f} PYG{RESET}")

# Insertar en la base de datos del SQL Proxy
print(f"\n{BOLD}💾 Insertando factura en SQL Proxy...{RESET}")

try:
    # Primero verificar si ya existe
    service.cursor.execute("""
        SELECT numero_factura FROM public.factura 
        WHERE establecimiento = %s 
        AND punto_expedicion = %s 
        AND numero_factura = %s
    """, (
        datos_factura['establecimiento'],
        datos_factura['punto_expedicion'],
        datos_factura['numero_factura']
    ))
    
    factura_existente = service.cursor.fetchone()
    
    if factura_existente:
        print(f"{YELLOW}⚠️  La factura 001-003-{numero_factura_formateado} ya existe{RESET}")
        print(f"{CYAN}ℹ️  Esto es normal si estás reutilizando números de prueba{RESET}")
    else:
        # Insertar la factura
        insert_query = """
        INSERT INTO public.factura (
            establecimiento, punto_expedicion, numero_factura,
            fecha_emision, tipo_factura, tipo_emision,
            emisor_ruc, emisor_razon_social,
            receptor_tipo_contribuyente, receptor_ruc, receptor_razon_social,
            total_operacion, total_iva, total_a_pagar,
            estado, numero_timbrado
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id;
        """
        
        service.cursor.execute(insert_query, (
            datos_factura['establecimiento'],
            datos_factura['punto_expedicion'],
            datos_factura['numero_factura'],
            datos_factura['fecha_emision'],
            datos_factura['tipo_factura'],
            datos_factura['tipo_emision'],
            datos_factura['emisor_ruc'],
            datos_factura['emisor_razon_social'],
            datos_factura['receptor_tipo_contribuyente'],
            datos_factura['receptor_ruc'],
            datos_factura['receptor_razon_social'],
            datos_factura['total_operacion'],
            datos_factura['total_iva'],
            datos_factura['total_a_pagar'],
            'PENDIENTE',
            datos_factura['numero_timbrado']
        ))
        
        factura_id = service.cursor.fetchone()['id']
        service.connection.commit()
        
        print(f"{GREEN}✅ Factura insertada con ID: {factura_id}{RESET}")
        
        # Insertar items
        for item in items:
            item_query = """
            INSERT INTO public.factura_item (
                factura_id, codigo, descripcion,
                cantidad, precio_unitario, monto_total
            ) VALUES (%s, %s, %s, %s, %s, %s);
            """
            
            service.cursor.execute(item_query, (
                factura_id,
                item['codigo'],
                item['descripcion'],
                item['cantidad'],
                item['precio_unitario'],
                item['montoTotal']
            ))
        
        service.connection.commit()
        print(f"{GREEN}✅ Items insertados{RESET}")
    
    # Verificar que la factura esté en la BD
    service.cursor.execute("""
        SELECT 
            f.id,
            f.establecimiento,
            f.punto_expedicion,
            f.numero_factura,
            f.estado,
            f.total_a_pagar,
            f.cdc
        FROM public.factura f
        WHERE f.establecimiento = %s 
        AND f.punto_expedicion = %s 
        AND f.numero_factura = %s
    """, (
        datos_factura['establecimiento'],
        datos_factura['punto_expedicion'],
        datos_factura['numero_factura']
    ))
    
    factura = service.cursor.fetchone()
    
    if factura:
        print(f"\n{BOLD}📊 Factura en Base de Datos:{RESET}")
        print(f"  ID: {factura['id']}")
        print(f"  Número: {factura['establecimiento']}-{factura['punto_expedicion']}-{factura['numero_factura']}")
        print(f"  Estado: {YELLOW}{factura['estado']}{RESET}")
        print(f"  Total: {GREEN}{factura['total_a_pagar']:,.2f} PYG{RESET}")
        if factura['cdc']:
            print(f"  CDC: {factura['cdc']}")
        else:
            print(f"  CDC: {YELLOW}Pendiente de generar{RESET}")
    
except Exception as e:
    print(f"{RED}❌ Error: {e}{RESET}")
    service.connection.rollback()
finally:
    service.desconectar()

print(f"\n{CYAN}{'='*70}{RESET}")
print(f"{GREEN}{BOLD}✅ TEST COMPLETADO{RESET}")
print(f"\n{CYAN}La factura de prueba ha sido procesada usando el número 051{RESET}")
print(f"{CYAN}Tu rango 87-150 permanece intacto{RESET}")
print(f"\n{CYAN}{'='*70}{RESET}\n")
