import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

# Orden de carga de fixtures (respetando dependencias)
FIXTURES_ORDER = [
    # 1. Usuarios y roles primero
    ('users', 'users/fixtures/users_data.json'),
    ('roles', 'roles/fixtures/roles_data.json'),
    
    # 2. Divisas y denominaciones
    ('divisas', 'divisas/fixtures/divisas_data.json'),
    ('denominaciones', 'divisas/fixtures/denominaciones_data.json'),
    
    # 3. Medios de pago
    ('medios de pago', 'medios_pago/fixtures/medios_data.json'),
    ('medios financieros', 'medios_pago/fixtures/mediosfinancieros_data.json'),
    
    # 4. Clientes
    ('clientes', 'clientes/fixtures/clientes_data.json'),
    ('medios financieros cliente', 'clientes/fixtures/mediosfinancieroscliente_data.json'),
    
    # 5. Bancos y billeteras
    ('bancos', 'banco/fixtures/bancos_data.json'),
    ('billeteras', 'billetera/fixtures/billetera_data.json'),
]

def check_encoding(filepath):
    """Verifica si el archivo tiene codificación UTF-16"""
    try:
        with open(filepath, 'rb') as f:
            first_bytes = f.read(2)
            if first_bytes == b'\xff\xfe':
                return 'UTF-16'
            return 'UTF-8'
    except:
        return 'ERROR'

def load_fixture(name, filepath):
    """Carga un fixture y reporta el resultado"""
    # Verificar que el archivo existe
    if not os.path.exists(filepath):
        print(f"  ⚠️  Archivo no encontrado: {filepath}")
        return False
    
    # Verificar codificación
    encoding = check_encoding(filepath)
    if encoding == 'UTF-16':
        print(f"  ⚠️  ADVERTENCIA: {filepath} está en UTF-16, debería ser UTF-8")
        return False
    elif encoding == 'ERROR':
        print(f"  ❌ Error al leer {filepath}")
        return False
    
    # Intentar cargar el fixture
    try:
        print(f"  📦 Cargando {name}...")
        call_command('loaddata', filepath, verbosity=0)
        print(f"  ✅ {name} cargado exitosamente")
        return True
    except Exception as e:
        print(f"  ❌ Error cargando {name}: {str(e)[:200]}")
        return False

def main():
    print("="*70)
    print("CARGA DE FIXTURES - DIAGNÓSTICO")
    print("="*70)
    
    # Verificar conexión a la base de datos
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            print(f"\n✅ Conexión a base de datos OK")
            print(f"   PostgreSQL: {db_version.split(',')[0]}\n")
    except Exception as e:
        print(f"\n❌ Error de conexión a base de datos: {e}\n")
        return
    
    # Cargar fixtures
    print("Cargando fixtures en orden de dependencias:\n")
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for name, filepath in FIXTURES_ORDER:
        print(f"\n[{name.upper()}]")
        if load_fixture(name, filepath):
            success_count += 1
        else:
            if os.path.exists(filepath):
                failed_count += 1
            else:
                skipped_count += 1
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"✅ Exitosos: {success_count}")
    print(f"❌ Fallidos: {failed_count}")
    print(f"⚠️  Omitidos (no encontrados): {skipped_count}")
    print(f"📊 Total: {len(FIXTURES_ORDER)}")
    
    if failed_count > 0:
        print("\n⚠️  Algunos fixtures fallaron. Revisa los errores arriba.")
        return 1
    else:
        print("\n✅ Todos los fixtures disponibles fueron cargados exitosamente")
        return 0

if __name__ == '__main__':
    sys.exit(main())
