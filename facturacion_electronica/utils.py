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


# ============================================================================
# FUNCIONES PARA GESTIÓN AUTOMÁTICA DE NÚMEROS DE FACTURA
# ============================================================================

def obtener_configuracion_facturacion():
    """
    Obtiene la configuración de facturación desde las variables de entorno.
    
    Returns:
        dict con la configuración:
            - numero_inicial: Primer número del rango asignado
            - numero_final: Último número del rango asignado
            - establecimiento: Código de establecimiento
            - punto_expedicion: Código de punto de expedición
    """
    import os
    return {
        'numero_inicial': int(os.getenv('FACTURACION_NUMERO_INICIAL', '51')),
        'numero_final': int(os.getenv('FACTURACION_NUMERO_FINAL', '100')),
        'establecimiento': os.getenv('FACTURACION_ESTABLECIMIENTO', '001'),
        'punto_expedicion': os.getenv('FACTURACION_PUNTO_EXPEDICION', '003')
    }


def extraer_numero_de_factura(numero_completo):
    """
    Extrae solo la parte numérica de un número de factura.
    
    Args:
        numero_completo: str en formato "001-003-0000083" o "0000083"
    
    Returns:
        int con el número extraído (ejemplo: 83)
    """
    if '-' in numero_completo:
        # Formato: "001-003-0000083"
        partes = numero_completo.split('-')
        return int(partes[2])
    else:
        # Formato: "0000083"
        return int(numero_completo)


def formatear_numero_factura(numero, establecimiento='001', punto_expedicion='003'):
    """
    Formatea un número de factura al formato completo.
    
    Args:
        numero: int o str con el número de factura (ejemplo: 83)
        establecimiento: Código de establecimiento (default: '001')
        punto_expedicion: Código de punto de expedición (default: '003')
    
    Returns:
        str en formato "001-003-0000083"
    """
    numero_str = str(numero).zfill(7)
    return f"{establecimiento}-{punto_expedicion}-{numero_str}"


def obtener_proximo_numero_factura():
    """
    Obtiene automáticamente el próximo número de factura disponible.
    
    Esta función:
    1. Consulta el SQL Proxy para obtener el último número usado (sincronizado entre todos)
    2. Si no hay conexión, usa la base de datos local como fallback
    3. Verifica que esté dentro del rango asignado al desarrollador
    4. Retorna el siguiente número disponible
    5. Es thread-safe (usa select_for_update)
    
    Returns:
        str: Número de factura en formato "001-003-0000083"
    
    Raises:
        ValueError: Si se alcanzó el límite del rango asignado
        ValueError: Si el próximo número está fuera del rango permitido
    
    Example:
        >>> numero = obtener_proximo_numero_factura()
        >>> print(numero)
        '001-003-0000083'
    """
    from django.db.models import Max
    from django.db import transaction
    import logging
    
    logger = logging.getLogger(__name__)
    config = obtener_configuracion_facturacion()
    
    with transaction.atomic():
        # PASO 1: Intentar obtener el último número desde SQL Proxy (sincronizado)
        proximo_numero = None
        try:
            from .services import SQLProxyService
            service = SQLProxyService()
            if service.conectar():
                ultimo_numero_sql_proxy = service.obtener_ultimo_numero_desde_sql_proxy()
                service.desconectar()
                
                if ultimo_numero_sql_proxy is not None:
                    proximo_numero = ultimo_numero_sql_proxy + 1
                    logger.info(f"[FACTURA] Número obtenido desde SQL Proxy: {proximo_numero}")
        except Exception as e:
            logger.warning(f"[FACTURA] No se pudo consultar SQL Proxy: {e}")
        
        # PASO 2: Fallback - usar la base de datos local si SQL Proxy no está disponible
        if proximo_numero is None:
            ultima_factura = FacturaElectronica.objects.select_for_update().aggregate(
                Max('numero_factura')
            )['numero_factura__max']
            
            if ultima_factura:
                ultimo_numero = extraer_numero_de_factura(ultima_factura)
                proximo_numero = ultimo_numero + 1
                logger.info(f"[FACTURA] Número obtenido desde BD local: {proximo_numero}")
            else:
                # No hay facturas, usar el número inicial del rango
                proximo_numero = config['numero_inicial']
                logger.info(f"[FACTURA] No hay facturas previas, usando número inicial: {proximo_numero}")
        
        # PASO 3: Verificar que el número esté dentro del rango asignado
        if proximo_numero < config['numero_inicial']:
            logger.warning(f"[FACTURA] Número {proximo_numero} menor al inicial {config['numero_inicial']}, ajustando...")
            proximo_numero = config['numero_inicial']
        
        if proximo_numero > config['numero_final']:
            raise ValueError(
                f"⚠️ LÍMITE DE RANGO ALCANZADO\n"
                f"Has usado todas las facturas de tu rango ({config['numero_inicial']}-{config['numero_final']}).\n"
                f"El siguiente número sería {proximo_numero}, pero está fuera de tu rango.\n"
                f"Coordina un nuevo rango con tu equipo y actualiza las variables de entorno:\n"
                f"  FACTURACION_NUMERO_INICIAL\n"
                f"  FACTURACION_NUMERO_FINAL\n"
                f"\nEjecuta: poetry run python obtener_proximo_numero.py"
            )
        
        logger.info(f"[FACTURA] Próximo número a usar: {proximo_numero}")
        
        # Formatear y retornar
        return formatear_numero_factura(
            proximo_numero,
            config['establecimiento'],
            config['punto_expedicion']
        )


def obtener_estadisticas_rango():
    """
    Obtiene estadísticas de uso del rango asignado.
    
    Returns:
        dict con:
            - total_rango: Total de números en el rango
            - usadas: Cantidad de facturas generadas en el rango
            - disponibles: Cantidad de números disponibles
            - porcentaje_usado: Porcentaje de uso del rango
            - numero_inicial: Primer número del rango
            - numero_final: Último número del rango
            - proximo_numero: Próximo número que se usará
    """
    config = obtener_configuracion_facturacion()
    
    # Total de números en el rango
    total_rango = config['numero_final'] - config['numero_inicial'] + 1
    
    # Contar facturas en el rango
    rango_inicio_str = formatear_numero_factura(config['numero_inicial'])
    rango_fin_str = formatear_numero_factura(config['numero_final'])
    
    usadas = FacturaElectronica.objects.filter(
        numero_factura__gte=rango_inicio_str,
        numero_factura__lte=rango_fin_str
    ).count()
    
    # Calcular disponibles
    disponibles = total_rango - usadas
    porcentaje_usado = (usadas / total_rango) * 100 if total_rango > 0 else 0
    
    # Próximo número
    try:
        proximo = obtener_proximo_numero_factura()
    except ValueError:
        proximo = "Rango completo"
    
    return {
        'total_rango': total_rango,
        'usadas': usadas,
        'disponibles': disponibles,
        'porcentaje_usado': round(porcentaje_usado, 1),
        'numero_inicial': config['numero_inicial'],
        'numero_final': config['numero_final'],
        'proximo_numero': proximo
    }
