#!/usr/bin/env python
"""
Script de diagnóstico para verificar estado de facturas en SIFEN
Verifica la estructura de la base de datos y el estado real de las facturas
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

# Agregar el path del proyecto
sys.path.insert(0, '/home/jose/proyecto_is2/global-exchange')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Configuración del SQL Proxy
SQL_PROXY_CONFIG = {
    'host': 'localhost',
    'port': 45432,
    'database': 'fs_proxy_bd',
    'user': 'fs_proxy_user',
    'password': 'p123456'
}

def conectar_sql_proxy():
    """Conecta al SQL Proxy"""
    try:
        conn = psycopg2.connect(
            host=SQL_PROXY_CONFIG['host'],
            port=SQL_PROXY_CONFIG['port'],
            database=SQL_PROXY_CONFIG['database'],
            user=SQL_PROXY_CONFIG['user'],
            password=SQL_PROXY_CONFIG['password']
        )
        print(f"✅ Conectado a SQL Proxy: {SQL_PROXY_CONFIG['database']}")
        return conn
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return None

def verificar_estructura_tabla(conn):
    """Verifica la estructura de la tabla 'de' (documentos electrónicos)"""
    print("\n" + "="*80)
    print("📋 ESTRUCTURA DE LA TABLA 'de' (Documentos Electrónicos)")
    print("="*80)
    
    cursor = conn.cursor()
    
    # Obtener nombres de columnas
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'de'
        ORDER BY ordinal_position;
    """)
    
    columnas = cursor.fetchall()
    
    if not columnas:
        print("⚠️ No se encontraron columnas. Intentando con mayúsculas...")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'DE'
            ORDER BY ordinal_position;
        """)
        columnas = cursor.fetchall()
    
    print(f"\n📊 Total de columnas: {len(columnas)}\n")
    print(f"{'Columna':<30} {'Tipo':<20} {'Max Length'}")
    print("-" * 80)
    
    for col in columnas:
        nombre = col[0]
        tipo = col[1]
        max_len = col[2] if col[2] else '-'
        print(f"{nombre:<30} {tipo:<20} {max_len}")
    
    cursor.close()
    return columnas

def listar_facturas_recientes(conn):
    """Lista las facturas más recientes"""
    print("\n" + "="*80)
    print("📄 FACTURAS RECIENTES (últimas 5)")
    print("="*80)
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Intentar consulta con nombres en minúsculas primero
    try:
        cursor.execute("""
            SELECT id, dnumdoc, estado, estado_sifen, desc_sifen, 
                   error_sifen, cdc, dfeemide, fch_ins
            FROM public.de
            ORDER BY id DESC
            LIMIT 5;
        """)
        facturas = cursor.fetchall()
        print("✅ Consulta exitosa con nombres en minúsculas\n")
    except Exception as e:
        print(f"⚠️ Error con minúsculas: {e}")
        print("Intentando con mayúsculas...\n")
        
        cursor.execute("""
            SELECT id, "dNumDoc", estado, estado_sifen, desc_sifen, 
                   error_sifen, "CDC", "dFeEmiDE", fch_ins
            FROM public.de
            ORDER BY id DESC
            LIMIT 5;
        """)
        facturas = cursor.fetchall()
        print("✅ Consulta exitosa con nombres en MAYÚSCULAS\n")
    
    if not facturas:
        print("⚠️ No hay facturas en la base de datos")
        cursor.close()
        return []
    
    for i, factura in enumerate(facturas, 1):
        print(f"\n{'─'*80}")
        print(f"FACTURA #{i}")
        print(f"{'─'*80}")
        for key, value in factura.items():
            print(f"  {key:<20}: {value}")
    
    cursor.close()
    return facturas

def verificar_factura_especifica(conn, numero_factura):
    """Verifica una factura específica por número"""
    print("\n" + "="*80)
    print(f"🔍 VERIFICACIÓN DE FACTURA: {numero_factura}")
    print("="*80)
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Probar diferentes formatos de consulta
    queries = [
        # Formato 1: minúsculas
        f"""
        SELECT * FROM public.de
        WHERE dnumdoc = '{numero_factura}'
        ORDER BY id DESC LIMIT 1;
        """,
        # Formato 2: mayúsculas
        f"""
        SELECT * FROM public.de
        WHERE "dNumDoc" = '{numero_factura}'
        ORDER BY id DESC LIMIT 1;
        """,
        # Formato 3: CAST
        f"""
        SELECT * FROM public.de
        WHERE CAST(dnumdoc AS TEXT) = '{numero_factura}'
        ORDER BY id DESC LIMIT 1;
        """
    ]
    
    factura = None
    query_exitosa = None
    
    for i, query in enumerate(queries, 1):
        try:
            cursor.execute(query)
            factura = cursor.fetchone()
            if factura:
                query_exitosa = i
                print(f"✅ Factura encontrada con query #{i}\n")
                break
        except Exception as e:
            print(f"❌ Query #{i} falló: {e}")
    
    if not factura:
        print(f"\n⚠️ No se encontró la factura {numero_factura}")
        cursor.close()
        return None
    
    # Mostrar todos los campos
    print(f"\n📋 DETALLES COMPLETOS DE LA FACTURA:")
    print("─" * 80)
    for key, value in factura.items():
        if value is not None and value != '':
            print(f"  {key:<30}: {value}")
    
    # Verificar campos críticos
    print(f"\n🔑 CAMPOS CRÍTICOS PARA SIFEN:")
    print("─" * 80)
    
    campos_criticos = [
        ('id', 'ID en base de datos'),
        ('estado', 'Estado del documento'),
        ('estado_sifen', 'Estado en SIFEN'),
        ('desc_sifen', 'Descripción SIFEN'),
        ('error_sifen', 'Error SIFEN'),
        ('cdc', 'CDC (Código de Control)'),
        ('CDC', 'CDC (mayúsculas)'),
        ('dnumdoc', 'Número de documento'),
        ('dNumDoc', 'Número de documento (mayúsculas)'),
    ]
    
    for campo, descripcion in campos_criticos:
        valor = factura.get(campo)
        if valor is not None and valor != '':
            icono = "✅" if valor else "⚠️"
            print(f"  {icono} {descripcion:<35}: {valor}")
    
    cursor.close()
    return factura

def verificar_archivos_pdf(numero_factura):
    """Verifica si existen archivos PDF generados"""
    print("\n" + "="*80)
    print(f"📁 VERIFICACIÓN DE ARCHIVOS PDF")
    print("="*80)
    
    import glob
    from datetime import datetime
    
    # Directorios donde buscar
    fecha_str = datetime.now().strftime('%Y%m')
    rutas_busqueda = [
        f'/home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/{fecha_str}',
        f'/home/jose/proyecto_is2/sql-proxy01/volumes/web/kude',
        '/home/jose/proyecto_is2/sql-proxy01/volumes/web',
    ]
    
    print(f"\n🔍 Buscando archivos para factura: {numero_factura}")
    print(f"📅 Fecha actual: {fecha_str}\n")
    
    archivos_encontrados = []
    
    for ruta in rutas_busqueda:
        patron = f"{ruta}/*{numero_factura}*"
        print(f"  Buscando en: {patron}")
        
        archivos = glob.glob(patron)
        if archivos:
            archivos_encontrados.extend(archivos)
            for archivo in archivos:
                print(f"    ✅ Encontrado: {archivo}")
        else:
            print(f"    ⚠️ No se encontraron archivos")
    
    if not archivos_encontrados:
        print(f"\n❌ No se encontraron archivos PDF/XML para la factura {numero_factura}")
        print(f"\n💡 Esto puede significar:")
        print(f"   1. SIFEN aún no ha procesado la factura")
        print(f"   2. El PDF no se ha generado todavía")
        print(f"   3. Hay un error en el procesamiento")
    else:
        print(f"\n✅ Total de archivos encontrados: {len(archivos_encontrados)}")
    
    return archivos_encontrados

def main():
    """Función principal"""
    print("\n" + "🔍 " + "="*76 + " 🔍")
    print("    DIAGNÓSTICO COMPLETO - ESTADO DE FACTURAS EN SIFEN")
    print("🔍 " + "="*76 + " 🔍\n")
    
    # Conectar
    conn = conectar_sql_proxy()
    if not conn:
        return
    
    try:
        # 1. Verificar estructura de la tabla
        verificar_estructura_tabla(conn)
        
        # 2. Listar facturas recientes
        facturas = listar_facturas_recientes(conn)
        
        # 3. Si se proporciona un número de factura específico
        if len(sys.argv) > 1:
            numero_factura = sys.argv[1]
            factura = verificar_factura_especifica(conn, numero_factura)
            
            if factura:
                # 4. Verificar archivos PDF
                verificar_archivos_pdf(numero_factura)
        else:
            print("\n" + "="*80)
            print("💡 AYUDA")
            print("="*80)
            print("\nPara verificar una factura específica, ejecuta:")
            print(f"  python {sys.argv[0]} 0000075")
            print("\nDonde '0000075' es el número de factura a verificar.")
    
    finally:
        conn.close()
        print("\n" + "="*80)
        print("✅ Diagnóstico completado")
        print("="*80 + "\n")

if __name__ == '__main__':
    main()
