"""
VERSIÓN ULTRA-SEGURA CON MODO DRY-RUN
Primero muestra QUÉ haría, sin hacer cambios reales.
"""
import os
from pathlib import Path
import shutil
from datetime import datetime

# Configuración
OLD_IMPORT = 'from clientes.decorators import require_permission'
NEW_IMPORT = 'from roles.decorators import require_permission'

EXCLUDE_DIRS = {
    '__pycache__', '.git', 'migrations', 'venv', 'env',
    'staticfiles', 'media', '.venv', 'node_modules',
}

def create_backup():
    """Crea un backup de todos los archivos Python antes de modificar."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f'backup_decorators_{timestamp}'
    
    print(f"📦 Creando backup en: {backup_dir}/")
    os.makedirs(backup_dir, exist_ok=True)
    
    count = 0
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file.endswith('.py'):
                src = os.path.join(root, file)
                
                # Recrear estructura de carpetas en backup
                rel_path = os.path.relpath(src, '.')
                dst = os.path.join(backup_dir, rel_path)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                
                shutil.copy2(src, dst)
                count += 1
    
    print(f"   ✓ {count} archivos respaldados")
    return backup_dir

def find_files_with_import():
    """Encuentra archivos con el import antiguo."""
    files_found = []
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if OLD_IMPORT in content:
                        # Contar ocurrencias
                        occurrences = content.count(OLD_IMPORT)
                        files_found.append((filepath, occurrences))
                
                except Exception as e:
                    print(f"⚠️  Error leyendo {filepath}: {e}")
    
    return files_found

def show_diff_preview(filepath):
    """Muestra un preview de los cambios que se harían."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"\n   📄 {filepath}:")
        for i, line in enumerate(lines, 1):
            if OLD_IMPORT in line:
                print(f"      Línea {i}:")
                print(f"      ❌ {line.rstrip()}")
                print(f"      ✅ {line.replace(OLD_IMPORT, NEW_IMPORT).rstrip()}")
    
    except Exception as e:
        print(f"      ⚠️  Error: {e}")

def dry_run(files_to_update):
    """Muestra QUÉ se cambiaría SIN hacer cambios reales."""
    print("\n" + "=" * 80)
    print("🔍 MODO DRY-RUN: Vista previa de cambios (SIN MODIFICAR archivos)")
    print("=" * 80)
    
    for filepath, occurrences in files_to_update:
        show_diff_preview(filepath)
    
    print("\n" + "=" * 80)
    print(f"📊 Total: {len(files_to_update)} archivos serían modificados")
    print("=" * 80)

def apply_changes(files_to_update, backup_dir):
    """Aplica los cambios REALES."""
    print("\n🔄 Aplicando cambios...")
    
    success = 0
    failed = 0
    
    for filepath, occurrences in files_to_update:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content.replace(OLD_IMPORT, NEW_IMPORT)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            success += 1
            print(f"   ✅ {filepath}")
        
        except Exception as e:
            failed += 1
            print(f"   ❌ {filepath}: {e}")
    
    print(f"\n✅ Actualizados: {success}")
    if failed > 0:
        print(f"❌ Errores: {failed}")
    
    print(f"\n💾 Backup guardado en: {backup_dir}/")
    print("   Para restaurar: cp -r {backup_dir}/* .")

def main():
    print("=" * 80)
    print("🛡️  MIGRACIÓN SEGURA DE DECORATORS (CON DRY-RUN Y BACKUP)")
    print("=" * 80)
    print()
    
    # Paso 1: Buscar archivos
    print("🔍 Buscando archivos con imports antiguos...")
    files_to_update = find_files_with_import()
    print(f"   ✓ Encontrados: {len(files_to_update)} archivo(s)")
    
    if not files_to_update:
        print("\n✅ No hay archivos que actualizar. ¡Todo listo!")
        return
    
    # Paso 2: DRY-RUN (vista previa)
    dry_run(files_to_update)
    
    print("\n" + "=" * 80)
    print("⚠️  OPCIONES:")
    print("=" * 80)
    print("   [1] Ver detalles de un archivo específico")
    print("   [2] Continuar y aplicar cambios (con backup automático)")
    print("   [3] Cancelar")
    print()
    
    choice = input("Selecciona una opción (1/2/3): ").strip()
    
    if choice == '1':
        print("\nArchivos disponibles:")
        for i, (filepath, _) in enumerate(files_to_update, 1):
            print(f"   [{i}] {filepath}")
        
        file_num = int(input("\nNúmero de archivo: ").strip())
        if 1 <= file_num <= len(files_to_update):
            filepath = files_to_update[file_num - 1][0]
            show_diff_preview(filepath)
        
        # Volver a preguntar
        if input("\n¿Aplicar cambios ahora? (s/n): ").strip().lower() != 's':
            print("❌ Operación cancelada.")
            return
    
    elif choice == '2':
        pass  # Continuar con el backup y cambios
    
    else:
        print("❌ Operación cancelada.")
        return
    
    # Paso 3: Crear backup
    print("\n" + "=" * 80)
    print("💾 CREANDO BACKUP DE SEGURIDAD")
    print("=" * 80)
    backup_dir = create_backup()
    
    # Paso 4: Aplicar cambios
    print("\n" + "=" * 80)
    print("✏️  APLICANDO CAMBIOS")
    print("=" * 80)
    apply_changes(files_to_update, backup_dir)
    
    # Paso 5: Verificación
    print("\n" + "=" * 80)
    print("🧪 SIGUIENTE PASO: VERIFICAR")
    print("=" * 80)
    print("\n1️⃣  Verificar sintaxis:")
    print("   poetry run python manage.py check")
    print("\n2️⃣  Si hay errores, restaurar backup:")
    print(f"   cp -r {backup_dir}/* .")
    print("\n3️⃣  Si todo OK, eliminar backup:")
    print(f"   rm -rf {backup_dir}/")
    print()

if __name__ == '__main__':
    main()