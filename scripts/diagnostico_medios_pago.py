"""
Script de diagnóstico para identificar problemas de configuración en medios de pago.
Especialmente útil para detectar tarjetas locales configuradas como Stripe.

Uso:
    python manage.py shell < scripts/diagnostico_medios_pago.py
"""

from medios_pago.models import MedioDePago
from clientes.models import ClienteMedioDePago

def print_separator(char="=", length=70):
    print(char * length)

def diagnosticar_medios_pago():
    """Diagnostica la configuración de medios de pago"""
    
    print("\n")
    print_separator()
    print("🔍 DIAGNÓSTICO DE MEDIOS DE PAGO")
    print_separator()
    
    medios = MedioDePago.objects.all()
    
    if not medios.exists():
        print("\n❌ No hay medios de pago configurados")
        return
    
    print(f"\n📊 Total de medios configurados: {medios.count()}\n")
    
    problemas_encontrados = []
    
    for medio in medios:
        print_separator("-")
        print(f"\n🏷️  ID: {medio.id}")
        print(f"📝 Nombre: {medio.nombre}")
        print(f"🔖 Tipo: '{medio.tipo_medio}'")
        print(f"📊 Estado: {medio.estado}")
        
        # Detectar problemas
        nombre_lower = medio.nombre.lower()
        tipo_lower = medio.tipo_medio.lower()
        
        # Problema 1: Medio "local" con tipo "stripe"
        if 'local' in nombre_lower and tipo_lower == 'stripe':
            problema = {
                'id': medio.id,
                'nombre': medio.nombre,
                'tipo_actual': medio.tipo_medio,
                'descripcion': 'Medio LOCAL configurado como Stripe',
                'solucion': "Cambiar tipo_medio a 'tarjeta' o 'tarjeta_local'"
            }
            problemas_encontrados.append(problema)
            print(f"\n🚨 PROBLEMA DETECTADO:")
            print(f"   → Medio con 'Local' en el nombre tiene tipo='stripe'")
            print(f"   → Esto causará que se procese con Stripe en lugar del sistema local")
            print(f"   ✅ Solución: Cambiar tipo a 'tarjeta'")
        
        # Problema 2: Medio "stripe" sin tipo stripe
        elif 'stripe' in nombre_lower and tipo_lower != 'stripe':
            problema = {
                'id': medio.id,
                'nombre': medio.nombre,
                'tipo_actual': medio.tipo_medio,
                'descripcion': 'Medio Stripe sin tipo stripe',
                'solucion': "Cambiar tipo_medio a 'stripe'"
            }
            problemas_encontrados.append(problema)
            print(f"\n⚠️  ADVERTENCIA:")
            print(f"   → Medio con 'Stripe' en el nombre NO tiene tipo='stripe'")
            print(f"   → Esto causará que NO se procese con Stripe")
            print(f"   ✅ Solución: Cambiar tipo a 'stripe'")
        
        # Problema 3: Medio billetera sin tipo billetera
        elif 'billetera' in nombre_lower and 'billetera' not in tipo_lower:
            problema = {
                'id': medio.id,
                'nombre': medio.nombre,
                'tipo_actual': medio.tipo_medio,
                'descripcion': 'Medio Billetera sin tipo billetera',
                'solucion': "Cambiar tipo_medio a 'billetera' o 'billetera_electronica'"
            }
            problemas_encontrados.append(problema)
            print(f"\n⚠️  ADVERTENCIA:")
            print(f"   → Medio con 'Billetera' en el nombre no tiene tipo apropiado")
            print(f"   ✅ Solución: Cambiar tipo a 'billetera' o 'billetera_electronica'")
        
        else:
            print(f"\n✅ Configuración parece correcta")
        
        # Mostrar clientes asignados
        clientes_count = ClienteMedioDePago.objects.filter(medio=medio).count()
        print(f"\n👥 Clientes con este medio: {clientes_count}")
    
    # Resumen de problemas
    print("\n")
    print_separator()
    print("📋 RESUMEN DE DIAGNÓSTICO")
    print_separator()
    
    if problemas_encontrados:
        print(f"\n❌ Se encontraron {len(problemas_encontrados)} problema(s):\n")
        
        for i, problema in enumerate(problemas_encontrados, 1):
            print(f"{i}. Medio ID {problema['id']}: {problema['nombre']}")
            print(f"   Problema: {problema['descripcion']}")
            print(f"   Tipo actual: '{problema['tipo_actual']}'")
            print(f"   Solución: {problema['solucion']}")
            print()
        
        print("\n🔧 COMANDOS PARA CORREGIR:\n")
        print("python manage.py shell\n")
        print("from medios_pago.models import MedioDePago\n")
        
        for problema in problemas_encontrados:
            tipo_sugerido = 'stripe' if 'Stripe' in problema['solucion'] else \
                           'billetera' if 'Billetera' in problema['solucion'] else 'tarjeta'
            
            print(f"# Corregir: {problema['nombre']}")
            print(f"medio = MedioDePago.objects.get(id={problema['id']})")
            print(f"medio.tipo_medio = '{tipo_sugerido}'")
            print(f"medio.save()")
            print(f"print('✅ Medio {problema['id']} actualizado')\n")
    
    else:
        print("\n✅ ¡No se encontraron problemas de configuración!")
        print("   Todos los medios de pago están configurados correctamente.\n")
    
    print_separator()
    
    return len(problemas_encontrados) == 0

def mostrar_tipos_esperados():
    """Muestra los tipos esperados para cada medio"""
    print("\n")
    print_separator()
    print("📚 TIPOS ESPERADOS POR MEDIO DE PAGO")
    print_separator()
    print("""
    ┌─────────────────────────────────┬────────────────────────────────┐
    │ Medio de Pago                   │ tipo_medio Esperado            │
    ├─────────────────────────────────┼────────────────────────────────┤
    │ Tarjeta Local (Débito/Crédito)  │ tarjeta, tarjeta_local         │
    │ Tarjeta Stripe                  │ stripe                         │
    │ Billetera Digital               │ billetera, billetera_electronica│
    │ Cuenta Bancaria / Transferencia │ transferencia, banco, cuenta   │
    └─────────────────────────────────┴────────────────────────────────┘
    
    ⚠️  IMPORTANTE:
    - Un medio "Local" NUNCA debe tener tipo 'stripe'
    - Un medio "Stripe" SIEMPRE debe tener tipo 'stripe'
    - Los nombres deben ser claros y consistentes con el tipo
    """)
    print_separator())

if __name__ == '__main__':
    todo_ok = diagnosticar_medios_pago()
    mostrar_tipos_esperados()
    
    if not todo_ok:
        print("\n⚠️  Se encontraron problemas. Por favor, corrígelos antes de continuar.\n")
    else:
        print("\n✅ Sistema de medios de pago configurado correctamente.\n")
