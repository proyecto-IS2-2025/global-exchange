#!/usr/bin/env python3
"""
Script de prueba simple para verificar facturación (sin Django)
"""
import psycopg2
from datetime import datetime

# Configuración
SQL_PROXY_CONFIG = {
    'host': 'localhost',
    'port': 45432,
    'database': 'fs_proxy_bd',
    'user': 'fs_proxy_user',
    'password': 'p123456'
}

ESI_CONFIG = {
    'email': 'glex.globalexchange@gmail.com',
    'password': 'Globalexchange#2000',
    'url_test': 'https://apitest.facturasegura.com.py',
}

EMISOR_CONFIG = {
    'ruc': '2595733',
    'dv': '3',
}

TIMBRADO_CONFIG = {
    'numero': '02595733',
    'fecha_inicio': '2025-03-27',
    'establecimiento': '001',
    'punto_expedicion': '003'
}

def conectar():
    """Conectar al SQL Proxy"""
    try:
        connection = psycopg2.connect(
            host=SQL_PROXY_CONFIG['host'],
            port=SQL_PROXY_CONFIG['port'],
            database=SQL_PROXY_CONFIG['database'],
            user=SQL_PROXY_CONFIG['user'],
            password=SQL_PROXY_CONFIG['password']
        )
        cursor = connection.cursor()
        print("✓ Conectado al SQL Proxy")
        return connection, cursor
    except Exception as e:
        print(f"✗ Error al conectar: {e}")
        return None, None

def verificar_esi(cursor):
    """Verificar si existe ESI"""
    cursor.execute("SELECT COUNT(*) FROM public.esi;")
    count = cursor.fetchone()[0]
    return count > 0

def inicializar_esi(connection, cursor):
    """Inicializar ESI"""
    try:
        query = f"""
        INSERT INTO public.esi 
        (ruc, ruc_dv, nombre, descripcion, estado, esi_email, esi_passwd, esi_token, esi_url)
        VALUES (
            '{EMISOR_CONFIG['ruc']}', 
            '{EMISOR_CONFIG['dv']}', 
            'Global Exchange - Equipo 7', 
            'Casa de Cambios - Sistema de Facturación Electrónica', 
            'ACTIVO', 
            '{ESI_CONFIG['email']}', 
            '{ESI_CONFIG['password']}', 
            '', 
            '{ESI_CONFIG['url_test']}'
        );
        """
        cursor.execute(query)
        connection.commit()
        print("✓ ESI inicializado correctamente")
        return True
    except Exception as e:
        print(f"✗ Error al inicializar ESI: {e}")
        connection.rollback()
        return False

def obtener_proximo_numero(cursor):
    """Obtener próximo número de factura"""
    cursor.execute(f"""
        SELECT MAX(CAST(dNumDoc AS INTEGER)) as max_num
        FROM public.de
        WHERE dEst = '{TIMBRADO_CONFIG['establecimiento']}'
        AND dPunExp = '{TIMBRADO_CONFIG['punto_expedicion']}'
        AND CAST(dNumDoc AS INTEGER) >= 51
        AND CAST(dNumDoc AS INTEGER) <= 100
    """)
    result = cursor.fetchone()
    
    if result and result[0]:
        proximo = result[0] + 1
    else:
        proximo = 51
    
    if proximo > 100:
        raise Exception("Se alcanzó el límite de facturas (51-100)")
    
    return str(proximo).zfill(7)

def crear_factura_prueba(connection, cursor):
    """Crear una factura de prueba"""
    try:
        numero_factura = obtener_proximo_numero(cursor)
        fecha_emision = datetime.now().strftime("%Y-%m-%d")
        
        print(f"\nGenerando factura {numero_factura}...")
        
        # Insertar documento electrónico
        de_query = f"""
        INSERT INTO public.de
        (iTiDE, dFeEmiDE, dEst, dPunExp, dNumDoc, CDC, dSerieNum, estado, 
        estado_sifen, desc_sifen, error_sifen, fch_sifen, 
        estado_can, desc_can, error_can, fch_can, 
        estado_inu, desc_inu, error_inu, fch_inu, 
        iTipEmi, dNumTim, dFeIniT, iTipTra, iTImp, cMoneOpe, dTiCam, dInfoFisc, 
        dRucEm, dDVEmi, iTipCont, dNomEmi, dDirEmi, dNumCas, 
        cDepEmi, dDesDepEmi, cCiuEmi, dDesCiuEmi, dTelEmi, dEmailE, 
        iNatRec, iTiOpe, cPaisRec, iTiContRec, dRucRec, dDVRec, 
        iTipIDRec, dDTipIDRec, dNumIDRec, dNomRec, dEmailRec, 
        dDirRec, dNumCasRec, cDepRec, dDesDepRec, cCiuRec, dDesCiuRec, 
        iNatVen, iTipIDVen, dNumIDVen, dNomVen, dDirVen, dNumCasVen, 
        cDepVen, dDesDepVen, cCiuVen, dDesCiuVen, 
        dDirProv, cDepProv, dDesDepProv, cCiuProv, dDesCiuProv, 
        iMotEmi, iIndPres, iCondOpe, dPlazoCre, 
        dModCont, dEntCont, dAnoCont, dSecCont, dFeCodCont, 
        dSisFact, dInfAdic, 
        iMotEmiNR, iRespEmiNR, 
        iTipTrans, iModTrans, iRespFlete, dIniTras, dFinTras, 
        dDirLocSal, dNumCasSal, cDepSal, dDesDepSal, cCiuSal, dDesCiuSal, 
        dDirLocEnt, dNumCasEnt, cDepEnt, dDesDepEnt, cCiuEnt, dDesCiuEnt, 
        dTiVehTras, dMarVeh, dTipIdenVeh, dNroIDVeh, dNroMatVeh, 
        iNatTrans, dNomTrans, dRucTrans, dDVTrans, iTipIDTrans, dNumIDTrans, 
        dNumIDChof, dNomChof, 
        fch_ins, fch_upd)
        VALUES(
            '1', '{fecha_emision}', '001', '003', '{numero_factura}', 
            '0', '', 'Borrador', 
            '', '', '', '', '', '', '', '', '', '', '', '', 
            '1', '02595733', '2025-03-27', '2', '5', 'PYG', '1', '', 
            '2595733', '3', '1', 
            'DE generado en ambiente de prueba - sin valor comercial ni fiscal', 
            'YVAPOVO C/ TOBATI', '1543', 
            '1', 'CAPITAL', '1', 'ASUNCION (DISTRITO)', 
            '(0961)988439', 'ggonzar@gmail.com', 
            '1', '1', 'PRY', '1', '80026216', '6', 
            '0', '', '0', 'CLIENTE DE PRUEBA', 'cliente@example.com', 
            '', '', '', '', '', '', 
            '', '', '', '', '', '', '', '', '', '', 
            '', '', '', '', '', 
            '', '1', '1', '', 
            '', '', '', '', '', 
            '1', 'Operación de cambio de divisas - Global Exchange - PRUEBA', 
            '', '', 
            '', '', '', '', '', 
            '', '', '', '', '', '', 
            '', '', '', '', '', '', 
            '', '', '', '', '', 
            '', '', '', '', '', '', 
            '', '', 
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        RETURNING id;
        """
        cursor.execute(de_query)
        de_id = cursor.fetchone()[0]
        
        # Insertar actividades económicas
        cursor.execute(f"""
        INSERT INTO public.gActEco (cActEco, dDesActEco, fch_ins, fch_upd, de_id)
        VALUES 
        ('62010', 'Actividades de programación informática', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id}),
        ('74909', 'Otras actividades profesionales, científicas y técnicas n.c.p.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id});
        """)
        
        # Insertar item
        cursor.execute(f"""
        INSERT INTO public.gCamItem
        (dCodInt, dDesProSer, dCantProSer, dPUniProSer, dDescItem, 
        iAfecIVA, dPropIVA, dTasaIVA, 
        dParAranc, dNCM, dDncpG, dDncpE, dGtin, dGtinPq, 
        fch_ins, fch_upd, de_id)
        VALUES (
            '1', 'CAMBIO DE DIVISAS - PRUEBA', '1', '500000', '0', 
            '1', '100', '10', 
            '', '', '', '', '', '', 
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id}
        );
        """)
        
        # Insertar forma de pago
        cursor.execute(f"""
        INSERT INTO public.gPaConEIni
        (iTiPago, dMonTiPag, cMoneTiPag, dTiCamTiPag, 
        dNumCheq, dBcoEmi, iDenTarj, iForProPa, 
        fch_ins, fch_upd, de_id)
        VALUES(
            '1', '0', 'PYG', '1', 
            '', '', '', '', 
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id}
        );
        """)
        
        # Actualizar a Confirmado
        cursor.execute(f"""
        UPDATE public.de
        SET estado = 'Confirmado'
        WHERE id = {de_id};
        """)
        
        connection.commit()
        
        print(f"✓ Factura {TIMBRADO_CONFIG['establecimiento']}-{TIMBRADO_CONFIG['punto_expedicion']}-{numero_factura} creada exitosamente!")
        print(f"  ID interno: {de_id}")
        print(f"\nAhora el SQL Proxy procesará la factura automáticamente.")
        print(f"\nPuedes ver el estado en:")
        print(f"  http://localhost:40080/kude/")
        print(f"  Usuario: sqlproxy")
        print(f"  Contraseña: kude1234")
        
        return True
    except Exception as e:
        print(f"✗ Error al crear factura: {e}")
        connection.rollback()
        return False

def main():
    print("="*70)
    print("PRUEBA DE FACTURACIÓN ELECTRÓNICA - EQUIPO 7")
    print("="*70)
    print()
    
    # Conectar
    connection, cursor = conectar()
    if not connection:
        print("\n⚠ Asegúrate de que el SQL Proxy esté levantado:")
        print("  cd /home/jose/proyecto_is2/sql-proxy01")
        print("  docker compose -f docker-compose.test.yml up -d")
        return
    
    try:
        # Verificar/Inicializar ESI
        print("\nVerificando configuración ESI...")
        if not verificar_esi(cursor):
            print("  No existe configuración ESI, inicializando...")
            if not inicializar_esi(connection, cursor):
                return
        else:
            print("  ✓ ESI ya está configurado")
        
        # Crear factura de prueba
        print("\nCreando factura de prueba...")
        crear_factura_prueba(connection, cursor)
        
        print("\n" + "="*70)
        print("✓ PRUEBA COMPLETADA")
        print("="*70)
        
    finally:
        cursor.close()
        connection.close()
        print("\nConexión cerrada")

if __name__ == "__main__":
    main()
