#!/usr/bin/env python3
"""
🚀 SCRIPT DE CONFIGURACIÓN AUTOMÁTICA DE RANGO DE FACTURAS

Este script configura automáticamente tu rango de facturas:
1. Consulta el último número usado en el sistema
2. Te asigna automáticamente los próximos 50 números disponibles
3. Actualiza tu archivo .env con la configuración
4. Verifica que todo esté correcto

USO:
    poetry run python configurar_rango_automatico.py

NOTA: Este script es SEGURO. Cada desarrollador obtiene un rango único
      basado en el momento en que ejecuta el script.
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from facturacion_electronica.models import FacturaElectronica
from django.db.models import Max
from datetime import datetime
import re


def leer_archivo_env():
    """Lee el contenido actual del archivo .env"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def actualizar_env(numero_inicial, numero_final):
    """
    Actualiza el archivo .env con el rango asignado.
    Si las variables ya existen, las actualiza. Si no, las agrega.
    """
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    contenido = leer_archivo_env()
    
    # Preparar las nuevas líneas
    configuracion = f"""
# ============================================================
# CONFIGURACIÓN DE FACTURACIÓN - RANGO ASIGNADO AUTOMÁTICAMENTE
# Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ============================================================
FACTURACION_NUMERO_INICIAL={numero_inicial}
FACTURACION_NUMERO_FINAL={numero_final}
FACTURACION_ESTABLECIMIENTO=001
FACTURACION_PUNTO_EXPEDICION=003
"""
    
    # Verificar si ya existen las variables
    tiene_inicial = 'FACTURACION_NUMERO_INICIAL' in contenido
    tiene_final = 'FACTURACION_NUMERO_FINAL' in contenido
    
    if tiene_inicial or tiene_final:
        # Actualizar las variables existentes
        contenido = re.sub(
            r'FACTURACION_NUMERO_INICIAL=\d+',
            f'FACTURACION_NUMERO_INICIAL={numero_inicial}',
            contenido
        )
        contenido = re.sub(
            r'FACTURACION_NUMERO_FINAL=\d+',
            f'FACTURACION_NUMERO_FINAL={numero_final}',
            contenido
        )
        print(f"   ✅ Variables actualizadas en .env")
    else:
        # Agregar al final del archivo
        if contenido and not contenido.endswith('\n'):
            contenido += '\n'
        contenido += configuracion
        print(f"   ✅ Variables agregadas a .env")
    
    # Escribir el archivo
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    return env_path


def extraer_numero(numero_completo):
    """Extrae el número de una factura en formato 001-003-0000082"""
    if '-' in numero_completo:
        return int(numero_completo.split('-')[2])
    return int(numero_completo)


def obtener_ultimo_numero_usado():
    """Consulta el último número de factura usado en la base de datos"""
    ultima_factura = FacturaElectronica.objects.aggregate(
        Max('numero_factura')
    )['numero_factura__max']
    
    if ultima_factura:
        return extraer_numero(ultima_factura)
    return 0


def calcular_rango_disponible(ultimo_usado, cantidad=50):
    """
    Calcula el próximo rango disponible de números.
    
    Args:
        ultimo_usado: Último número usado en el sistema
        cantidad: Cantidad de números a asignar (default: 50)
    
    Returns:
        tuple: (numero_inicial, numero_final)
    """
    # El próximo disponible es el último usado + 1
    proximo = ultimo_usado + 1
    
    # Asignar los próximos 'cantidad' números
    inicial = proximo
    final = proximo + cantidad - 1
    
    return inicial, final


def main():
    print("\n" + "="*80)
    print("🚀 CONFIGURACIÓN AUTOMÁTICA DE RANGO DE FACTURAS")
    print("="*80)
    
    # Paso 1: Consultar último número usado
    print("\n📊 PASO 1: Consultando el último número usado en el sistema...")
    
    try:
        ultimo_usado = obtener_ultimo_numero_usado()
        print(f"   Último número usado: {ultimo_usado:07d}")
    except Exception as e:
        print(f"   ❌ Error al consultar la base de datos: {e}")
        print("\n   ⚠️  Asegúrate de que:")
        print("      1. La base de datos esté accesible")
        print("      2. Las variables de entorno estén configuradas")
        sys.exit(1)
    
    # Paso 2: Calcular rango disponible
    print("\n🔢 PASO 2: Calculando tu rango automáticamente...")
    
    inicial, final = calcular_rango_disponible(ultimo_usado, cantidad=50)
    
    print(f"   Tu rango asignado: {inicial} - {final}")
    print(f"   Total de números: {final - inicial + 1}")
    
    # Paso 3: Verificar si hay configuración previa
    contenido_actual = leer_archivo_env()
    tiene_config = 'FACTURACION_NUMERO_INICIAL' in contenido_actual
    
    if tiene_config:
        # Extraer configuración actual
        match_inicial = re.search(r'FACTURACION_NUMERO_INICIAL=(\d+)', contenido_actual)
        match_final = re.search(r'FACTURACION_NUMERO_FINAL=(\d+)', contenido_actual)
        
        if match_inicial and match_final:
            actual_inicial = int(match_inicial.group(1))
            actual_final = int(match_final.group(1))
            
            print(f"\n   ⚠️  Ya tienes un rango configurado:")
            print(f"      Rango actual: {actual_inicial} - {actual_final}")
            print(f"      Nuevo rango propuesto: {inicial} - {final}")
            
            respuesta = input("\n   ¿Quieres actualizar al nuevo rango? (s/n): ").lower()
            if respuesta != 's':
                print("\n   ℹ️  Configuración mantenida. No se realizaron cambios.")
                sys.exit(0)
    
    # Paso 4: Actualizar .env
    print("\n💾 PASO 3: Actualizando tu archivo .env...")
    
    try:
        from datetime import datetime
        env_path = actualizar_env(inicial, final)
        print(f"   Archivo actualizado: {env_path}")
    except Exception as e:
        print(f"   ❌ Error al actualizar .env: {e}")
        sys.exit(1)
    
    # Paso 5: Verificar configuración
    print("\n✅ PASO 4: Verificando la configuración...")
    
    # Recargar las variables de entorno
    os.environ['FACTURACION_NUMERO_INICIAL'] = str(inicial)
    os.environ['FACTURACION_NUMERO_FINAL'] = str(final)
    
    from facturacion_electronica.utils import obtener_configuracion_facturacion
    
    config = obtener_configuracion_facturacion()
    
    if config['numero_inicial'] == inicial and config['numero_final'] == final:
        print(f"   ✅ Configuración cargada correctamente")
    else:
        print(f"   ⚠️  La configuración no se cargó correctamente")
        print(f"      Esperado: {inicial} - {final}")
        print(f"      Obtenido: {config['numero_inicial']} - {config['numero_final']}")
    
    # Resumen final
    print("\n" + "="*80)
    print("🎉 CONFIGURACIÓN COMPLETADA")
    print("="*80)
    print(f"\n✅ Tu rango de facturas:")
    print(f"   Número inicial: {inicial:07d}")
    print(f"   Número final: {final:07d}")
    print(f"   Total disponible: {final - inicial + 1} facturas")
    
    print(f"\n📋 Configuración guardada en:")
    print(f"   {env_path}")
    
    print(f"\n🔄 Próximos pasos:")
    print(f"   1. Reinicia el servidor Django:")
    print(f"      pkill -f runserver")
    print(f"      poetry run python manage.py runserver")
    print(f"   ")
    print(f"   2. (Opcional) Verifica tu configuración:")
    print(f"      poetry run python verificar_configuracion_rango.py")
    print(f"   ")
    print(f"   3. ¡Empieza a generar facturas!")
    print(f"      El sistema usará automáticamente números del {inicial} al {final}")
    
    print("\n" + "="*80)
    print("✅ ¡Todo listo! Puedes generar facturas sin conflictos con tus compañeros.")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuración cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        print("\nSi el problema persiste, contacta con el equipo.")
        sys.exit(1)
