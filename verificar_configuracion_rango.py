#!/usr/bin/env python3
"""
Script para verificar la configuración de tu rango de facturas.
Ejecutar después de configurar las variables de entorno.

USO:
    poetry run python verificar_configuracion_rango.py
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from facturacion_electronica.utils import (
    obtener_configuracion_facturacion,
    obtener_estadisticas_rango,
    obtener_proximo_numero_factura
)
from facturacion_electronica.models import FacturaElectronica


def main():
    print("\n" + "="*80)
    print("🔧 VERIFICACIÓN DE CONFIGURACIÓN DE RANGO DE FACTURAS")
    print("="*80)
    
    # 1. Verificar variables de entorno
    print("\n📋 PASO 1: Verificando variables de entorno...")
    
    env_inicial = os.getenv('FACTURACION_NUMERO_INICIAL')
    env_final = os.getenv('FACTURACION_NUMERO_FINAL')
    env_establecimiento = os.getenv('FACTURACION_ESTABLECIMIENTO')
    env_punto = os.getenv('FACTURACION_PUNTO_EXPEDICION')
    
    if env_inicial:
        print(f"   ✅ FACTURACION_NUMERO_INICIAL = {env_inicial}")
    else:
        print(f"   ⚠️  FACTURACION_NUMERO_INICIAL no configurada (usando default: 51)")
    
    if env_final:
        print(f"   ✅ FACTURACION_NUMERO_FINAL = {env_final}")
    else:
        print(f"   ⚠️  FACTURACION_NUMERO_FINAL no configurada (usando default: 100)")
    
    if env_establecimiento:
        print(f"   ✅ FACTURACION_ESTABLECIMIENTO = {env_establecimiento}")
    else:
        print(f"   ℹ️  FACTURACION_ESTABLECIMIENTO no configurada (usando default: 001)")
    
    if env_punto:
        print(f"   ✅ FACTURACION_PUNTO_EXPEDICION = {env_punto}")
    else:
        print(f"   ℹ️  FACTURACION_PUNTO_EXPEDICION no configurada (usando default: 003)")
    
    # 2. Obtener configuración
    print("\n📊 PASO 2: Configuración cargada...")
    
    config = obtener_configuracion_facturacion()
    print(f"   Rango asignado: {config['numero_inicial']} - {config['numero_final']}")
    print(f"   Establecimiento: {config['establecimiento']}")
    print(f"   Punto Expedición: {config['punto_expedicion']}")
    print(f"   Total de números disponibles: {config['numero_final'] - config['numero_inicial'] + 1}")
    
    # 3. Obtener estadísticas
    print("\n📈 PASO 3: Estadísticas de uso...")
    
    try:
        stats = obtener_estadisticas_rango()
        print(f"   Facturas generadas en tu rango: {stats['usadas']}")
        print(f"   Números disponibles: {stats['disponibles']}")
        print(f"   Porcentaje usado: {stats['porcentaje_usado']}%")
        
        if stats['disponibles'] < 10 and stats['disponibles'] > 0:
            print(f"\n   ⚠️  ADVERTENCIA: Te quedan menos de 10 facturas disponibles!")
        elif stats['disponibles'] == 0:
            print(f"\n   ❌ RANGO COMPLETO: No hay más números disponibles.")
    except Exception as e:
        print(f"   ❌ Error al obtener estadísticas: {e}")
    
    # 4. Obtener próximo número
    print("\n🔢 PASO 4: Próximo número de factura...")
    
    try:
        proximo = obtener_proximo_numero_factura()
        print(f"   ✅ Próximo número a usar: {proximo}")
        
        # Extraer número
        if '-' in proximo:
            numero = int(proximo.split('-')[2])
        else:
            numero = int(proximo)
        
        # Verificar que esté en el rango
        if config['numero_inicial'] <= numero <= config['numero_final']:
            print(f"   ✅ El número {numero} está dentro de tu rango")
        else:
            print(f"   ⚠️  El número {numero} está FUERA de tu rango configurado")
            print(f"      Verifica tu archivo .env")
    except ValueError as e:
        print(f"   ❌ Error: {e}")
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
    
    # 5. Verificar última factura en la BD
    print("\n💾 PASO 5: Última factura en la base de datos...")
    
    try:
        ultima = FacturaElectronica.objects.order_by('-fecha_emision').first()
        if ultima:
            print(f"   Número: {ultima.numero_factura}")
            print(f"   Estado: {ultima.estado_sifen}")
            print(f"   Fecha: {ultima.fecha_emision}")
            print(f"   CDC: {ultima.cdc or 'N/A'}")
        else:
            print(f"   ℹ️  No hay facturas en la base de datos aún")
    except Exception as e:
        print(f"   ❌ Error al consultar la BD: {e}")
    
    # 6. Recomendaciones
    print("\n" + "="*80)
    print("💡 RECOMENDACIONES")
    print("="*80)
    
    if not env_inicial or not env_final:
        print("\n⚠️  NO HAS CONFIGURADO TU RANGO")
        print("\n   1. Ejecuta: poetry run python obtener_proximo_numero.py")
        print("   2. Coordina tu rango con el equipo")
        print("   3. Edita tu archivo .env y agrega:")
        print("      FACTURACION_NUMERO_INICIAL=tu_numero_inicial")
        print("      FACTURACION_NUMERO_FINAL=tu_numero_final")
        print("   4. Reinicia el servidor Django")
        print("   5. Ejecuta este script nuevamente")
    else:
        print("\n✅ Configuración correcta!")
        print(f"   Puedes generar facturas del {config['numero_inicial']} al {config['numero_final']}")
        print(f"   Tienes {stats['disponibles'] if 'stats' in locals() else 'N/A'} números disponibles")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {e}")
        print("\nAsegúrate de:")
        print("  1. Estar en el directorio del proyecto")
        print("  2. Tener poetry instalado")
        print("  3. Tener las variables de entorno configuradas")
        print("  4. Tener acceso a la base de datos")
        sys.exit(1)
