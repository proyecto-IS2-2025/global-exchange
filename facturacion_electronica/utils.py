"""
Utilidades para generar facturas electrónicas desde transacciones
"""
from decimal import Decimal
from .services import SQLProxyService
from .models import FacturaElectronica
from .config import TIMBRADO_CONFIG, KUDE_CONFIG
from django.utils import timezone
import glob
import os
import logging

logger = logging.getLogger(__name__)


def generar_factura_desde_transaccion(transaccion):
    """
    Genera una factura electrónica a partir de una transacción
    
    Args:
        transaccion: Instancia del modelo Transaccion
    
    Returns:
        FacturaElectronica: La factura generada
    
    Raises:
        Exception: Si hay algún error al generar la factura
    """
    
    # Verificar que la transacción esté completada o pagada
    if transaccion.estado not in ['completado', 'pagada']:
        raise Exception(f"La transacción debe estar completada o pagada. Estado actual: {transaccion.estado}")
    
    # Verificar que no tenga ya una factura
    if hasattr(transaccion, 'factura_electronica'):
        raise Exception(f"La transacción ya tiene una factura electrónica: {transaccion.factura_electronica.numero_factura}")
    
    # Preparar datos del cliente
    cliente_ruc = getattr(transaccion.cliente, 'ruc', '0')
    cliente_dv = getattr(transaccion.cliente, 'ruc_dv', '0')
    cliente_nombre = transaccion.cliente.nombre_completo
    cliente_email = getattr(transaccion.cliente, 'email', 'cliente@example.com')
    
    # Preparar descripción del servicio
    if transaccion.tipo_operacion == 'compra':
        descripcion = f"COMPRA DE {transaccion.divisa_destino.code} - VENTA DE {transaccion.divisa_origen.code}"
    else:  # venta
        descripcion = f"VENTA DE {transaccion.divisa_origen.code} - COMPRA DE {transaccion.divisa_destino.code}"
    
    # Calcular monto para la factura
    # En Paraguay, las facturas deben estar en Guaraníes (PYG)
    monto_pyg = calcular_monto_pyg(transaccion)
    
    # Preparar items de la factura
    items = [
        {
            'descripcion': descripcion,
            'cantidad': '1',
            'precio_unitario': str(int(monto_pyg)),  # Convertir a entero para PYG
            'descuento': '0',
            'afectacion_iva': '1',  # Gravado IVA 10%
            'proporcion_iva': '100',
            'tasa_iva': '10'
        }
    ]
    
    # Preparar datos completos para la factura
    datos_factura = {
        'cliente_ruc': str(cliente_ruc),
        'cliente_dv': str(cliente_dv),
        'cliente_nombre': cliente_nombre,
        'cliente_email': cliente_email,
        'items': items
    }
    
    # Conectar al SQL Proxy y generar la factura
    servicio = SQLProxyService()
    
    try:
        if not servicio.conectar():
            raise Exception("No se pudo conectar al SQL Proxy")
        
        # Crear la factura en el SQL Proxy
        resultado = servicio.crear_factura(datos_factura)
        
        # Crear el registro en Django
        factura = FacturaElectronica.objects.create(
            transaccion=transaccion,
            numero_factura=f"{TIMBRADO_CONFIG['establecimiento']}-{TIMBRADO_CONFIG['punto_expedicion']}-{resultado['numero_factura']}",
            establecimiento=TIMBRADO_CONFIG['establecimiento'],
            punto_expedicion=TIMBRADO_CONFIG['punto_expedicion'],
            numero_documento=resultado['numero_factura'],
            de_id=resultado['de_id'],
            estado='confirmado',
            datos_factura=datos_factura,
            url_kude_pdf=f"{KUDE_CONFIG['url']}{resultado['numero_factura']}.pdf",
            url_kude_xml=f"{KUDE_CONFIG['url']}{resultado['numero_factura']}.xml"
        )
        
        # Actualizar estado de la transacción
        transaccion.observacion = f"Factura electrónica generada: {factura.numero_factura}"
        transaccion.save()
        
        return factura
    
    finally:
        servicio.desconectar()


def calcular_monto_pyg(transaccion):
    """
    Calcula el monto en guaraníes (PYG) de una transacción
    
    Args:
        transaccion: Instancia del modelo Transaccion
    
    Returns:
        Decimal: Monto en PYG
    """
    # Si alguna de las divisas es PYG, usar ese monto
    if transaccion.divisa_origen.code == 'PYG':
        return Decimal(transaccion.monto_origen)
    elif transaccion.divisa_destino.code == 'PYG':
        return Decimal(transaccion.monto_destino)
    else:
        # Si ninguna es PYG, usar el monto destino como aproximación
        # En un caso real, necesitarías obtener la cotización a PYG
        return Decimal(transaccion.monto_destino)


def actualizar_estado_factura(factura):
    """
    Consulta y actualiza el estado de una factura en el SIFEN
    
    Args:
        factura: Instancia del modelo FacturaElectronica
    
    Returns:
        dict: Estado actualizado de la factura
    """
    servicio = SQLProxyService()
    
    try:
        if not servicio.conectar():
            raise Exception("No se pudo conectar al SQL Proxy")
        
        # Consultar estado en el SQL Proxy
        estado = servicio.consultar_estado_factura(factura.numero_documento)
        
        if estado:
            # Actualizar campos de la factura
            factura.estado_sifen = estado.get('estado_sifen', '')
            factura.descripcion_sifen = estado.get('desc_sifen', '')
            factura.error_sifen = estado.get('error_sifen', '')
            
            # ⭐ Si tiene CDC VÁLIDO (no '0'), actualizar
            cdc_recibido = estado.get('cdc', '')
            if cdc_recibido and cdc_recibido != '0':
                factura.cdc = cdc_recibido
                factura.estado = 'aprobado'
                factura.fecha_aprobacion = timezone.now()
                
                # Construir URL del PDF en KuDE
                # Formato: /kude/YYYYMM/001-003-0000070_YYYYMMDD_HHMMSS_NNNNNN.pdf
                fecha_str = factura.fecha_emision.strftime('%Y%m')
                # URL base - se actualizará con el archivo específico después
                factura.url_kude_pdf = f"http://localhost:40080/kude/{fecha_str}/"
                factura.url_kude_xml = f"http://localhost:40080/kude/{fecha_str}/"
            
            # Si fue rechazado
            elif estado.get('error_sifen'):
                factura.estado = 'rechazado'
            
            factura.save()
        
        return estado
    
    finally:
        servicio.desconectar()


def buscar_y_actualizar_pdf(factura):
    """
    Busca el archivo PDF en el filesystem y actualiza la URL en la factura.
    
    Esta función se ejecuta automáticamente cada vez que se accede a una factura
    aprobada que aún no tiene la URL del PDF completa.
    
    Args:
        factura: Instancia de FacturaElectronica
    
    Returns:
        bool: True si se encontró y actualizó el PDF, False en caso contrario
    """
    # Solo buscar para facturas aprobadas con CDC válido
    if factura.estado != 'aprobado' or not factura.cdc or factura.cdc == '0':
        return False
    
    # Si ya tiene URL completa con .pdf, no buscar de nuevo
    if factura.url_kude_pdf and '.pdf' in factura.url_kude_pdf:
        return True
    
    try:
        # Construir patrón de búsqueda
        fecha_str = factura.fecha_emision.strftime('%Y%m')
        pdf_pattern = f'/home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/{fecha_str}/{factura.numero_factura}_*.pdf'
        
        # Buscar archivos que coincidan
        pdfs = glob.glob(pdf_pattern)
        
        if pdfs:
            # Tomar el primer archivo encontrado
            pdf_file = os.path.basename(pdfs[0])
            nueva_url = f"http://localhost:40080/kude/{fecha_str}/{pdf_file}"
            
            # Actualizar solo si cambió
            if factura.url_kude_pdf != nueva_url:
                factura.url_kude_pdf = nueva_url
                factura.save(update_fields=['url_kude_pdf'])
                logger.info(f"📄 PDF encontrado y actualizado para {factura.numero_factura}: {pdf_file}")
            
            return True
        else:
            logger.debug(f"PDF no encontrado aún para {factura.numero_factura} en {pdf_pattern}")
            return False
            
    except Exception as e:
        logger.warning(f"Error buscando PDF para {factura.numero_factura}: {e}")
        return False


def generar_facturas_pendientes():
    """
    Genera facturas para todas las transacciones completadas que no tienen factura
    
    Returns:
        dict: Resumen de facturas generadas y errores
    """
    from transacciones.models import Transaccion
    
    # Buscar transacciones completadas sin factura
    transacciones = Transaccion.objects.filter(
        estado__in=['completado', 'pagada']
    ).exclude(
        factura_electronica__isnull=False
    )
    
    resultados = {
        'generadas': [],
        'errores': []
    }
    
    for transaccion in transacciones:
        try:
            factura = generar_factura_desde_transaccion(transaccion)
            resultados['generadas'].append({
                'transaccion': transaccion.numero_transaccion,
                'factura': factura.numero_factura
            })
        except Exception as e:
            resultados['errores'].append({
                'transaccion': transaccion.numero_transaccion,
                'error': str(e)
            })
    
    return resultados
