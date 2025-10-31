"""
Script de ayuda para cargar el fixture de medios financieros del Cliente General
con todas sus dependencias en el orden correcto.

Uso:
    python scripts/load_medios_cliente_general.py [--verificar-solo]
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

from django.core.management import call_command
from clientes.models import Cliente, ClienteMedioDePago
from medios_pago.models import MedioDePago
from users.models import CustomUser


def verificar_dependencias():
    """Verifica que todas las dependencias necesarias existen."""
    print("\n" + "="*60)
    print("VERIFICACIÓN DE DEPENDENCIAS")
    print("="*60)
    
    dependencias_ok = True
    
    # Verificar Cliente General
    cliente_existe = Cliente.objects.filter(id=1).exists()
    print(f"{'✓' if cliente_existe else '✗'} Cliente 'Cliente General' (ID: 1): {'EXISTE' if cliente_existe else 'NO ENCONTRADO'}")
    if not cliente_existe:
        dependencias_ok = False
        print("  ⚠ Necesitas cargar el fixture de clientes primero")
    
    # Verificar Medios de Pago
    medios_requeridos = [1, 2, 3, 4]
    for medio_id in medios_requeridos:
        medio_existe = MedioDePago.objects.filter(id=medio_id).exists()
        medio_nombre = MedioDePago.objects.get(id=medio_id).nombre if medio_existe else "N/A"
        print(f"{'✓' if medio_existe else '✗'} Medio de Pago ID {medio_id}: {medio_nombre if medio_existe else 'NO ENCONTRADO'}")
        if not medio_existe:
            dependencias_ok = False
            print("  ⚠ Necesitas cargar el fixture 'mediosfinancieros_data' primero")
    
    # Verificar Usuarios creadores
    usuarios_requeridos = [4, 11]
    for user_id in usuarios_requeridos:
        usuario_existe = CustomUser.objects.filter(id=user_id).exists()
        if usuario_existe:
            user = CustomUser.objects.get(id=user_id)
            print(f"✓ Usuario ID {user_id}: {user.username}")
        else:
            print(f"⚠ Usuario ID {user_id}: NO ENCONTRADO (no crítico, se puede ajustar)")
    
    print("="*60)
    
    if not dependencias_ok:
        print("\n❌ FALTAN DEPENDENCIAS CRÍTICAS")
        print("\nPara cargar las dependencias, ejecuta en orden:")
        print("  1. python manage.py loaddata clientes_base  # Si no tienes el Cliente General")
        print("  2. python manage.py loaddata mediosfinancieros_data")
        print("  3. python scripts/load_medios_cliente_general.py")
        return False
    else:
        print("\n✅ Todas las dependencias críticas están disponibles")
        return True


def mostrar_estado_actual():
    """Muestra el estado actual de los medios del Cliente General."""
    print("\n" + "="*60)
    print("ESTADO ACTUAL")
    print("="*60)
    
    try:
        cliente = Cliente.objects.get(id=1)
        print(f"Cliente: {cliente.nombre_completo}")
        
        medios = ClienteMedioDePago.objects.filter(cliente=cliente)
        print(f"Total de medios de pago configurados: {medios.count()}")
        
        if medios.exists():
            print("\nMedios existentes:")
            for medio in medios:
                principal = "⭐ PRINCIPAL" if medio.es_principal else ""
                activo = "✓" if medio.es_activo else "✗"
                print(f"  {activo} ID {medio.id}: {medio.medio_de_pago.nombre} {principal}")
        else:
            print("  No hay medios configurados")
            
    except Cliente.DoesNotExist:
        print("❌ Cliente 'Cliente General' no encontrado")
    
    print("="*60)


def cargar_fixture():
    """Carga el fixture de medios financieros del cliente."""
    print("\n" + "="*60)
    print("CARGANDO FIXTURE")
    print("="*60)
    
    try:
        print("\n📦 Cargando 'mediosfinancieroscliente_data.json'...")
        call_command('loaddata', 'mediosfinancieroscliente_data', verbosity=2)
        print("\n✅ Fixture cargado exitosamente")
        return True
    except Exception as e:
        print(f"\n❌ Error al cargar el fixture: {e}")
        return False


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Carga el fixture de medios del Cliente General')
    parser.add_argument('--verificar-solo', action='store_true', 
                       help='Solo verifica dependencias sin cargar el fixture')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("FIXTURE: Medios Financieros del Cliente General")
    print("="*60)
    
    # Verificar dependencias
    if not verificar_dependencias():
        return 1
    
    # Mostrar estado actual
    mostrar_estado_actual()
    
    # Si solo es verificación, terminar aquí
    if args.verificar_solo:
        print("\n✓ Verificación completada. Usa el script sin argumentos para cargar el fixture.")
        return 0
    
    # Confirmar carga
    print("\n" + "⚠"*30)
    print("ADVERTENCIA: La carga del fixture sobrescribirá los medios existentes")
    print("con los IDs: 1, 2, 3, 4, 5 del Cliente General")
    print("⚠"*30)
    
    respuesta = input("\n¿Deseas continuar? (s/n): ").strip().lower()
    if respuesta != 's':
        print("\n❌ Operación cancelada")
        return 0
    
    # Cargar fixture
    if cargar_fixture():
        # Mostrar nuevo estado
        print("\n" + "="*60)
        print("VERIFICANDO RESULTADO")
        print("="*60)
        mostrar_estado_actual()
        print("\n✅ Proceso completado exitosamente")
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
