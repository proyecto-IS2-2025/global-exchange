#!/usr/bin/env python3
"""
Script para consultar el último número de factura utilizado en SIFEN
a través de la API de Factura Segura.

Este script intenta determinar cuál es el último número de factura
generado consultando el estado de múltiples facturas en orden descendente.
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la API
API_BASE_URL = os.getenv('FACTURA_SEGURA_API_URL', 'https://apitest.facturasegura.com.py')
AUTH_TOKEN = os.getenv('FACTURA_SEGURA_TOKEN')
RUC_EMISOR = os.getenv('FACTURA_SEGURA_RUC', '80002247')

# Configuración de numeración
ESTABLECIMIENTO = os.getenv('FACTURA_SEGURA_ESTABLECIMIENTO', '001')
PUNTO_EXPEDICION = os.getenv('FACTURA_SEGURA_PUNTO_EXPEDICION', '001')
TIMBRADO = os.getenv('FACTURA_SEGURA_TIMBRADO', '80002247')

# Rango de búsqueda
NUMERO_INICIAL = 1
NUMERO_FINAL = 200  # Ajusta según necesites


def generar_cdc(numero_factura):
    """
    Genera un CDC basado en el número de factura.
    NOTA: Este es un CDC aproximado. El CDC real se genera en el servidor.
    
    Formato CDC: RUC(8) + DV(1) + ESTABLECIMIENTO(3) + PUNTO_EXP(3) + 
                 NUMERO(7) + TIPO_CONTRIB(1) + FECHA(8) + CODIGO_SEG(9)
    """
    # Esto es solo una aproximación, el CDC real incluye código de seguridad
    # que solo conoce el servidor
    fecha = datetime.now().strftime('%Y%m%d')
    numero_str = str(numero_factura).zfill(7)
    
    # CDC aproximado (no será válido para consulta real)
    # Necesitaremos usar otro enfoque
    return None


def consultar_estado_sifen(cdc):
    """
    Consulta el estado de un documento electrónico en SIFEN.
    
    Args:
        cdc: Código de Control del documento
        
    Returns:
        dict con la respuesta de la API
    """
    url = f"{API_BASE_URL}/misife00/v1/esi"
    
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authentication-Token': AUTH_TOKEN
    }
    
    payload = {
        "operation": "get_estado_sifen",
        "params": {
            "CDC": cdc,
            "dRucEm": RUC_EMISOR
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "code": -1}


def intentar_generar_factura_prueba(numero):
    """
    Intenta generar una factura mínima para verificar si el número ya existe.
    Si SIFEN la rechaza por duplicado, sabemos que existe.
    
    ADVERTENCIA: Esta función NO debe ejecutarse en producción sin cuidado,
    ya que podría generar facturas reales.
    """
    # Esta función está deshabilitada por seguridad
    # En su lugar, se recomienda usar el método de consulta directa a la base de datos
    pass


def buscar_en_base_datos_local():
    """
    Busca el último número de factura en la base de datos local del proyecto.
    Este es el método RECOMENDADO.
    """
    try:
        import django
        import os
        import sys
        
        # Configurar Django
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
        django.setup()
        
        from facturacion_electronica.models import FacturaElectronica
        
        # Buscar la última factura generada
        ultima_factura = FacturaElectronica.objects.filter(
            estado_sifen__in=['Aprobado', 'Aprobado con observación', 'ENVIADO_A_SIFEN', 'SOL.APROBACION']
        ).order_by('-numero_factura').first()
        
        if ultima_factura:
            print("\n" + "="*80)
            print("ÚLTIMA FACTURA ENCONTRADA EN BASE DE DATOS LOCAL")
            print("="*80)
            print(f"Número de Factura: {ultima_factura.numero_factura}")
            print(f"Establecimiento: {ultima_factura.establecimiento}")
            print(f"Punto Expedición: {ultima_factura.punto_expedicion}")
            print(f"Estado SIFEN: {ultima_factura.estado_sifen}")
            print(f"CDC: {ultima_factura.cdc}")
            print(f"Fecha Emisión: {ultima_factura.fecha_emision}")
            print(f"Monto Total: {ultima_factura.monto_total}")
            print("="*80)
            print(f"\n✅ PRÓXIMO NÚMERO DISPONIBLE: {int(ultima_factura.numero_factura) + 1}")
            print("="*80)
            
            return {
                'ultimo_numero': ultima_factura.numero_factura,
                'proximo_numero': str(int(ultima_factura.numero_factura) + 1).zfill(7),
                'cdc': ultima_factura.cdc,
                'estado': ultima_factura.estado_sifen
            }
        else:
            print("\n⚠️  No se encontraron facturas en la base de datos local.")
            print(f"    Puedes comenzar desde el número: {str(NUMERO_INICIAL).zfill(7)}")
            return {
                'ultimo_numero': '0000000',
                'proximo_numero': str(NUMERO_INICIAL).zfill(7)
            }
            
    except Exception as e:
        print(f"\n❌ Error al consultar la base de datos: {e}")
        return None


def consultar_via_sql_proxy():
    """
    Consulta el último número de factura a través del SQL Proxy.
    Este método consulta directamente la base de datos de Factura Segura.
    """
    try:
        # Conectar al SQL Proxy
        import psycopg2
        
        sql_proxy_host = os.getenv('SQL_PROXY_HOST', 'localhost')
        sql_proxy_port = os.getenv('SQL_PROXY_PORT', '45432')
        sql_proxy_db = os.getenv('SQL_PROXY_DB', 'fs_db')
        sql_proxy_user = os.getenv('SQL_PROXY_USER', 'postgres')
        sql_proxy_pass = os.getenv('SQL_PROXY_PASS', 'postgres')
        
        conn = psycopg2.connect(
            host=sql_proxy_host,
            port=sql_proxy_port,
            database=sql_proxy_db,
            user=sql_proxy_user,
            password=sql_proxy_pass
        )
        
        cursor = conn.cursor()
        
        # Consulta SQL para obtener la última factura del emisor
        query = """
        SELECT 
            numero_factura,
            establecimiento,
            punto_expedicion,
            cdc,
            estado_sifen,
            fecha_emision,
            monto_total
        FROM facturas_electronicas
        WHERE ruc_emisor = %s
          AND establecimiento = %s
          AND punto_expedicion = %s
          AND estado_sifen IN ('Aprobado', 'Aprobado con observación', 'ENVIADO_A_SIFEN')
        ORDER BY numero_factura DESC
        LIMIT 1;
        """
        
        cursor.execute(query, (RUC_EMISOR, ESTABLECIMIENTO, PUNTO_EXPEDICION))
        result = cursor.fetchone()
        
        if result:
            numero, est, pto, cdc, estado, fecha, monto = result
            print("\n" + "="*80)
            print("ÚLTIMA FACTURA ENCONTRADA EN SIFEN (VIA SQL PROXY)")
            print("="*80)
            print(f"Número de Factura: {numero}")
            print(f"Establecimiento: {est}")
            print(f"Punto Expedición: {pto}")
            print(f"Estado SIFEN: {estado}")
            print(f"CDC: {cdc}")
            print(f"Fecha Emisión: {fecha}")
            print(f"Monto Total: {monto}")
            print("="*80)
            print(f"\n✅ PRÓXIMO NÚMERO DISPONIBLE: {int(numero) + 1}")
            print("="*80)
            
            return {
                'ultimo_numero': numero,
                'proximo_numero': str(int(numero) + 1).zfill(7),
                'cdc': cdc,
                'estado': estado
            }
        else:
            print("\n⚠️  No se encontraron facturas en SIFEN para este emisor.")
            return None
            
        cursor.close()
        conn.close()
        
    except ImportError:
        print("\n❌ psycopg2 no está instalado. Instálalo con: pip install psycopg2-binary")
        return None
    except Exception as e:
        print(f"\n❌ Error al consultar SQL Proxy: {e}")
        return None


def main():
    """Función principal"""
    print("\n" + "="*80)
    print("CONSULTA DE ÚLTIMO NÚMERO DE FACTURA ELECTRÓNICA")
    print("="*80)
    print(f"Emisor RUC: {RUC_EMISOR}")
    print(f"Establecimiento: {ESTABLECIMIENTO}")
    print(f"Punto Expedición: {PUNTO_EXPEDICION}")
    print(f"Timbrado: {TIMBRADO}")
    print("="*80)
    
    if not AUTH_TOKEN:
        print("\n⚠️  ADVERTENCIA: No se encontró el token de autenticación.")
        print("    Configure la variable FACTURA_SEGURA_TOKEN en el archivo .env")
        print("\n    Intentando consulta local...\n")
    
    # Método 1: Consultar base de datos local (RECOMENDADO)
    print("\n📊 Método 1: Consultando base de datos local de Django...")
    resultado_local = buscar_en_base_datos_local()
    
    if resultado_local:
        return resultado_local
    
    # Método 2: Consultar a través de SQL Proxy (si está disponible)
    print("\n📊 Método 2: Consultando a través de SQL Proxy...")
    resultado_proxy = consultar_via_sql_proxy()
    
    if resultado_proxy:
        return resultado_proxy
    
    # Si ningún método funcionó
    print("\n❌ No se pudo determinar el último número de factura.")
    print("    Opciones:")
    print("    1. Verifica que tengas facturas generadas en tu base de datos")
    print("    2. Verifica la conexión al SQL Proxy")
    print("    3. Consulta manualmente en el portal de Factura Segura")
    
    return None


if __name__ == "__main__":
    resultado = main()
    
    if resultado:
        print("\n✅ Consulta completada exitosamente")
        print(f"\n💡 RECOMENDACIÓN PARA EL EQUIPO:")
        print(f"   Todos deben comenzar desde el número: {resultado['proximo_numero']}")
        print(f"   Y coordinar quién usa qué rango de números.")
        print("\n   Ejemplo de asignación por desarrollador:")
        siguiente = int(resultado['proximo_numero'])
        print(f"   - Desarrollador 1: {siguiente} - {siguiente + 49}")
        print(f"   - Desarrollador 2: {siguiente + 50} - {siguiente + 99}")
        print(f"   - Desarrollador 3: {siguiente + 100} - {siguiente + 149}")
