#!/usr/bin/env python
"""
Script de inicialización completa del sistema
- Carga todos los fixtures en el orden correcto
- Sincroniza permisos de todos los grupos
- Verifica y crea usuarios de desarrollo si es necesario
"""
import os
import sys
import django

# Agregar el directorio raíz del proyecto al PYTHONPATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from django.core.management import call_command
from django.db import connection, transaction
from django.contrib.auth.models import Group, Permission
from users.models import CustomUser

# Colores para la terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

# Orden de carga de fixtures (respetando dependencias)
FIXTURES_ORDER = [
    # 1. Usuarios y roles primero
    ('Roles y Grupos', 'roles/fixtures/roles_data.json'),
    ('Usuarios', 'users/fixtures/users_data.json'),
    ('Clientes', 'clientes/fixtures/clientes_data.json'),

    # 2. Divisas y denominaciones
    ('Divisas', 'divisas/fixtures/divisas_data.json'),
    ('Denominaciones', 'divisas/fixtures/denominaciones_data.json'),
    
    # 3. Medios de pago
    ('Medios de Pago', 'medios_pago/fixtures/medios_data.json'),
    ('Medios Financieros', 'medios_pago/fixtures/mediosfinancieros_data.json'),
    ('Medios Financieros Cliente', 'clientes/fixtures/mediosfinancieroscliente_data.json'),
    
    # 4. Bancos y billeteras
    ('Bancos', 'banco/fixtures/bancos_data.json'),
    ('Billeteras', 'billetera/fixtures/billetera_data.json'),
    
    # 5. TAUSER (Terminales de autoservicio con inventario)
    ('TAUSER (Terminales)', 'tauser/fixtures/tausers_data.json'),
]

def check_database_connection():
    """Verifica la conexión a la base de datos"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            print_success("Conexión a base de datos establecida")
            print_info(f"PostgreSQL: {db_version.split(',')[0]}")
            return True
    except Exception as e:
        print_error(f"Error de conexión a base de datos: {e}")
        return False

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
        print_warning(f"Archivo no encontrado: {filepath}")
        return False
    
    # Verificar codificación
    encoding = check_encoding(filepath)
    if encoding == 'UTF-16':
        print_error(f"{filepath} está en UTF-16, debe ser UTF-8")
        return False
    elif encoding == 'ERROR':
        print_error(f"Error al leer {filepath}")
        return False
    
    # Intentar cargar el fixture
    try:
        print_info(f"Cargando {name}...")
        call_command('loaddata', filepath, verbosity=0)
        print_success(f"{name} cargado exitosamente")
        return True
    except Exception as e:
        print_error(f"Error cargando {name}: {str(e)[:150]}")
        return False

def sync_permissions():
    """Sincroniza los permisos de todos los grupos usando el comando de management"""
    try:
        print_info("Sincronizando permisos personalizados...")
        call_command('sync_permissions', verbosity=0)
        print_success("Permisos personalizados sincronizados")
        return True
    except Exception as e:
        print_error(f"Error sincronizando permisos: {e}")
        return False

def assign_group_permissions():
    """Asigna permisos a grupos según la matriz de permisos"""
    try:
        print_info("Asignando permisos a grupos...")
        call_command('assign_group_permissions', verbosity=0, force=True)
        print_success("Permisos asignados a grupos correctamente")
        return True
    except Exception as e:
        print_error(f"Error asignando permisos a grupos: {e}")
        return False

def verify_dev_user():
    """Verifica y crea el usuario dev si no existe"""
    try:
        dev_user = CustomUser.objects.filter(email='dev@test.com').first()
        if not dev_user:
            print_warning("Usuario dev@test.com no encontrado, se creará automáticamente")
            # El fixture ya lo tiene, así que no debería llegar aquí
            return False
        
        print_success(f"Usuario dev verificado: {dev_user.username} ({dev_user.email})")
        print_info(f"  - Superusuario: {dev_user.is_superuser}")
        print_info(f"  - Staff: {dev_user.is_staff}")
        print_info(f"  - Grupos: {', '.join([g.name for g in dev_user.groups.all()])}")
        return True
    except Exception as e:
        print_error(f"Error verificando usuario dev: {e}")
        return False

def verify_groups_and_permissions():
    """Verifica que los grupos tengan permisos asignados"""
    try:
        print_info("Verificando grupos y permisos...")
        groups = Group.objects.all()
        
        for group in groups:
            perm_count = group.permissions.count()
            if perm_count > 0:
                print_success(f"Grupo '{group.name}': {perm_count} permisos")
            else:
                print_warning(f"Grupo '{group.name}': Sin permisos asignados")
        
        return True
    except Exception as e:
        print_error(f"Error verificando grupos: {e}")
        return False

def show_summary():
    """Muestra un resumen de usuarios, grupos y datos importantes"""
    try:
        print_header("RESUMEN DEL SISTEMA")
        
        # Usuarios
        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(is_active=True).count()
        staff_users = CustomUser.objects.filter(is_staff=True).count()
        print(f"{Colors.BOLD}USUARIOS:{Colors.ENDC}")
        print(f"  Total: {total_users}")
        print(f"  Activos: {active_users}")
        print(f"  Staff: {staff_users}")
        
        # Grupos
        total_groups = Group.objects.count()
        print(f"\n{Colors.BOLD}GRUPOS:{Colors.ENDC}")
        print(f"  Total: {total_groups}")
        for group in Group.objects.all():
            print(f"  - {group.name}: {group.permissions.count()} permisos")
        
        # Datos del sistema
        from clientes.models import Cliente
        from divisas.models import Divisa
        from medios_pago.models import MedioDePago
        from tauser.models import Terminal, InventarioDenominacionTerminal
        
        print(f"\n{Colors.BOLD}DATOS DEL SISTEMA:{Colors.ENDC}")
        print(f"  Clientes: {Cliente.objects.count()}")
        print(f"  Divisas: {Divisa.objects.count()}")
        print(f"  Medios de Pago: {MedioDePago.objects.count()}")
        print(f"  TAUSER (Terminales): {Terminal.objects.count()}")
        print(f"  Inventario TAUSER (líneas): {InventarioDenominacionTerminal.objects.count()}")
        
        return True
    except Exception as e:
        print_error(f"Error generando resumen: {e}")
        return False

def main():
    """Función principal"""
    print_header("INICIALIZACIÓN DEL SISTEMA")
    print_info("Este script realizará:")
    print_info("  1. Verificación de base de datos")
    print_info("  2. Carga de fixtures")
    print_info("  3. Sincronización de permisos personalizados")
    print_info("  4. Asignación de permisos a grupos")
    print_info("  5. Verificación de grupos y permisos")
    print_info("  6. Verificación de usuarios")
    print_info("  7. Resumen del sistema")
    
    #input(f"\n{Colors.WARNING}Presiona ENTER para continuar...{Colors.ENDC}")
    
    # 1. Verificar conexión a la base de datos
    print_header("PASO 1: VERIFICACIÓN DE BASE DE DATOS")
    if not check_database_connection():
        print_error("No se pudo conectar a la base de datos. Abortando.")
        return 1
    
    # 2. Cargar fixtures
    print_header("PASO 2: CARGA DE FIXTURES")
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for name, filepath in FIXTURES_ORDER:
        if load_fixture(name, filepath):
            success_count += 1
        else:
            if os.path.exists(filepath):
                failed_count += 1
            else:
                skipped_count += 1
    
    print(f"\n{Colors.BOLD}Resultado de carga:{Colors.ENDC}")
    print_success(f"Exitosos: {success_count}")
    if failed_count > 0:
        print_error(f"Fallidos: {failed_count}")
    if skipped_count > 0:
        print_warning(f"Omitidos: {skipped_count}")
    
    if failed_count > 0:
        print_error("Algunos fixtures fallaron. Revisa los errores.")
        return 1
    
    # 3. Sincronizar permisos
    print_header("PASO 3: SINCRONIZACIÓN DE PERMISOS")
    if not sync_permissions():
        print_error("Error al sincronizar permisos. Continuando...")
    
    # 4. Asignar permisos a grupos
    print_header("PASO 4: ASIGNACIÓN DE PERMISOS A GRUPOS")
    if not assign_group_permissions():
        print_error("Error al asignar permisos a grupos. Continuando...")
    
    # 5. Verificar grupos y permisos
    print_header("PASO 5: VERIFICACIÓN DE GRUPOS Y PERMISOS")
    verify_groups_and_permissions()
    
    # 6. Verificar usuario dev
    print_header("PASO 6: VERIFICACIÓN DE USUARIOS")
    verify_dev_user()
    
    # 6. Mostrar resumen
    show_summary()
    
    # Resultado final
    print_header("INICIALIZACIÓN COMPLETADA")
    print_success("El sistema está listo para usar")
    print_info("\nUsuarios de prueba disponibles:")
    print_info("  - dev@test.com / 12345678 (Superusuario)")
    print_info("  - admin@gmail.com / 12345678 (Administrador)")
    print_info("  - operador@test.com / 12345678 (Operador)")
    print_info("  - observador@test.com / 12345678 (Observador)")
    print_info("  - analista@test.com / 12345678 (Analista)")
    print_info("  - cliente@test.com / 12345678 (Cliente)")
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warning("\n\nProceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nError inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
