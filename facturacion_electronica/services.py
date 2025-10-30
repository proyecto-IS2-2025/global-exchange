"""
Servicio para conectarse al SQL Proxy y generar facturas electrónicas
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from .config import (
    SQL_PROXY_CONFIG, 
    EMISOR_CONFIG, 
    TIMBRADO_CONFIG, 
    FACTURACION_CONFIG,
    ACTIVIDADES_ECONOMICAS,
    ESI_CONFIG
)


class SQLProxyService:
    """
    Servicio para interactuar con el SQL Proxy de Factura Segura
    """
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def conectar(self):
        """Establece conexión con la base de datos del SQL Proxy"""
        try:
            self.connection = psycopg2.connect(
                host=SQL_PROXY_CONFIG['host'],
                port=SQL_PROXY_CONFIG['port'],
                database=SQL_PROXY_CONFIG['database'],
                user=SQL_PROXY_CONFIG['user'],
                password=SQL_PROXY_CONFIG['password']
            )
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            print("✓ Conectado al SQL Proxy de Factura Segura")
            return True
        except (Exception, psycopg2.Error) as error:
            print(f"✗ Error al conectar al SQL Proxy: {error}")
            return False
    
    def desconectar(self):
        """Cierra la conexión con la base de datos"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("✓ Conexión al SQL Proxy cerrada")
    
    def verificar_esi_existe(self):
        """Verifica si existe configuración ESI en la base de datos"""
        try:
            self.cursor.execute("SELECT COUNT(*) as count FROM public.esi;")
            result = self.cursor.fetchone()
            return result['count'] > 0
        except (Exception, psycopg2.Error) as error:
            print(f"✗ Error al verificar ESI: {error}")
            return False
    
    def inicializar_esi(self):
        """
        Inicializa la tabla ESI con los datos del equipo
        Solo se debe ejecutar una vez al configurar el sistema
        """
        if self.verificar_esi_existe():
            print("⚠ Ya existe configuración ESI. No se inicializará de nuevo.")
            return False
        
        try:
            url = ESI_CONFIG['url_test'] if ESI_CONFIG['ambiente'] == 'TEST' else ESI_CONFIG['url_prod']
            
            insert_query = f"""
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
                '{ESI_CONFIG['token']}', 
                '{url}'
            );
            """
            self.cursor.execute(insert_query)
            self.connection.commit()
            print("✓ Configuración ESI inicializada correctamente")
            return True
        except (Exception, psycopg2.Error) as error:
            print(f"✗ Error al inicializar ESI: {error}")
            self.connection.rollback()
            return False
    
    def obtener_proximo_numero_factura(self):
        """
        Obtiene el próximo número de factura disponible
        dentro del rango asignado (51-100)
        """
        try:
            # Buscar el último número usado en la base de datos
            self.cursor.execute(f"""
                SELECT MAX(CAST(dNumDoc AS INTEGER)) as max_num
                FROM public.de
                WHERE dEst = '{TIMBRADO_CONFIG['establecimiento']}'
                AND dPunExp = '{TIMBRADO_CONFIG['punto_expedicion']}'
                AND CAST(dNumDoc AS INTEGER) >= {FACTURACION_CONFIG['numero_inicial']}
                AND CAST(dNumDoc AS INTEGER) <= {FACTURACION_CONFIG['numero_final']}
            """)
            result = self.cursor.fetchone()
            
            if result and result['max_num']:
                proximo = result['max_num'] + 1
            else:
                proximo = FACTURACION_CONFIG['numero_inicial']
            
            # Verificar que no exceda el rango
            if proximo > FACTURACION_CONFIG['numero_final']:
                raise Exception(f"Se ha alcanzado el límite de facturas. Rango disponible: {FACTURACION_CONFIG['numero_inicial']}-{FACTURACION_CONFIG['numero_final']}")
            
            # Formatear con ceros a la izquierda (7 dígitos)
            return str(proximo).zfill(7)
        
        except (Exception, psycopg2.Error) as error:
            print(f"✗ Error al obtener próximo número de factura: {error}")
            raise
    
    def crear_factura(self, datos_factura):
        """
        Crea una factura electrónica en el SQL Proxy
        
        Args:
            datos_factura: dict con los siguientes campos:
                - cliente_ruc: RUC del cliente
                - cliente_dv: DV del cliente
                - cliente_nombre: Nombre del cliente
                - cliente_email: Email del cliente
                - items: lista de items con {descripcion, cantidad, precio_unitario, iva_tasa}
        
        Returns:
            dict con {numero_factura, de_id, estado}
        """
        try:
            # Obtener próximo número de factura
            numero_factura = self.obtener_proximo_numero_factura()
            fecha_emision = datetime.now().strftime("%Y-%m-%d")
            
            # Insertar el documento electrónico
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
                '1', '{fecha_emision}', '{TIMBRADO_CONFIG['establecimiento']}', 
                '{TIMBRADO_CONFIG['punto_expedicion']}', '{numero_factura}', 
                '0', '', 'Borrador', 
                '', '', '', '', '', '', '', '', '', '', '', '', 
                '1', '{TIMBRADO_CONFIG['numero']}', '{TIMBRADO_CONFIG['fecha_inicio']}', 
                '2', '5', 'PYG', '1', '', 
                '{EMISOR_CONFIG['ruc']}', '{EMISOR_CONFIG['dv']}', 
                '{EMISOR_CONFIG['tipo_contribuyente']}', '{EMISOR_CONFIG['nombre']}', 
                '{EMISOR_CONFIG['direccion']}', '{EMISOR_CONFIG['numero_casa']}', 
                '{EMISOR_CONFIG['departamento']}', '{EMISOR_CONFIG['departamento_desc']}', 
                '{EMISOR_CONFIG['ciudad']}', '{EMISOR_CONFIG['ciudad_desc']}', 
                '{EMISOR_CONFIG['telefono']}', '{EMISOR_CONFIG['email']}', 
                '1', '1', 'PRY', '1', 
                '{datos_factura.get('cliente_ruc', '0')}', 
                '{datos_factura.get('cliente_dv', '0')}', 
                '0', '', '0', 
                '{datos_factura.get('cliente_nombre', 'CLIENTE GENERICO')}', 
                '{datos_factura.get('cliente_email', 'cliente@example.com')}', 
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
            
            self.cursor.execute(insert_de_query)
            de_id = self.cursor.fetchone()['id']
            
            # Insertar actividades económicas
            for actividad in ACTIVIDADES_ECONOMICAS:
                insert_acteco_query = f"""
                INSERT INTO public.gActEco
                (cActEco, dDesActEco, fch_ins, fch_upd, de_id)
                VALUES (
                    '{actividad['codigo']}', 
                    '{actividad['descripcion']}', 
                    CURRENT_TIMESTAMP, 
                    CURRENT_TIMESTAMP, 
                    {de_id}
                );
                """
                self.cursor.execute(insert_acteco_query)
            
            # Insertar items de la factura
            for item in datos_factura.get('items', []):
                insert_item_query = f"""
                INSERT INTO public.gCamItem
                (dCodInt, dDesProSer, dCantProSer, dPUniProSer, dDescItem, 
                iAfecIVA, dPropIVA, dTasaIVA, 
                dParAranc, dNCM, dDncpG, dDncpE, dGtin, dGtinPq, 
                fch_ins, fch_upd, de_id)
                VALUES (
                    '1', 
                    '{item.get('descripcion', 'SERVICIO')}', 
                    '{item.get('cantidad', 1)}', 
                    '{item.get('precio_unitario', 0)}', 
                    '{item.get('descuento', 0)}', 
                    '{item.get('afectacion_iva', '1')}', 
                    '{item.get('proporcion_iva', '100')}', 
                    '{item.get('tasa_iva', '10')}', 
                    '', '', '', '', '', '', 
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id}
                );
                """
                self.cursor.execute(insert_item_query)
            
            # Insertar forma de pago (contado por defecto)
            insert_pago_query = f"""
            INSERT INTO public.gPaConEIni
            (iTiPago, dMonTiPag, cMoneTiPag, dTiCamTiPag, 
            dNumCheq, dBcoEmi, iDenTarj, iForProPa, 
            fch_ins, fch_upd, de_id)
            VALUES(
                '1', '0', 'PYG', '1', 
                '', '', '', '', 
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id}
            );
            """
            self.cursor.execute(insert_pago_query)
            
            # Actualizar estado a "Confirmado" para que el SQL Proxy lo envíe
            update_query = f"""
            UPDATE public.de
            SET estado = 'Confirmado'
            WHERE id = {de_id};
            """
            self.cursor.execute(update_query)
            
            self.connection.commit()
            
            print(f"✓ Factura {numero_factura} creada exitosamente (ID: {de_id})")
            
            return {
                'numero_factura': numero_factura,
                'de_id': de_id,
                'estado': 'Confirmado',
                'mensaje': f'Factura {TIMBRADO_CONFIG["establecimiento"]}-{TIMBRADO_CONFIG["punto_expedicion"]}-{numero_factura} generada correctamente'
            }
        
        except (Exception, psycopg2.Error) as error:
            print(f"✗ Error al crear factura: {error}")
            self.connection.rollback()
            raise
    
    def consultar_estado_factura(self, numero_factura):
        """
        Consulta el estado de una factura en el SIFEN
        
        Args:
            numero_factura: Número de factura (formato 0000051)
        
        Returns:
            dict con el estado de la factura
        """
        try:
            query = f"""
            SELECT id, dnumdoc, estado, estado_sifen, desc_sifen, 
                   error_sifen, fch_sifen, cdc
            FROM public.de
            WHERE dNumDoc = '{numero_factura}'
            ORDER BY id DESC
            LIMIT 1;
            """
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            
            if result:
                return dict(result)
            else:
                return None
        
        except (Exception, psycopg2.Error) as error:
            print(f"✗ Error al consultar estado de factura: {error}")
            return None
    
    def cancelar_factura(self, cdc):
        """
        Solicita la cancelación de una factura ya emitida
        
        Args:
            cdc: Código de Control del documento
        """
        try:
            update_query = f"""
            UPDATE public.de
            SET estado = 'Cancelar'
            WHERE cdc = '{cdc}';
            """
            self.cursor.execute(update_query)
            self.connection.commit()
            print(f"✓ Solicitud de cancelación enviada para CDC: {cdc}")
            return True
        except (Exception, psycopg2.Error) as error:
            print(f"✗ Error al cancelar factura: {error}")
            self.connection.rollback()
            return False
    
    def inutilizar_numero(self, numero_factura):
        """
        Inutiliza un número de factura (para números que no se usarán)
        
        Args:
            numero_factura: Número de factura a inutilizar (formato 0000051)
        """
        try:
            insert_query = f"""
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
                '1', '', '{TIMBRADO_CONFIG['establecimiento']}', 
                '{TIMBRADO_CONFIG['punto_expedicion']}', '{numero_factura}', 
                '0', '', 'Inutilizar', 
                '', '', '', '', '', '', '', '', '', '', '', '', 
                '', '{TIMBRADO_CONFIG['numero']}', '', '', '', '', '', '', 
                '{EMISOR_CONFIG['ruc']}', '', '', '', '', '', 
                '', '', '', '', '', '', 
                '', '', '', '', '', '', '', '', '', '', '', 
                '', '', '', '', '', '', 
                '', '', '', '', '', '', '', '', '', '', 
                '', '', '', '', '', 
                '', '', '', '', 
                '', '', '', '', '', 
                '', '', 
                '', '', 
                '', '', '', '', '', 
                '', '', '', '', '', '', 
                '', '', '', '', '', '', 
                '', '', '', '', '', 
                '', '', '', '', '', '', 
                '', '', 
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            );
            """
            self.cursor.execute(insert_query)
            self.connection.commit()
            print(f"✓ Número {numero_factura} inutilizado correctamente")
            return True
        except (Exception, psycopg2.Error) as error:
            print(f"✗ Error al inutilizar número: {error}")
            self.connection.rollback()
            return False
