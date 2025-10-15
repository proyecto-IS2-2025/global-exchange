"""
Script para iniciar todos los servicios necesarios para desarrollo
Ejecutar con: python scripts/start_dev.py
"""
import subprocess
import sys
import platform
import time
import os

def es_windows():
    return platform.system() == 'Windows'

def verificar_redis():
    """Verifica si Redis está corriendo"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis está corriendo")
        return True
    except:
        print("❌ Redis no está corriendo")
        return False

def verificar_docker():
    """Verifica si Docker está instalado"""
    try:
        subprocess.run(['docker', '--version'], capture_output=True, check=True)
        print("✅ Docker está instalado")
        return True
    except:
        print("❌ Docker no está instalado")
        return False

def iniciar_redis():
    """Inicia Redis con Docker"""
    print("\n🚀 Iniciando Redis...")
    try:
        # Intentar detener contenedor existente
        subprocess.run(['docker', 'stop', 'redis-global-exchange'], 
                      capture_output=True)
        subprocess.run(['docker', 'rm', 'redis-global-exchange'], 
                      capture_output=True)
        
        # Iniciar nuevo contenedor
        subprocess.run([
            'docker', 'run', '-d', 
            '-p', '6379:6379',
            '--name', 'redis-global-exchange',
            'redis:alpine'
        ], check=True)
        
        time.sleep(2)  # Esperar a que Redis inicie
        
        if verificar_redis():
            print("✅ Redis iniciado correctamente")
            return True
    except Exception as e:
        print(f"❌ Error al iniciar Redis: {e}")
        return False

def main():
    print("=" * 60)
    print("  🚀 INICIADOR DE SERVICIOS - GLOBAL EXCHANGE")
    print("=" * 60)
    
    # Verificar requisitos
    print("\n📋 Verificando requisitos...")
    
    if not verificar_docker():
        print("\n⚠️  Docker no está instalado.")
        print("Opciones:")
        print("1. Instalar Docker Desktop: https://www.docker.com/products/docker-desktop")
        print("2. Iniciar servicios manualmente (ver docs/COMO_EJECUTAR_NOTIFICACIONES.md)")
        return
    
    # Iniciar Redis si no está corriendo
    if not verificar_redis():
        if not iniciar_redis():
            print("\n❌ No se pudo iniciar Redis")
            return
    
    print("\n" + "=" * 60)
    print("  ✅ REDIS LISTO - Ahora inicia los demás servicios")
    print("=" * 60)
    
    if es_windows():
        print("\n🪟 Detectado: Windows")
        print("\nAbre 3 NUEVAS ventanas de PowerShell/CMD y ejecuta:")
        print("\n1️⃣  Terminal 1 - Celery Worker:")
        print("   make celery-worker")
        print("\n2️⃣  Terminal 2 - Celery Beat:")
        print("   make celery-beat")
        print("\n3️⃣  Terminal 3 - Django Server:")
        print("   make run")
    else:
        print("\n🐧 Detectado: Linux/Mac")
        print("\nAbre 3 NUEVAS terminales y ejecuta:")
        print("\n1️⃣  Terminal 1: make celery-worker")
        print("\n2️⃣  Terminal 2: make celery-beat")
        print("\n3️⃣  Terminal 3: make run")
    
    print("\n" + "=" * 60)
    print("  📖 Documentación completa en:")
    print("  docs/COMO_EJECUTAR_NOTIFICACIONES.md")
    print("=" * 60)

if __name__ == "__main__":
    main()
