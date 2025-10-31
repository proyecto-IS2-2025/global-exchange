#!/usr/bin/env python3
"""
Script simple para consultar el último número de factura.
Ejecutar desde la raíz del proyecto Django.

USO:
    poetry run python obtener_proximo_numero.py
    # O si estás en el venv activado:
    python obtener_proximo_numero.py
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from facturacion_electronica.models import FacturaElectronica
from django.db.models import Max


def main():
    print("\n" + "="*80)
    print("🔍 CONSULTANDO ÚLTIMO NÚMERO DE FACTURA")
    print("="*80)
    
    # Obtener el último número de factura
    ultimo_numero = FacturaElectronica.objects.aggregate(
        Max('numero_factura')
    )['numero_factura__max']
    
    if ultimo_numero:
        # Convertir a entero y sumar 1
        try:
            # El formato puede ser "001-003-0000082" o "0000082"
            # Extraer solo la parte numérica final
            if '-' in ultimo_numero:
                # Formato: "001-003-0000082"
                partes = ultimo_numero.split('-')
                establecimiento = partes[0]
                punto_exp = partes[1]
                numero = partes[2]
                numero_int = int(numero)
            else:
                # Formato: "0000082"
                establecimiento = "001"
                punto_exp = "003"
                numero_int = int(ultimo_numero)
            
            proximo_numero = numero_int + 1
            
            # Obtener información de la última factura
            ultima_factura = FacturaElectronica.objects.filter(
                numero_factura=ultimo_numero
            ).first()
            
            print(f"\n📋 ÚLTIMA FACTURA REGISTRADA:")
            print(f"   Número completo: {ultimo_numero}")
            if '-' in ultimo_numero:
                print(f"   Establecimiento: {establecimiento}")
                print(f"   Punto Expedición: {punto_exp}")
                print(f"   Número: {numero}")
            print(f"   Estado: {ultima_factura.estado_sifen}")
            print(f"   Fecha: {ultima_factura.fecha_emision}")
            print(f"   CDC: {ultima_factura.cdc or 'N/A'}")
            
            # Formato del próximo número
            if '-' in ultimo_numero:
                proximo_formateado = f"{establecimiento}-{punto_exp}-{str(proximo_numero).zfill(7)}"
            else:
                proximo_formateado = str(proximo_numero).zfill(7)
            
            print(f"\n✅ PRÓXIMO NÚMERO DISPONIBLE:")
            print(f"   Formato completo: {proximo_formateado}")
            print(f"   Solo número: {str(proximo_numero).zfill(7)}")
            
            # Contar facturas por estado
            print(f"\n📊 ESTADÍSTICAS:")
            estados = FacturaElectronica.objects.values('estado_sifen').annotate(
                total=Count('id')
            ).order_by('-total')
            
            for estado in estados:
                icono = {
                    'Aprobado': '✅',
                    'Aprobado con observación': '⚠️',
                    'Rechazado': '❌',
                    'ENVIADO_A_SIFEN': '📤',
                    'SOL.APROBACION': '⏳',
                    'Cancelado': '🚫',
                    'Inutilizado': '❌'
                }.get(estado['estado_sifen'], '❓')
                
                print(f"   {icono} {estado['estado_sifen']}: {estado['total']}")
            
            # Sugerencia para el equipo
            print(f"\n💡 RECOMENDACIÓN PARA EL EQUIPO:")
            print(f"   Coordinen quién usa qué rango de números:")
            print(f"   - Desarrollador 1: {proximo_numero:07d} - {proximo_numero+49:07d}")
            print(f"   - Desarrollador 2: {proximo_numero+50:07d} - {proximo_numero+99:07d}")
            print(f"   - Desarrollador 3: {proximo_numero+100:07d} - {proximo_numero+149:07d}")
            
        except ValueError:
            print(f"\n⚠️  El número de factura '{ultimo_numero}' no es válido")
            
    else:
        print("\n⚠️  No se encontraron facturas en la base de datos")
        print("   Puedes comenzar desde el número: 0000001")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        from django.db.models import Count
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nAsegúrate de:")
        print("  1. Estar en el directorio del proyecto Django")
        print("  2. Tener las variables de entorno configuradas")
        print("  3. Tener acceso a la base de datos")
        sys.exit(1)
