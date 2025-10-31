"""
Script para mostrar un resumen del fixture de medios financieros del Cliente General.
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from clientes.models import Cliente, ClienteMedioDePago


def main():
    print("\n" + "="*70)
    print("RESUMEN DEL FIXTURE: mediosfinancieroscliente_data.json")
    print("="*70)
    
    try:
        cliente = Cliente.objects.get(id=1)
        
        print(f"\n📋 Cliente: {cliente.nombre_completo}")
        print(f"🆔 ID: {cliente.id}")
        
        medios = cliente.medios_pago.all()
        print(f"\n💳 Total de Medios de Pago: {medios.count()}")
        print("\n" + "-"*70)
        
        for idx, medio in enumerate(medios, 1):
            activo = "✓" if medio.es_activo else "✗"
            principal = "⭐ PRINCIPAL" if medio.es_principal else ""
            
            print(f"\n{idx}. [{activo}] {medio.medio_de_pago.nombre} {principal}")
            print(f"   🆔 ID del registro: {medio.id}")
            print(f"   🔗 Medio de Pago ID: {medio.medio_de_pago.id}")
            print(f"   📅 Creado: {medio.fecha_creacion.strftime('%Y-%m-%d %H:%M')}")
            
            # Mostrar algunos datos (sin información sensible completa)
            print(f"   📝 Datos configurados:")
            for campo, valor in medio.datos_campos.items():
                # Ocultar información sensible
                if 'tarjeta' in campo.lower() or 'número' in campo.lower():
                    if len(str(valor)) > 10:
                        valor = f"{str(valor)[:4]} **** **** {str(valor)[-4:]}"
                elif 'cvc' in campo.lower() or 'cvv' in campo.lower() or 'seguridad' in campo.lower():
                    valor = "***"
                
                print(f"      • {campo}: {valor}")
        
        print("\n" + "-"*70)
        print("\n✅ El fixture contiene estos datos listos para ser cargados")
        print("📦 Archivo: clientes/fixtures/mediosfinancieroscliente_data.json")
        print("\n💡 Para cargar: python manage.py loaddata mediosfinancieroscliente_data")
        print("💡 O usar: python scripts/load_medios_cliente_general.py")
        print("\n" + "="*70)
        
    except Cliente.DoesNotExist:
        print("\n❌ Error: Cliente 'Cliente General' (ID: 1) no encontrado")
        print("   Asegúrate de que el cliente existe en la base de datos")
        return 1
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
