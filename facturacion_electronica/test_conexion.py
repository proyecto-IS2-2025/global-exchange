#!/usr/bin/env python3
"""
Script de prueba rápida para verificar la conexión al SQL Proxy
"""
import os
import sys

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2

# Configuración
SQL_PROXY_CONFIG = {
    'host': 'localhost',
    'port': 45432,
    'database': 'fs_proxy_bd',
    'user': 'fs_proxy_user',
    'password': 'p123456'
}

def test_conexion():
    """Prueba la conexión al SQL Proxy"""
    print("="*60)
    print("PRUEBA DE CONEXIÓN AL SQL PROXY")
    print("="*60)
    print()
    
    print("Intentando conectar a:")
    print(f"  Host: {SQL_PROXY_CONFIG['host']}")
    print(f"  Puerto: {SQL_PROXY_CONFIG['port']}")
    print(f"  Base de datos: {SQL_PROXY_CONFIG['database']}")
    print(f"  Usuario: {SQL_PROXY_CONFIG['user']}")
    print()
    
    try:
        connection = psycopg2.connect(
            host=SQL_PROXY_CONFIG['host'],
            port=SQL_PROXY_CONFIG['port'],
            database=SQL_PROXY_CONFIG['database'],
            user=SQL_PROXY_CONFIG['user'],
            password=SQL_PROXY_CONFIG['password']
        )
        cursor = connection.cursor()
        
        print("✓ CONEXIÓN EXITOSA")
        print()
        
        # Obtener versión de PostgreSQL
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"Versión PostgreSQL: {version[:50]}...")
        print()
        
        # Verificar tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tablas = cursor.fetchall()
        
        print("Tablas disponibles:")
        for tabla in tablas:
            print(f"  - {tabla[0]}")
        print()
        
        # Verificar si existe configuración ESI
        cursor.execute("SELECT COUNT(*) FROM public.esi;")
        count_esi = cursor.fetchone()[0]
        
        if count_esi > 0:
            print(f"✓ Configuración ESI encontrada ({count_esi} registro(s))")
            
            cursor.execute("SELECT ruc, ruc_dv, nombre, estado FROM public.esi LIMIT 1;")
            esi = cursor.fetchone()
            print(f"  RUC: {esi[0]}-{esi[1]}")
            print(f"  Nombre: {esi[2]}")
            print(f"  Estado: {esi[3]}")
        else:
            print("⚠ No hay configuración ESI")
            print("  Ejecuta: python facturacion_electronica/inicializar_esi.py")
        print()
        
        # Verificar documentos electrónicos
        cursor.execute("SELECT COUNT(*) FROM public.de;")
        count_de = cursor.fetchone()[0]
        print(f"Documentos electrónicos en el sistema: {count_de}")
        
        if count_de > 0:
            cursor.execute("""
                SELECT dnumdoc, estado, estado_sifen 
                FROM public.de 
                ORDER BY id DESC 
                LIMIT 3;
            """)
            documentos = cursor.fetchall()
            print("Últimos documentos:")
            for doc in documentos:
                print(f"  - {doc[0]}: Estado={doc[1]}, SIFEN={doc[2]}")
        print()
        
        cursor.close()
        connection.close()
        
        print("="*60)
        print("✓ PRUEBA COMPLETADA EXITOSAMENTE")
        print("="*60)
        print()
        print("Siguiente paso: Ejecutar ejemplo_uso.py para generar una factura")
        print()
        
        return True
        
    except psycopg2.OperationalError as e:
        print("✗ ERROR DE CONEXIÓN")
        print()
        print(f"Detalle: {e}")
        print()
        print("Posibles causas:")
        print("  1. Los contenedores del SQL Proxy no están levantados")
        print("  2. El puerto 45432 no está disponible")
        print("  3. Docker no está ejecutándose")
        print()
        print("Solución:")
        print("  cd /home/jose/proyecto_is2/sql-proxy01")
        print("  docker compose -f docker-compose.test.yml up -d")
        print()
        
        return False
    
    except Exception as e:
        print("✗ ERROR INESPERADO")
        print()
        print(f"Detalle: {e}")
        print()
        
        return False


if __name__ == "__main__":
    exito = test_conexion()
    sys.exit(0 if exito else 1)
