#!/usr/bin/env python
"""
Script para verificar la configuración de facturación desde variables de entorno
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
project_dir = Path(__file__).resolve().parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from facturacion_electronica.config import FACTURACION_CONFIG, TIMBRADO_CONFIG, SQL_PROXY_CONFIG, KUDE_CONFIG

# Colores
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

print(f"\n{CYAN}{'='*70}{RESET}")
print(f"{BOLD}{CYAN}  VERIFICACIÓN DE CONFIGURACIÓN DE FACTURACIÓN ELECTRÓNICA{RESET}")
print(f"{CYAN}{'='*70}{RESET}\n")

# Variables de entorno
print(f"{BOLD}📝 Variables de Entorno (.env):{RESET}")
print(f"  FACTURACION_NUMERO_INICIAL = {os.getenv('FACTURACION_NUMERO_INICIAL', 'NO DEFINIDO')}")
print(f"  FACTURACION_NUMERO_FINAL = {os.getenv('FACTURACION_NUMERO_FINAL', 'NO DEFINIDO')}")
print(f"  FACTURACION_ESTABLECIMIENTO = {os.getenv('FACTURACION_ESTABLECIMIENTO', 'NO DEFINIDO')}")
print(f"  FACTURACION_PUNTO_EXPEDICION = {os.getenv('FACTURACION_PUNTO_EXPEDICION', 'NO DEFINIDO')}")
print(f"  SQL_PROXY_BASE_URL = {os.getenv('SQL_PROXY_BASE_URL', 'NO DEFINIDO')}")
print()

# Configuración cargada
print(f"{BOLD}⚙️  Configuración Cargada (FACTURACION_CONFIG):{RESET}")
print(f"  Número Inicial: {GREEN}{FACTURACION_CONFIG['numero_inicial']}{RESET}")
print(f"  Número Final: {GREEN}{FACTURACION_CONFIG['numero_final']}{RESET}")
print(f"  Número Actual: {YELLOW}{FACTURACION_CONFIG['numero_actual']}{RESET}")
print(f"  Formato: {FACTURACION_CONFIG['formato_numero']}")
print()

# Cálculo de capacidad
capacidad = FACTURACION_CONFIG['numero_final'] - FACTURACION_CONFIG['numero_inicial'] + 1
print(f"{BOLD}📊 Capacidad del Rango:{RESET}")
print(f"  Facturas disponibles: {GREEN}{capacidad}{RESET} ({FACTURACION_CONFIG['numero_inicial']} - {FACTURACION_CONFIG['numero_final']})")
print()

# Timbrado
print(f"{BOLD}🏷️  Timbrado:{RESET}")
print(f"  Establecimiento: {TIMBRADO_CONFIG['establecimiento']}")
print(f"  Punto de Expedición: {TIMBRADO_CONFIG['punto_expedicion']}")
print(f"  Número de Timbrado: {TIMBRADO_CONFIG['numero']}")
print(f"  Fecha Inicio: {TIMBRADO_CONFIG['fecha_inicio']}")
print()

# SQL Proxy
print(f"{BOLD}🔌 SQL Proxy:{RESET}")
print(f"  KUDE URL: {SQL_PROXY_CONFIG['kude_url']}")
print(f"  Host: {SQL_PROXY_CONFIG['host']}:{SQL_PROXY_CONFIG['port']}")
print(f"  Base de Datos: {SQL_PROXY_CONFIG['database']}")
print()

# Formato de ejemplo
numero_ejemplo = FACTURACION_CONFIG['numero_inicial']
formato_completo = f"{TIMBRADO_CONFIG['establecimiento']}-{TIMBRADO_CONFIG['punto_expedicion']}-{numero_ejemplo:07d}"

print(f"{BOLD}📄 Ejemplo de Factura:{RESET}")
print(f"  Formato: {GREEN}{formato_completo}{RESET}")
print(f"  (Establecimiento-PuntoExpedición-Número)")
print()

# Validaciones
print(f"{BOLD}✅ Validaciones:{RESET}")
errores = []

if FACTURACION_CONFIG['numero_inicial'] >= FACTURACION_CONFIG['numero_final']:
    errores.append("❌ El número inicial debe ser menor que el número final")
else:
    print(f"  {GREEN}✓{RESET} Rango válido")

if capacidad < 10:
    print(f"  {YELLOW}⚠{RESET} Advertencia: Capacidad muy baja ({capacidad} facturas)")
elif capacidad < 50:
    print(f"  {GREEN}✓{RESET} Capacidad adecuada para desarrollo ({capacidad} facturas)")
else:
    print(f"  {GREEN}✓{RESET} Capacidad suficiente ({capacidad} facturas)")

if not os.getenv('FACTURACION_NUMERO_INICIAL'):
    errores.append("❌ Variable FACTURACION_NUMERO_INICIAL no está definida en .env")
else:
    print(f"  {GREEN}✓{RESET} Variables de entorno configuradas")

# Resumen final
print()
if errores:
    print(f"{RED}{BOLD}❌ ERRORES ENCONTRADOS:{RESET}")
    for error in errores:
        print(f"  {error}")
    print()
    print(f"{YELLOW}Por favor, revisa tu archivo .env{RESET}")
else:
    print(f"{GREEN}{BOLD}✅ CONFIGURACIÓN CORRECTA{RESET}")
    print(f"{GREEN}El sistema está listo para generar facturas desde el número {FACTURACION_CONFIG['numero_inicial']}{RESET}")

print(f"\n{CYAN}{'='*70}{RESET}\n")
