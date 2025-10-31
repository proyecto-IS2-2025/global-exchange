#!/usr/bin/env python
"""
Script para probar si SIFEN TEST acepta números fuera del rango asignado
Vamos a intentar generar una factura con número 150 (fuera del rango 51-100)
"""
import psycopg2

# Configuración SQL Proxy
SQL_PROXY_CONFIG = {
    'host': 'localhost',
    'port': 45432,
    'database': 'fs_proxy_bd',
    'user': 'fs_proxy_user',
    'password': 'p123456'
}

TIMBRADO_CONFIG = {
    'numero': '80002247',
    'establecimiento': '001',
    'punto_expedicion': '003'
}

EMISOR_CONFIG = {
    'ruc': '2595733',
    'dv': '3',
    'nombre': 'DE generado en ambiente de prueba - sin valor comercial ni fiscal'
}

FACTURACION_CONFIG = {
    'numero_inicial': 51,
    'numero_final': 100
}

def test_numero_fuera_rango():
    """
    Prueba intentar crear una factura con número 150 (fuera del rango 51-100)
    directamente en SQL Proxy para ver si SIFEN TEST lo rechaza
    """
    print("="*70)
    print("🧪 TEST: ¿SIFEN TEST valida el rango de numeración asignado?")
    print("="*70)
    print(f"\n📋 Rango asignado: {FACTURACION_CONFIG['numero_inicial']}-{FACTURACION_CONFIG['numero_final']}")
    print(f"🎯 Número a probar: 0000150 (FUERA DEL RANGO)")
    print()
    
    try:
        conn = psycopg2.connect(
            host=SQL_PROXY_CONFIG['host'],
            port=SQL_PROXY_CONFIG['port'],
            database=SQL_PROXY_CONFIG['database'],
            user=SQL_PROXY_CONFIG['user'],
            password=SQL_PROXY_CONFIG['password']
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Intentar insertar una factura con número 150
        numero_prueba = "0000150"
        
        print(f"📝 Insertando factura de prueba con número: {numero_prueba}")
        print(f"   Timbrado: {TIMBRADO_CONFIG['numero']}")
        print(f"   Establecimiento: {TIMBRADO_CONFIG['establecimiento']}")
        print(f"   Punto Expedición: {TIMBRADO_CONFIG['punto_expedicion']}")
        print()
        
        # Crear el INSERT básico
        cursor.execute(f"""
            INSERT INTO public.de
            (itide, dfeemide, dest, dpunexp, dnumdoc, cdc, dserienum, estado, 
             drucemi, ddvemi, dnomemi, itiptra, itimp, cmoneope, dcondticam, 
             dticam, dnomfan, dnombod, inaturec, itiope, ddestiope, itipidrecruc, 
             drucrecgral, ddvrecruc, dnomrec, ddirrec, inumdocrecrucgral, idnattip, 
             ddesnattip, dnumidrec, ddesnumidrec, cemisrec, dtelrec, iindpres, 
             ddesindpres, icondope, ddescondope, dicondinipag, ddescondinipag, 
             itipcondinipag, ddestipcondinipag, dmonitipag, iitemopera, dtotope, 
             dtotdesc, dtotdescglob, dtotdescglobi, dtotantitem, dtotantglobi, 
             dtotant, dporc, dsaldoant, drespe)
            VALUES 
            (1, NOW(), '{TIMBRADO_CONFIG['establecimiento']}', 
             '{TIMBRADO_CONFIG['punto_expedicion']}', '{numero_prueba}', 
             '0', '001003{numero_prueba}', 'borrador',
             '{EMISOR_CONFIG['ruc']}', '{EMISOR_CONFIG['dv']}', 
             '{EMISOR_CONFIG['nombre']}', 1, 1, 'PYG', 1,
             1, NULL, NULL, 1, 1, 'Venta de bienes', 1,
             '80026216', '9', 'CLIENTE DE PRUEBA', 'ASUNCION', NULL, NULL,
             NULL, NULL, NULL, 1, '0981123456', 1,
             'Operación presencial', 1, 'Contado', NULL, NULL,
             NULL, NULL, 100000, 1, 100000,
             0, 0, 0, 0, 0,
             0, 0, 0, 100000)
            RETURNING id
        """)
        
        de_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✅ Factura insertada en SQL Proxy con ID: {de_id}")
        print(f"   → Estado inicial: borrador")
        print()
        print("⏳ Esperando 5 segundos para que SQL Proxy procese...")
        
        import time
        time.sleep(5)
        
        # Consultar el estado
        cursor.execute(f"""
            SELECT id, dnumdoc, estado, estado_sifen, desc_sifen, error_sifen, cdc
            FROM public.de
            WHERE id = {de_id}
        """)
        
        result = cursor.fetchone()
        
        print("\n📊 RESULTADO:")
        print("="*70)
        print(f"ID: {result[0]}")
        print(f"Número: {result[1]}")
        print(f"Estado: {result[2]}")
        print(f"Estado SIFEN: {result[3] or 'NULL'}")
        print(f"Descripción SIFEN: {result[4] or 'NULL'}")
        print(f"Error SIFEN: {result[5] or 'NULL'}")
        print(f"CDC: {result[6] or '0'}")
        print("="*70)
        
        # Interpretación
        print("\n🔍 INTERPRETACIÓN:")
        if result[3] and 'Aprobado' in str(result[3]):
            print("✅ SIFEN TEST **ACEPTÓ** el número 150 (fuera del rango)")
            print("   → Conclusión: En TEST puedes usar cualquier número")
            print("   → Tu rango 51-100 es solo organizativo para el curso")
        elif result[3] and 'Rechazado' in str(result[3]):
            print("❌ SIFEN TEST **RECHAZÓ** el número 150")
            print(f"   → Motivo: {result[4]}")
            print("   → Conclusión: SIFEN valida el rango incluso en TEST")
        else:
            print("⏳ La factura aún está en procesamiento")
            print("   → Espera 30-60 segundos y consulta el estado manualmente")
        
        # Limpiar - eliminar la factura de prueba
        print("\n🗑️  Limpiando factura de prueba...")
        cursor.execute(f"DELETE FROM public.de WHERE id = {de_id}")
        conn.commit()
        print("✅ Factura de prueba eliminada")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "="*70)
    print("FIN DEL TEST")
    print("="*70)

if __name__ == '__main__':
    test_numero_fuera_rango()
