#!/usr/bin/env python3
"""
Script para insertar una factura directamente en SQL Proxy con los datos correctos del profesor.
Esto evita problemas con Django y genera la factura inmediatamente.
"""
import psycopg2
from datetime import datetime

# Configuración de conexión (desde docker-compose)
DB_CONFIG = {
    'user': 'fs_proxy_user',
    'password': 'p123456',
    'host': 'localhost',
    'port': '45432',
    'database': 'fs_proxy_bd'
}

# Datos de la factura (copiados del XML del profesor)
NUMERO_FACTURA = '0000066'  # Siguiente número disponible (dentro del rango 51-100)
PUNTO_EXPEDICION = '003'  # PUNTO ASIGNADO AL EQUIPO 7
FECHA_EMISION = datetime.now().strftime("%Y-%m-%d")

print("=" * 80)
print("INSERTANDO FACTURA CON DATOS CORRECTOS DEL PROFESOR")
print("=" * 80)

try:
    # Conectar a la base de datos
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    print("\n✅ Conectado a PostgreSQL")
    
    # Insertar factura
    insert_de_query = f"""
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
        '1', '{FECHA_EMISION}', '001', '{PUNTO_EXPEDICION}', '{NUMERO_FACTURA}', 
        '0', '', 'Confirmado', 
        '', '', '', '', '', '', '', '', '', '', '', '', 
        '1', '02595733', '2025-03-27', '2', '5', 'PYG', '1', '', 
        '2595733', '3', '1', 
        'DE generado en ambiente de prueba - sin valor comercial ni fiscal', 
        'YVAPOVO C/ TOBATI', '1543', 
        '1', 'CAPITAL', '1', 'ASUNCION (DISTRITO)', 
        '(0961)988439', 'glex.globalexchange@gmail.com', 
        '1', '1', 'PRY', '2', '80026216', '6', 
        '', '', '', 'GUILLERMO GONZALEZ', 'soporte@facturasegura.com.py', 
        '', '', '', '', '', '', 
        '', '', '', '', '', '', '', '', '', '', 
        '', '', '', '', '', 
        '', '1', '1', '', 
        '', '', '', '', '', 
        '1', 'Operación de cambio de divisas - Global Exchange', 
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
    
    cursor.execute(insert_de_query)
    de_id = cursor.fetchone()[0]
    print(f"✅ Factura insertada con ID: {de_id}")
    
    # Insertar actividades económicas
    actividades = [
        ('62010', 'Actividades de programación informática'),
        ('74909', 'Otras actividades profesionales, científicas y técnicas n.c.p.')
    ]
    
    for codigo, descripcion in actividades:
        insert_acteco_query = f"""
        INSERT INTO public.gActEco
        (cActEco, dDesActEco, fch_ins, fch_upd, de_id)
        VALUES ('{codigo}', '{descripcion}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id});
        """
        cursor.execute(insert_acteco_query)
    
    print(f"✅ Actividades económicas insertadas (2)")
    
    # Insertar item
    insert_item_query = f"""
    INSERT INTO public.gCamItem
    (dCodInt, dDesProSer, dCantProSer, dPUniProSer, dDescItem, 
    iAfecIVA, dPropIVA, dTasaIVA, 
    dParAranc, dNCM, dDncpG, dDncpE, dGtin, dGtinPq, 
    fch_ins, fch_upd, de_id)
    VALUES (
        '1', 
        'Compra de USD 20.00 a tasa 7500 PYG - Operacion de cambio', 
        '1', 
        '150000', 
        '0', 
        '1', 
        '100', 
        '10', 
        '', '', '', '', '', '', 
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id}
    );
    """
    cursor.execute(insert_item_query)
    print(f"✅ Item insertado")
    
    # Insertar pago (OBLIGATORIO para que funcione)
    insert_pago_query = f"""
    INSERT INTO public.gPaConEIni
    (iTiPago, dMonTiPag, cMoneTiPag, dTiCamTiPag, 
    dNumCheq, dBcoEmi, iDenTarj, iForProPa,
    fch_ins, fch_upd, de_id)
    VALUES (
        '1',  -- Efectivo
        '0',  -- Monto (0 porque es contado)
        'PYG',
        '1',
        '', '', '', '',
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id}
    );
    """
    cursor.execute(insert_pago_query)
    print(f"✅ Pago insertado")
    
    # Commit
    connection.commit()
    
    print("\n" + "=" * 80)
    print("🎉 FACTURA GENERADA EXITOSAMENTE")
    print("=" * 80)
    print(f"\n📋 DETALLES:")
    print(f"   • Número: {NUMERO_FACTURA}")
    print(f"   • Establecimiento: 001")
    print(f"   • Punto: 003")
    print(f"   • Estado: Confirmado")
    print(f"   • Fecha: {FECHA_EMISION}")
    print(f"\n👤 CLIENTE (igual al XML del profesor):")
    print(f"   • RUC: 80026216-6")
    print(f"   • Tipo contribuyente: 2 (Persona física)")
    print(f"   • Nombre: GUILLERMO GONZALEZ")
    print(f"   • Email: soporte@facturasegura.com.py")
    print(f"\n⏳ PRÓXIMOS PASOS:")
    print(f"   1. El scheduler procesará en ~20 segundos")
    print(f"   2. Enviará a SIFEN para aprobación")
    print(f"   3. Verifica el estado cada 30 segundos con:")
    print(f"      docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \"SELECT dnumdoc, estado, estado_sifen, desc_sifen FROM public.de WHERE dnumdoc = '{NUMERO_FACTURA}';\"")
    print(f"\n🎯 RESULTADO ESPERADO:")
    print(f"   • Estado: 'Aprobado' o 'Sol.Aprobacion'")
    print(f"   • NO debe aparecer: 'Rechazado' ni 'ERROR_SIFEN'")
    print(f"   • PDF disponible en: http://localhost:40080/kude/{NUMERO_FACTURA}.pdf")
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    if connection:
        cursor.close()
        connection.close()
        print("\n✅ Conexión cerrada")
