#!/usr/bin/env python
"""
Script de verificación para configuración de Render
Ejecutar ANTES de hacer deploy
"""
import os
import sys

def check_settings():
    print("🔍 Verificando configuración para Render...\n")
    
    # Leer settings.py
    settings_path = 'casa_de_cambios/settings.py'
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ No se encontró settings.py")
        return False
    
    issues = []
    warnings = []
    success = []
    
    # 1. Verificar DATABASE_URL
    if "os.environ.get('DATABASE_URL')" in content:
        success.append("✅ DATABASE_URL verificación correcta")
    else:
        issues.append("❌ No se encontró verificación correcta de DATABASE_URL")
    
    # 2. Verificar que no haya URL hardcoded
    if 'postgresql://' in content and "if os.environ.get('postgresql://" in content:
        issues.append("❌ CRÍTICO: URL de base de datos hardcoded en if statement")
    else:
        success.append("✅ No hay URLs hardcoded en condiciones")
    
    # 3. Verificar dj_database_url
    if 'import dj_database_url' in content:
        success.append("✅ dj_database_url importado")
    else:
        issues.append("❌ dj_database_url no está importado")
    
    # 4. Verificar WhiteNoise
    if 'whitenoise.middleware.WhiteNoiseMiddleware' in content:
        success.append("✅ WhiteNoise configurado en MIDDLEWARE")
    else:
        warnings.append("⚠️  WhiteNoise no está en MIDDLEWARE")
    
    # 5. Verificar ALLOWED_HOSTS
    if 'ALLOWED_HOSTS' in content and 'os.environ.get' in content:
        success.append("✅ ALLOWED_HOSTS usa variables de entorno")
    else:
        warnings.append("⚠️  ALLOWED_HOSTS podría no estar configurado correctamente")
    
    # 6. Verificar SECRET_KEY
    if "os.environ.get('SECRET_KEY')" in content:
        success.append("✅ SECRET_KEY usa variable de entorno")
    else:
        issues.append("❌ SECRET_KEY no usa variable de entorno")
    
    # 7. Verificar DEBUG
    if "os.environ.get('DEBUG'" in content:
        success.append("✅ DEBUG usa variable de entorno")
    else:
        warnings.append("⚠️  DEBUG podría no estar configurado para producción")
    
    # Mostrar resultados
    print("=" * 60)
    print("✅ CORRECTO:")
    print("=" * 60)
    for item in success:
        print(f"  {item}")
    
    if warnings:
        print("\n" + "=" * 60)
        print("⚠️  ADVERTENCIAS:")
        print("=" * 60)
        for item in warnings:
            print(f"  {item}")
    
    if issues:
        print("\n" + "=" * 60)
        print("❌ PROBLEMAS CRÍTICOS:")
        print("=" * 60)
        for item in issues:
            print(f"  {item}")
    
    # Verificar archivos requeridos
    print("\n" + "=" * 60)
    print("📁 ARCHIVOS REQUERIDOS:")
    print("=" * 60)
    
    required_files = {
        'Procfile': 'Comando de inicio para Gunicorn',
        'requirements.txt': 'Dependencias Python',
        'build.sh': 'Script de build',
        'casa_de_cambios/settings.py': 'Configuración Django',
        '.gitignore': 'Archivos a ignorar',
    }
    
    for file, desc in required_files.items():
        if os.path.exists(file):
            print(f"  ✅ {file} - {desc}")
        else:
            print(f"  ❌ {file} - {desc} (FALTANTE)")
            issues.append(f"Archivo faltante: {file}")
    
    # Resultado final
    print("\n" + "=" * 60)
    if not issues:
        print("✅ CONFIGURACIÓN LISTA PARA RENDER")
        print("=" * 60)
        print("\n🚀 Próximos pasos:")
        print("  1. git add .")
        print("  2. git commit -m 'Fix: Configuración para Render'")
        print("  3. git push origin devel0p")
        return True
    else:
        print("❌ SE ENCONTRARON PROBLEMAS CRÍTICOS")
        print("=" * 60)
        print(f"\n⚠️  Total de problemas: {len(issues)}")
        print("Corrígelos antes de hacer deploy.")
        return False

if __name__ == '__main__':
    success = check_settings()
    sys.exit(0 if success else 1)
