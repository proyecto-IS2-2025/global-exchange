#!/usr/bin/env python
"""
Script para resetear migraciones de Django
Útil cuando tienes conflictos de migraciones
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def find_migration_dirs():
    """Encuentra todos los directorios de migraciones"""
    migration_dirs = []
    for root, dirs, files in os.walk('.'):
        if 'migrations' in dirs:
            migration_path = Path(root) / 'migrations'
            # Excluir venv y otros directorios no relevantes
            if not any(part in migration_path.parts for part in ['.venv', 'venv', 'node_modules', '.git']):
                migration_dirs.append(migration_path)
    return migration_dirs

def reset_migrations():
    """Resetea todas las migraciones"""
    print("🔄 Encontrando directorios de migraciones...")
    migration_dirs = find_migration_dirs()
    
    for migration_dir in migration_dirs:
        print(f"📁 Procesando: {migration_dir}")
        
        # Eliminar todos los archivos .py excepto __init__.py
        for file in migration_dir.glob('*.py'):
            if file.name != '__init__.py':
                print(f"  🗑️ Eliminando: {file.name}")
                file.unlink()
        
        # Eliminar __pycache__ si existe
        pycache_dir = migration_dir / '__pycache__'
        if pycache_dir.exists():
            print(f"  🗑️ Eliminando __pycache__")
            shutil.rmtree(pycache_dir)
    
    print("\n✅ Migraciones eliminadas")
    print("🔄 Creando nuevas migraciones...")
    
    # Crear nuevas migraciones
    try:
        result = subprocess.run([
            'poetry', 'run', 'python', 'manage.py', 'makemigrations'
        ], capture_output=True, text=True, check=True)
        print("✅ Nuevas migraciones creadas")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al crear migraciones: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False
    
    return True

if __name__ == '__main__':
    print("🚀 Iniciando reset de migraciones...")
    if reset_migrations():
        print("\n🎉 Reset completado exitosamente!")
        print("💡 Ahora puedes ejecutar: poetry run python manage.py migrate")
    else:
        print("\n❌ Hubo errores durante el reset")
        sys.exit(1)