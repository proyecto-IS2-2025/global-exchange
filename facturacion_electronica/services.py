"""
Servicio para conectarse al SQL Proxy y generar facturas electrónicas
"""
import psycopg2
import os
from psycopg2.extras import RealDictCursor
from datetime import datetime
from .config import (
    SQL_PROXY_CONFIG, 
    EMISOR_CONFIG, 
    TIMBRADO_CONFIG, 
    FACTURACION_CONFIG,
    ACTIVIDADES_ECONOMICAS,
    ESI_CONFIG,
    KUDE_CONFIG
)


def convertir_a_url_publica(url_interna):
    """
    Convierte URLs internas (host.docker.internal) a URLs públicas (localhost)
    para que sean accesibles desde el navegador del usuario
    """
    if not url_interna:
        return url_interna
    
    # Obtener URL pública de variables de entorno o usar localhost por defecto
    url_publica_base = os.getenv('KUDE_PUBLIC_URL', 'http://localhost:40080/kude/')
    
    # Si la URL interna contiene host.docker.internal, reemplazar
    if 'host.docker.internal' in url_interna:
        # Extraer la parte después de /kude/
        if '/kude/' in url_interna:
            path_relativo = url_interna.split('/kude/', 1)[1]
            return f"{url_publica_base}{path_relativo}"
    
    return url_interna


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
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[SQL_PROXY] Intentando conectar con: host={SQL_PROXY_CONFIG['host']}, port={SQL_PROXY_CONFIG['port']}, db={SQL_PROXY_CONFIG['database']}, user={SQL_PROXY_CONFIG['user']}")
            
            self.connection = psycopg2.connect(
                host=SQL_PROXY_CONFIG['host'],
                port=SQL_PROXY_CONFIG['port'],
                database=SQL_PROXY_CONFIG['database'],
                user=SQL_PROXY_CONFIG['user'],
                password=SQL_PROXY_CONFIG['password']
            )
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            logger.info("✓ Conectado al SQL Proxy de Factura Segura")
            return True
        except (Exception, psycopg2.Error) as error:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"✗ Error al conectar al SQL Proxy: {error}")
            logger.error(f"✗ Configuración usada: {SQL_PROXY_CONFIG}")
            return False
    
    def buscar_pdf_en_kude(self, numero_factura, fecha_emision):
        """
        Busca el PDF de una factura en el servidor KuDE consultando el directorio HTTP
        
        Args:
            numero_factura: Número completo de factura (ej: "001-003-0000092")
            fecha_emision: datetime de emisión de la factura
            
        Returns:
            str: URL completa del PDF si se encuentra, None si no existe
        """
        try:
            import urllib.request
            import urllib.error
            import base64
            from html.parser import HTMLParser
            import logging
            
            logger = logging.getLogger(__name__)
            
            # Construir URL del directorio (formato YYYYMM)
            fecha_dir = fecha_emision.strftime('%Y%m')
            dir_url = f"{KUDE_CONFIG['url']}{fecha_dir}/"
            
            logger.info(f"[KUDE] Buscando PDF en: {dir_url}")
            
            # Preparar autenticación
            credentials = f"{KUDE_CONFIG['username']}:{KUDE_CONFIG['password']}"
            encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            
            # Parsear HTML para buscar el archivo
            class LinkParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.links = []
                
                def handle_starttag(self, tag, attrs):
                    if tag == 'a':
                        for attr, value in attrs:
                            if attr == 'href':
                                self.links.append(value)
            
            # Listar directorio
            req = urllib.request.Request(dir_url)
            req.add_header('Authorization', f'Basic {encoded}')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                content = response.read().decode('utf-8')
                parser = LinkParser()
                parser.feed(content)
                
                # Buscar archivo que contenga el número de factura
                pdfs = [link for link in parser.links 
                       if numero_factura in link and '.pdf' in link.lower()]
                
                if pdfs:
                    pdf_name = pdfs[0]  # Tomar el primero
                    pdf_url = f"{dir_url}{pdf_name}"
                    logger.info(f"[KUDE] ✅ PDF encontrado: {pdf_url}")
                    
                    # Convertir a URL pública para que sea accesible desde el navegador
                    pdf_url_publica = convertir_a_url_publica(pdf_url)
                    logger.info(f"[KUDE] URL pública: {pdf_url_publica}")
                    
                    return pdf_url_publica
                else:
                    logger.warning(f"[KUDE] ⚠️ PDF no encontrado para {numero_factura}")
                    return None
                    
        except urllib.error.HTTPError as e:
            logger.warning(f"[KUDE] HTTP Error {e.code}: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"[KUDE] Error buscando PDF: {e}")
            return None
    
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
    
    def obtener_ultimo_numero_desde_sql_proxy(self):
        """
        Consulta el SQL Proxy para obtener el último número de factura usado.
        Esto sincroniza con todas las facturas de todos los desarrolladores.
        
        Returns:
            int: Número de la última factura, o None si no hay facturas
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Consultar el último número de factura en el SQL Proxy
            query = """
            SELECT MAX(CAST(dnumdoc AS INTEGER)) as ultimo_numero 
            FROM public.de 
            WHERE dpunexp = %s AND dest = %s
            """
            
            self.cursor.execute(query, (
                TIMBRADO_CONFIG['punto_expedicion'],
                TIMBRADO_CONFIG['establecimiento']
            ))
            
            result = self.cursor.fetchone()
            
            if result and result['ultimo_numero']:
                logger.info(f"[SQL_PROXY] Último número de factura en SQL Proxy: {result['ultimo_numero']}")
                return int(result['ultimo_numero'])
            else:
                logger.info(f"[SQL_PROXY] No hay facturas previas en SQL Proxy")
                return None
                
        except (Exception, psycopg2.Error) as error:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[SQL_PROXY] Error al consultar último número: {error}")
            return None
    
    def buscar_pdf_en_kude(self, numero_factura, fecha_emision):
        """
        Busca el PDF de una factura en el servidor KuDE.
        
        Args:
            numero_factura: Número completo de la factura (ej: '001-003-0000087')
            fecha_emision: Fecha de emisión de la factura (datetime object)
            
        Returns:
            str: URL completa del PDF si se encuentra, None si no existe
        """
        try:
            import urllib.request
            import urllib.error
            import base64
            from html.parser import HTMLParser
            import logging
            
            logger = logging.getLogger(__name__)
            
            # Construir URL del directorio (formato YYYYMM)
            fecha_dir = fecha_emision.strftime('%Y%m')
            dir_url = f"{KUDE_CONFIG['url']}{fecha_dir}/"
            
            logger.info(f"[KUDE] Buscando PDF en: {dir_url}")
            
            # Preparar autenticación
            credentials = f"{KUDE_CONFIG['username']}:{KUDE_CONFIG['password']}"
            encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            
            # Parsear HTML para buscar el archivo
            class LinkParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.links = []
                
                def handle_starttag(self, tag, attrs):
                    if tag == 'a':
                        for attr, value in attrs:
                            if attr == 'href':
                                self.links.append(value)
            
            # Listar directorio
            req = urllib.request.Request(dir_url)
            req.add_header('Authorization', f'Basic {encoded}')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                content = response.read().decode('utf-8')
                parser = LinkParser()
                parser.feed(content)
                
                # Buscar archivo que contenga el número de factura
                numero_sin_guiones = numero_factura.replace('-', '-')  # Mantener formato
                pdfs = [link for link in parser.links 
                       if numero_factura in link and '.pdf' in link.lower()]
                
                if pdfs:
                    pdf_name = pdfs[0]  # Tomar el primero
                    pdf_url = f"{dir_url}{pdf_name}"
                    logger.info(f"[KUDE] ✅ PDF encontrado: {pdf_url}")
                    
                    # Convertir a URL pública para que sea accesible desde el navegador
                    pdf_url_publica = convertir_a_url_publica(pdf_url)
                    logger.info(f"[KUDE] URL pública: {pdf_url_publica}")
                    
                    return pdf_url_publica
                else:
                    logger.warning(f"[KUDE] ⚠️ PDF no encontrado para {numero_factura}")
                    return None
                    
        except urllib.error.HTTPError as e:
            logger.warning(f"[KUDE] HTTP Error {e.code}: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"[KUDE] Error buscando PDF: {e}")
            return None
    
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
        Obtiene el próximo número de factura disponible.
        
        DEPRECADO: Este método ahora delega a la función de utils.py
        que obtiene el número desde Django ORM y valida el rango asignado.
        
        Returns:
            str: Número de factura en formato "0000083"
        """
        from .utils import obtener_proximo_numero_factura as obtener_numero_django
        
        # Obtener el número completo desde Django (formato: 001-003-0000083)
        numero_completo = obtener_numero_django()
        
        # Extraer solo la parte numérica para compatibilidad
        partes = numero_completo.split('-')
        return partes[2]  # Retorna "0000083"
    
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
            (itide, dfeemide, dest, dpunexp, dnumdoc, cdc, dserienum, estado, 
            estado_sifen, desc_sifen, error_sifen, fch_sifen, 
            estado_can, desc_can, error_can, fch_can, 
            estado_inu, desc_inu, error_inu, fch_inu, 
            itipemi, dnumtim, dfeinit, itiptra, itimp, cmoneope, dticam, dinfofisc, 
            drucem, ddvemi, itipcont, dnomemi, ddiremi, dnumcas, 
            cdepemi, ddesdepemi, cciuemi, ddesciuemi, dtelemi, demaile, 
            inatrec, itiope, cpaisrec, iticontrec, drucrec, ddvrec, 
            itipidrec, ddtipidrec, dnumidrec, dnomrec, demailrec, 
            ddirrec, dnumcasrec, cdeprec, ddesdeprec, cciurec, ddesciurec, 
            inatven, itipidven, dnumidven, dnomven, ddirven, dnumcasven, 
            cdepven, ddesdepven, cciuven, ddesciuven, 
            ddirprov, cdepprov, ddesdepprov, cciuprov, ddesciuprov, 
            imotemi, iindpres, icondope, dplazocre, 
            dmodcont, dentcont, danocont, dseccont, dfecodcont, 
            dsisfact, dinfadic, 
            imoteminr, irespeminr, 
            itiptrans, imodtrans, irespflete, dinitras, dfintras, 
            ddirlocsal, dnumcassal, cdepsal, ddesdepsal, cciusal, ddesciusal, 
            ddirlocent, dnumcasent, cdepent, ddesdepent, cciuent, ddesciuent, 
            dtivehtras, dmarveh, dtipidenveh, dnroidveh, dnromatveh, 
            inattrans, dnomtrans, dructrans, ddvtrans, itipidtrans, dnumidtrans, 
            dnumidchof, dnomchof, 
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
                '1', '1', 'PRY', '2', 
                '{datos_factura.get('cliente_ruc', '80026216')}', 
                '{datos_factura.get('cliente_dv', '6')}', 
                '', '', '', 
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
            
            # OBLIGATORIO: Insertar forma de pago en gPaConEIni (sin esto la API da error)
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
            
            # Actualizar estado a "Confirmado" para que el scheduler lo procese
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
            WHERE dnumdoc = '{numero_factura}'
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
            (itide, dfeemide, dest, dpunexp, dnumdoc, cdc, dserienum, estado, 
            estado_sifen, desc_sifen, error_sifen, fch_sifen, 
            estado_can, desc_can, error_can, fch_can, 
            estado_inu, desc_inu, error_inu, fch_inu, 
            itipemi, dnumtim, dfeinit, itiptra, itimp, cmoneope, dticam, dinfofisc, 
            drucem, ddvemi, itipcont, dnomemi, ddiremi, dnumcas, 
            cdepemi, ddesdepemi, cciuemi, ddesciuemi, dtelemi, demaile, 
            inatrec, itiope, cpaisrec, iticontrec, drucrec, ddvrec, 
            itipidrec, ddtipidrec, dnumidrec, dnomrec, demailrec, 
            ddirrec, dnumcasrec, cdeprec, ddesdeprec, cciurec, ddesciurec, 
            inatven, itipidven, dnumidven, dnomven, ddirven, dnumcasven, 
            cdepven, ddesdepven, cciuven, ddesciuven, 
            ddirprov, cdepprov, ddesdepprov, cciuprov, ddesciuprov, 
            imotemi, iindpres, icondope, dplazocre, 
            dmodcont, dentcont, danocont, dseccont, dfecodcont, 
            dsisfact, dinfadic, 
            imoteminr, irespeminr, 
            itiptrans, imodtrans, irespflete, dinitras, dfintras, 
            ddirlocsal, dnumcassal, cdepsal, ddesdepsal, cciusal, ddesciusal, 
            ddirlocent, dnumcasent, cdepent, ddesdepent, cciuent, ddesciuent, 
            dtivehtras, dmarveh, dtipidenveh, dnroidveh, dnromatveh, 
            inattrans, dnomtrans, dructrans, ddvtrans, itipidtrans, dnumidtrans, 
            dnumidchof, dnomchof, 
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


# =================================================================
# FUNCIONES HELPER PARA INTEGRACIÓN CON TRANSACCIONES
# =================================================================

def generar_factura_automatica(transaccion):
    """
    Genera automáticamente una factura electrónica para una transacción.
    
    Soporta tanto COMPRA como VENTA de divisas:
    - COMPRA: Cliente paga PYG → recibe divisa extranjera
             Factura por monto_origen (guaraníes pagados), cantidad=1
    - VENTA: Cliente entrega divisa extranjera → recibe PYG
             Factura por monto_destino, cantidad=divisas vendidas
    
    Args:
        transaccion: Objeto Transaccion (modelo Django)
    
    Returns:
        tuple: (success: bool, factura: FacturaElectronica o None, error_msg: str o None)
    """
    import logging
    from .models import FacturaElectronica
    
    logger = logging.getLogger(__name__)
    
    tipo_op = transaccion.tipo_operacion  # 'compra' o 'venta'
    
    logger.info(f"[FACTURA_AUTO] ═══ INICIO generar_factura_automatica para {transaccion.numero_transaccion} ═══")
    logger.info(f"[FACTURA_AUTO] Tipo operación: {tipo_op.upper()}")
    logger.info(f"[FACTURA_AUTO] Cliente: {transaccion.cliente.nombre_completo}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # DETERMINAR MONTO, DIVISA Y CANTIDAD SEGÚN TIPO DE OPERACIÓN
    # ═══════════════════════════════════════════════════════════════════════
    items = []  # Lista de items para la factura
    
    if tipo_op == 'compra':
        # COMPRA: Cliente paga PYG (monto_origen) → recibe divisa (monto_destino)
        # Una sola fila: cantidad=1, precio=monto_total
        monto_pyg = float(transaccion.monto_origen)
        divisa_operacion = transaccion.divisa_destino
        cantidad_divisas = int(float(transaccion.monto_destino))  # Cantidad de divisas que recibe
        
        items.append({
            'descripcion': f"Compra de {cantidad_divisas} {divisa_operacion.code}",
            'cantidad': 1,
            'precio_unitario': monto_pyg,
            'descuento': 0,
            'afectacion_iva': '3',
            'proporcion_iva': '0',
            'tasa_iva': '0'
        })
        
        logger.info(f"[FACTURA_AUTO] COMPRA: {monto_pyg} PYG por {cantidad_divisas} {divisa_operacion.code}")
    else:
        # VENTA: Cliente entrega divisa → recibe PYG
        # UNA SOLA FILA:
        #   - Precio Unitario = total a recibir (196716)
        #   - Cantidad = 1
        #   - Descuento = 0
        #   - Exentas = total a recibir (196716)
        #   - Descripción incluye cantidad vendida y comisión
        
        divisa_operacion = transaccion.divisa_origen
        cantidad_divisas = int(float(transaccion.monto_origen))  # 30 USD
        monto_base = int(float(transaccion.monto_destino))  # 202800
        comision = int(float(transaccion.comision_aplicada)) if transaccion.comision_aplicada else 0  # 6084
        monto_neto = monto_base - comision  # 196716
        
        # Descripción con detalle de la operación
        if comision > 0:
            descripcion = f"Venta de {cantidad_divisas} {divisa_operacion.code} (Comisión medio de pago: {comision} Gs.)"
        else:
            descripcion = f"Venta de {cantidad_divisas} {divisa_operacion.code}"
        
        items.append({
            'descripcion': descripcion,
            'cantidad': 1,
            'precio_unitario': monto_neto,  # 196716 (total a recibir)
            'descuento': 0,
            'afectacion_iva': '3',
            'proporcion_iva': '0',
            'tasa_iva': '0'
        })
        
        monto_pyg = monto_neto  # Total final: 196716
        
        logger.info(f"[FACTURA_AUTO] VENTA: {cantidad_divisas} {divisa_operacion.code}")
        logger.info(f"[FACTURA_AUTO]   Descripción: {descripcion}")
        logger.info(f"[FACTURA_AUTO]   Precio Unitario: {monto_neto} PYG")
        logger.info(f"[FACTURA_AUTO]   Descuento: 0")
        logger.info(f"[FACTURA_AUTO]   Total (Exentas): {monto_neto} PYG")
    
    logger.info(f"[FACTURA_AUTO] Items preparados: {len(items)} item(s), Total: {monto_pyg} PYG")
    
    try:
        # Verificar si ya tiene factura
        if hasattr(transaccion, 'factura_electronica'):
            logger.warning(f"[FACTURA_AUTO] ⚠️ Transacción ya tiene factura: {transaccion.factura_electronica.numero_factura}")
            return True, transaccion.factura_electronica, None
        
        logger.info(f"[FACTURA_AUTO] Conectando a SQL Proxy...")
        
        # Conectar al SQL Proxy
        service = SQLProxyService()
        if not service.conectar():
            error_msg = "No se pudo conectar al servidor de facturación (SQL Proxy)"
            logger.error(f"[FACTURA_AUTO] ❌ {error_msg}")
            return False, None, error_msg
        
        logger.info(f"[FACTURA_AUTO] ✅ Conectado a SQL Proxy")
        
        try:
            # Preparar datos del cliente
            cliente = transaccion.cliente
            logger.info(f"[FACTURA_AUTO] Preparando datos del cliente...")
            
            # TEMPORAL: Usar siempre el RUC del profesor para ambiente de prueba
            # En producción, validar que el RUC del cliente exista en SIFEN
            # Por ahora, SIFEN solo tiene registrado el RUC 80026216 en su base de datos de prueba
            cliente_ruc = '80026216'  # RUC del profesor (único válido en SIFEN TEST)
            cliente_dv = '6'
            
            # TODO EN PRODUCCIÓN: Descomentar esto y validar RUCs reales
            # if hasattr(cliente, 'ruc') and cliente.ruc:
            #     cliente_ruc = str(cliente.ruc)
            #     cliente_dv = str(getattr(cliente, 'dv', '0'))
            # elif hasattr(cliente, 'cedula') and cliente.cedula:
            #     cliente_ruc = str(cliente.cedula)
            #     cliente_dv = '0'
            
            # ═══════════════════════════════════════════════════════════════════
            # ITEMS YA PREPARADOS ARRIBA
            # ═══════════════════════════════════════════════════════════════════
            # Los items ya fueron construidos en la sección anterior según el tipo de operación
            # COMPRA: 1 item
            # VENTA: 2 items (venta de divisas + comisión)
            
            for i, item in enumerate(items):
                logger.info(f"[FACTURA_AUTO] Item {i+1}: {item['descripcion']}")
                logger.info(f"[FACTURA_AUTO]   Cantidad: {item['cantidad']}, Precio: {item['precio_unitario']}, Descuento: {item['descuento']}")
            
            # Datos para el SQL Proxy
            datos_factura = {
                'cliente_ruc': str(cliente_ruc),
                'cliente_dv': str(cliente_dv),
                'cliente_nombre': cliente.nombre_completo,
                'cliente_email': cliente.email or 'sin_email@globalexchange.com',
                'items': items
            }
            
            logger.info(f"[FACTURA_AUTO] Datos factura preparados: RUC={cliente_ruc}, Cliente={cliente.nombre_completo}")
            logger.info(f"[FACTURA_AUTO] Llamando a service.crear_factura()...")
            
            # Crear factura en SQL Proxy
            resultado = service.crear_factura(datos_factura)
            
            logger.info(f"[FACTURA_AUTO] ✅ Factura creada en SQL Proxy: {resultado}")
            
            # Generar URLs correctas del PDF/XML (formato: YYYYMM/est-pto-numero_YYYYMMDD_HHMMSS_random.pdf)
            # Nota: El nombre exacto del archivo se genera en SIFEN con timestamp, 
            # pero podemos construir la URL base correctamente
            fecha_actual = datetime.now()
            directorio_fecha = fecha_actual.strftime("%Y%m")  # 202510
            
            # Crear registro en Django
            numero_completo = f"{TIMBRADO_CONFIG['establecimiento']}-{TIMBRADO_CONFIG['punto_expedicion']}-{resultado['numero_factura']}"
            
            logger.info(f"[FACTURA_AUTO] Número completo: {numero_completo}")
            logger.info(f"[FACTURA_AUTO] Creando registro en Django...")
            
            # URL base - el archivo real se generará con timestamp cuando SIFEN apruebe
            # Ejemplo: http://localhost:40080/kude/202510/001-003-0000066_20251030_213134_944599.pdf
            url_kude_base = f"{SQL_PROXY_CONFIG['kude_url']}/{directorio_fecha}"
            
            factura = FacturaElectronica.objects.create(
                transaccion=transaccion,
                numero_factura=numero_completo,
                establecimiento=TIMBRADO_CONFIG['establecimiento'],
                punto_expedicion=TIMBRADO_CONFIG['punto_expedicion'],
                numero_documento=resultado['numero_factura'],
                de_id=resultado['de_id'],
                estado='confirmado',
                estado_sifen='Procesando',
                descripcion_sifen='Factura enviada al SIFEN para procesamiento. Esperando aprobación (puede tomar 30-60 segundos).',
                # Guardar URL base - se actualizará cuando tengamos el CDC
                url_kude_pdf=url_kude_base,  # Se actualizará con nombre completo después
                url_kude_xml=url_kude_base,
                datos_factura=datos_factura
            )
            
            logger.info(f"[FACTURA_AUTO] ✅ Registro Django creado: ID={factura.id}")
            logger.info(f"✅ Factura {numero_completo} generada automáticamente para transacción {transaccion.numero_transaccion}")
            logger.info(f"[FACTURA_AUTO] ═══ FIN exitoso ═══")
            return True, factura, None
            
        finally:
            service.desconectar()
            logger.info(f"[FACTURA_AUTO] SQL Proxy desconectado")
    
    except Exception as e:
        logger.error(f"[FACTURA_AUTO] ❌ ERROR CRÍTICO: {str(e)}", exc_info=True)
        error_msg = f"Error al generar factura: {str(e)}"
        logger.error(f"Error en generar_factura_automatica para {transaccion.numero_transaccion}: {e}", exc_info=True)
        return False, None, error_msg


def actualizar_estado_factura(factura_id):
    """
    Actualiza el estado de una factura consultando al SQL Proxy.
    Debe llamarse periódicamente o después de generar una factura.
    
    Args:
        factura_id: ID de la FacturaElectronica en Django
    
    Returns:
        bool: True si se actualizó correctamente
    """
    import logging
    import os
    import glob
    from .models import FacturaElectronica
    from .config import SQL_PROXY_CONFIG
    
    logger = logging.getLogger(__name__)
    
    try:
        factura = FacturaElectronica.objects.get(id=factura_id)
        
        # Conectar al SQL Proxy
        service = SQLProxyService()
        if not service.conectar():
            logger.error(f"No se pudo conectar al SQL Proxy para actualizar factura {factura.numero_factura}")
            return False
        
        try:
            # Consultar estado en SQL Proxy
            estado_sql = service.consultar_estado_factura(factura.numero_documento)
            
            if not estado_sql:
                logger.warning(f"No se encontró la factura {factura.numero_documento} en SQL Proxy")
                return False
            
            # Actualizar estado en Django
            factura.estado_sifen = estado_sql.get('estado_sifen', '')
            factura.descripcion_sifen = estado_sql.get('desc_sifen', '')
            factura.error_sifen = estado_sql.get('error_sifen', '')
            
            # Si tiene CDC, actualizar
            if estado_sql.get('cdc') and estado_sql['cdc'] != '0':
                factura.cdc = estado_sql['cdc']
            
            # Actualizar estado Django según SIFEN
            estado_sifen_lower = factura.estado_sifen.lower()
            if 'aprobado' in estado_sifen_lower:
                factura.estado = 'aprobado'
                if not factura.fecha_aprobacion:
                    factura.fecha_aprobacion = datetime.now()
                    
                # Buscar el archivo PDF real generado por SIFEN
                # Formato: /kude/202510/001-003-0000066_20251030_213134_944599.pdf
                fecha_actual = datetime.now()
                directorio_fecha = fecha_actual.strftime("%Y%m")
                numero_completo = f"{factura.establecimiento}-{factura.punto_expedicion}-{factura.numero_documento}"
                
                # Buscar en el directorio de volúmenes del SQL Proxy
                # Nota: En producción esto puede variar según configuración
                kude_path = f"/home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/{directorio_fecha}"
                patron_busqueda = f"{kude_path}/{numero_completo}_*.pdf"
                
                archivos_pdf = glob.glob(patron_busqueda)
                if archivos_pdf:
                    # Tomar el primer archivo encontrado (debería ser único)
                    nombre_archivo = os.path.basename(archivos_pdf[0])
                    nombre_xml = nombre_archivo.replace('.pdf', '.xml')
                    
                    # Actualizar URLs con nombres completos
                    factura.url_kude_pdf = f"{SQL_PROXY_CONFIG['kude_url']}/{directorio_fecha}/{nombre_archivo}"
                    factura.url_kude_xml = f"{SQL_PROXY_CONFIG['kude_url']}/{directorio_fecha}/{nombre_xml}"
                    
                    logger.info(f"✅ URLs actualizadas para factura {factura.numero_factura}: {nombre_archivo}")
                else:
                    logger.warning(f"⚠️ PDF no encontrado en {patron_busqueda}")
                    
            elif 'rechazado' in estado_sifen_lower or 'error' in estado_sifen_lower:
                factura.estado = 'rechazado'
            
            factura.save()
            logger.info(f"✅ Estado de factura {factura.numero_factura} actualizado: {factura.estado_sifen}")
            return True
            
        finally:
            service.desconectar()
    
    except FacturaElectronica.DoesNotExist:
        logger.error(f"Factura con ID {factura_id} no existe")
        return False
    except Exception as e:
        logger.error(f"Error al actualizar estado de factura: {e}", exc_info=True)
        return False
