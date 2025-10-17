"""
Script simple para corregir el medio de pago "Tarjeta de Crédito/Débito Local"
que está incorrectamente configurado como tipo 'stripe'.

INSTRUCCIONES:
1. Activar entorno virtual
2. Ejecutar: python scripts/fix_tarjeta_local.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from medios_pago.models import MedioDePago

def fix_tarjeta_local():
    print("\n" + "="*70)
    print("🔧 CORRECCIÓN DE MEDIO DE PAGO: Tarjeta Local")
    print("="*70 + "\n")
    
    try:
        # Buscar el medio de pago por ID
        medio = MedioDePago.objects.get(id=4)
        
        print(f"📋 Medio encontrado:")
        print(f"   ID: {medio.id}")
        print(f"   Nombre: {medio.nombre}")
        print(f"   Tipo ACTUAL: '{medio.tipo_medio}'")
        print(f"   Estado: {medio.estado}\n")
        
        # Verificar si tiene el problema
        if medio.tipo_medio == 'stripe' and 'local' in medio.nombre.lower():
            print("🚨 PROBLEMA DETECTADO:")
            print(f"   → Medio 'Local' tiene tipo 'stripe'")
            print(f"   → Esto causa que se procese con Stripe\n")
            
            # Corregir
            print("🔧 Aplicando corrección...")
            medio.tipo_medio = 'tarjeta'
            medio.save()
            
            print(f"✅ CORREGIDO:")
            print(f"   Tipo NUEVO: '{medio.tipo_medio}'")
            print(f"\n✨ El medio ahora se procesará con el sistema LOCAL de tarjetas\n")
            
        elif medio.tipo_medio != 'stripe':
            print(f"✅ El medio ya está configurado correctamente")
            print(f"   Tipo: '{medio.tipo_medio}'\n")
            
        else:
            print(f"⚠️  El medio tiene tipo 'stripe' pero no parece ser local")
            print(f"   Revisa manualmente si esto es correcto\n")
        
        print("="*70)
        print("✅ Proceso completado")
        print("="*70 + "\n")
        
        print("📝 PRÓXIMOS PASOS:")
        print("1. Reinicia el servidor Django (si está corriendo)")
        print("2. Intenta realizar una compra con tarjeta local")
        print("3. Verifica los logs - debe decir '[PAGO_TARJETA]' NO '[STRIPE]'\n")
        
    except MedioDePago.DoesNotExist:
        print("❌ ERROR: No se encontró el medio de pago con ID=4")
        print("\n📋 Medios de pago disponibles:\n")
        
        for m in MedioDePago.objects.all():
            icono = "🚨" if (m.tipo_medio == 'stripe' and 'local' in m.nombre.lower()) else "✅"
            print(f"{icono} ID {m.id}: {m.nombre} (tipo: '{m.tipo_medio}')")
        
        print("\n💡 Edita el script y cambia el ID en la línea 24\n")
    
    except Exception as e:
        print(f"❌ ERROR: {e}\n")

if __name__ == '__main__':
    fix_tarjeta_local()
