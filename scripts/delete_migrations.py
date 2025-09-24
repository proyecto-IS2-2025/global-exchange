#!/usr/bin/env python3
"""
Script para eliminar todas las migraciones de un proyecto Django
Autor: Asistente
Descripción: Elimina todos los archivos de migración excepto __init__.py
"""

import os
import shutil
from pathlib import Path

def find_django_apps(project_root="."):
    """
    Encuentra todas las apps de Django en el proyecto
    """
    apps = []
    
    for item in os.listdir(project_root):
        item_path = os.path.join(project_root, item)
        
        # Verificar si es un directorio y contiene migrations
        if os.path.isdir(item_path):
            migrations_path = os.path.join(item_path, "migrations")
            if os.path.exists(migrations_path):
                apps.append(item)
    
    return apps

def delete_migration_files(app_name):
    """
    Elimina todos los archivos de migración de una app específica
    """
    migrations_path = os.path.join(app_name, "migrations")
    
    if not os.path.exists(migrations_path):
        print(f"❌ No se encontró el directorio migrations en {app_name}")
        return False
    
    deleted_files = []
    
    # Recorrer todos los archivos en el directorio migrations
    for filename in os.listdir(migrations_path):
        file_path = os.path.join(migrations_path, filename)
        
        # Eliminar archivos .py que no sean __init__.py
        if filename.endswith('.py') and filename != '__init__.py':
            try:
                os.remove(file_path)
                deleted_files.append(filename)
                print(f"  ✅ Eliminado: {filename}")
            except OSError as e:
                print(f"  ❌ Error al eliminar {filename}: {e}")
        
        # Eliminar archivos .pyc
        elif filename.endswith('.pyc'):
            try:
                os.remove(file_path)
                deleted_files.append(filename)
                print(f"  ✅ Eliminado: {filename}")
            except OSError as e:
                print(f"  ❌ Error al eliminar {filename}: {e}")
    
    # Eliminar directorio __pycache__ si existe
    pycache_path = os.path.join(migrations_path, "__pycache__")
    if os.path.exists(pycache_path):
        try:
            shutil.rmtree(pycache_path)
            print(f"  ✅ Eliminado directorio: __pycache__")
        except OSError as e:
            print(f"  ❌ Error al eliminar __pycache__: {e}")
    
    return len(deleted_files) > 0

def main():
    """
    Función principal del script
    """
    print("🚀 Iniciando eliminación de migraciones de Django...")
    print("=" * 50)
    
    # Verificar si estamos en un proyecto Django
    if not os.path.exists("manage.py"):
        print("❌ Error: No se encontró manage.py")
        print("   Asegúrate de ejecutar este script desde el directorio raíz de tu proyecto Django")
        return
    
    # Encontrar todas las apps
    apps = find_django_apps()
    
    if not apps:
        print("❌ No se encontraron apps con migraciones en el proyecto")
        return
    
    print(f"📱 Apps encontradas: {', '.join(apps)}")
    print()
    
    # Confirmar antes de proceder
    respuesta = input("¿Estás seguro de que quieres eliminar TODAS las migraciones? (s/N): ")
    if respuesta.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Operación cancelada")
        return
    
    print()
    total_apps_procesadas = 0
    
    # Procesar cada app
    for app in apps:
        print(f"🔄 Procesando app: {app}")
        if delete_migration_files(app):
            total_apps_procesadas += 1
        print()
    
    print("=" * 50)
    print(f"✅ Proceso completado!")
    print(f"📊 Apps procesadas: {total_apps_procesadas}/{len(apps)}")
    
    if total_apps_procesadas > 0:
        print()
        print("⚠️  RECORDATORIOS IMPORTANTES:")
        print("   1. Ejecuta 'python manage.py makemigrations' para crear nuevas migraciones")
        print("   2. Ejecuta 'python manage.py migrate' para aplicar las migraciones")
        print("   3. Si tienes datos importantes, asegúrate de tener un backup de tu base de datos")

if __name__ == "__main__":
    main()