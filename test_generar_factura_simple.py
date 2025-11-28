#!/usr/bin/env python
"""
Script simplificado para probar la generación de factura usando el servicio
"""
import os
import sys
import django
from pathlib import Path
from decimal import Decimal

# Configurar Django
project_dir = Path(__file__).resolve().parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from transacciones.models import Transaccion
from clientes.models import Cliente
from facturacion_electronica.services import generar_factura_automatica

# Colores
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

print(f"\n{CYAN}{'='*70}{RESET}")
print(f"{BOLD}{CYAN}  TEST DE GENERACIÓN DE FACTURA{RESET}")
print(f"{CYAN}{'='*70}{RESET}\n")

# Buscar una transacción pagada que no tenga factura
print(f"{BOLD}🔍 Buscando transacción de prueba...{RESET}")

try:
    # Buscar la última transacción PAGADA
    transaccion = Transaccion.objects.filter(
        estado='PAGADA'
    ).order_by('-fecha_creacion').first()
    
    if not transaccion:
        print(f"{RED}❌ No hay transacciones PAGADAS en el sistema{RESET}")
        print(f"{YELLOW}Realiza una compra primero en http://localhost{RESET}")
        sys.exit(1)
    
    print(f"{GREEN}✅ Transacción encontrada: {transaccion.numero_transaccion}{RESET}")
    print(f"  Cliente: {transaccion.cliente.nombre_completo}")
    print(f"  Monto origen: {YELLOW}{transaccion.monto_origen:,.2f} {transaccion.divisa_origen.codigo}{RESET}")
    print(f"  Estado: {GREEN}{transaccion.estado}{RESET}")
    
    # Verificar si ya tiene factura
    if hasattr(transaccion, 'factura_electronica') and transaccion.factura_electronica:
        print(f"\n{YELLOW}⚠️  Esta transacción ya tiene factura:{RESET}")
        print(f"  Número: {transaccion.factura_electronica.numero_factura_completo}")
        print(f"{CYAN}ℹ️  Generando factura de todos modos para prueba...{RESET}")
    
    # Intentar generar la factura
    print(f"\n{BOLD}📝 Generando factura automáticamente...{RESET}")
    
    factura = generar_factura_automatica(transaccion)
    
    if factura:
        print(f"\n{GREEN}{BOLD}✅ ¡FACTURA GENERADA EXITOSAMENTE!{RESET}")
        print(f"\n{BOLD}📄 Detalles de la Factura:{RESET}")
        print(f"  Número: {GREEN}{factura.numero_factura_completo}{RESET}")
        print(f"  CDC: {factura.cdc if factura.cdc else f'{YELLOW}Pendiente{RESET}'}")
        print(f"  Estado: {factura.estado}")
        print(f"  Monto: {YELLOW}{factura.monto_total:,.2f} PYG{RESET}")
        print(f"  Fecha: {factura.fecha_emision}")
        
        if factura.pdf_url:
            print(f"  PDF: {CYAN}{factura.pdf_url}{RESET}")
        if factura.xml_url:
            print(f"  XML: {CYAN}{factura.xml_url}{RESET}")
    else:
        print(f"{RED}❌ No se pudo generar la factura{RESET}")
        print(f"{YELLOW}Revisa los logs para más detalles{RESET}")

except Exception as e:
    print(f"{RED}❌ Error: {e}{RESET}")
    import traceback
    traceback.print_exc()

print(f"\n{CYAN}{'='*70}{RESET}\n")
