"""
Vistas para el módulo de Facturación Electrónica
Usa el sistema de roles y permisos personalizado (NO Django Admin)
"""
import glob
import os
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator

from roles.decorators import require_permission
from .models import FacturaElectronica
from .services import SQLProxyService
from .utils import generar_factura_desde_transaccion, actualizar_estado_factura
from transacciones.models import Transaccion

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# LISTADO DE FACTURAS
# ═══════════════════════════════════════════════════════════════════════════

@login_required
@require_permission('facturacion_electronica.view_todas_facturas')
def lista_facturas(request):
    """
    Lista facturas electrónicas agrupadas por cliente
    Permite filtrar por segmento, estado y búsqueda
    """
    # ═══ AUTO-SINCRONIZAR FACTURAS PENDIENTES ═══
    # Buscar facturas sin CDC válido o en estado pendiente
    facturas_pendientes = FacturaElectronica.objects.filter(
        Q(cdc__isnull=True) | Q(cdc='0') | Q(estado__in=['confirmado', 'borrador'])
    )
    facturas_sin_pdf = FacturaElectronica.objects.filter(
        estado='aprobado'
    ).exclude(cdc__isnull=True).exclude(cdc='0').exclude(url_kude_pdf__contains='.pdf')
    
    # Sincronizar estados desde SQL Proxy
    for factura in facturas_pendientes:
        try:
            actualizar_estado_factura(factura)
            factura.refresh_from_db()
        except Exception as e:
            logger.warning(f"No se pudo sincronizar {factura.numero_factura}: {e}")
    
    # Buscar PDFs en el filesystem para facturas aprobadas sin URL completa
    from .utils import buscar_y_actualizar_pdf
    for factura in list(facturas_pendientes) + list(facturas_sin_pdf):
        if factura.estado == 'aprobado' and factura.cdc and factura.cdc != '0':
            try:
                buscar_y_actualizar_pdf(factura)
            except Exception as e:
                logger.warning(f"Error buscando PDF para {factura.numero_factura}: {e}")
    
    # ═══ OBTENER TODAS LAS FACTURAS ═══
    facturas = FacturaElectronica.objects.all().select_related(
        'transaccion', 
        'transaccion__cliente',
        'transaccion__cliente__segmento'
    )
    
    # ═══ FILTROS ═══
    from clientes.models import Cliente, Segmento
    
    segmento_id = request.GET.get('segmento', '')
    estado = request.GET.get('estado', '')
    busqueda = request.GET.get('q', '')
    
    # Filtro por estado
    if estado:
        facturas = facturas.filter(estado=estado)
    
    # Filtro por búsqueda
    if busqueda:
        facturas = facturas.filter(
            Q(numero_factura__icontains=busqueda) |
            Q(cdc__icontains=busqueda) |
            Q(transaccion__numero_transaccion__icontains=busqueda) |
            Q(transaccion__cliente__nombre_completo__icontains=busqueda)
        )
    
    # ═══ AGRUPAR POR CLIENTE ═══
    clientes_con_facturas = {}
    for factura in facturas:
        cliente = factura.transaccion.cliente
        if cliente not in clientes_con_facturas:
            clientes_con_facturas[cliente] = {
                'facturas': [],
                'total_facturas': 0,
                'total_aprobadas': 0,
                'total_rechazadas': 0,
            }
        clientes_con_facturas[cliente]['facturas'].append(factura)
        clientes_con_facturas[cliente]['total_facturas'] += 1
        if factura.estado == 'aprobado':
            clientes_con_facturas[cliente]['total_aprobadas'] += 1
        elif factura.estado == 'rechazado':
            clientes_con_facturas[cliente]['total_rechazadas'] += 1
    
    # Filtrar por segmento si se especificó
    if segmento_id:
        clientes_con_facturas = {
            cliente: datos 
            for cliente, datos in clientes_con_facturas.items() 
            if cliente.segmento_id == int(segmento_id)
        }
    
    # Ordenar clientes alfabéticamente
    clientes_ordenados = sorted(
        clientes_con_facturas.items(),
        key=lambda x: x[0].nombre_completo
    )
    
    # Ordenar facturas dentro de cada cliente por fecha (más reciente primero)
    for cliente, datos in clientes_ordenados:
        datos['facturas'].sort(key=lambda x: x.fecha_emision, reverse=True)
    
    # Obtener lista de segmentos para el filtro
    segmentos = Segmento.objects.filter(
        cliente__transacciones__factura_electronica__isnull=False
    ).distinct().order_by('name')
    
    context = {
        'clientes_con_facturas': clientes_ordenados,
        'segmentos': segmentos,
        'segmento_filtro': segmento_id,
        'estado_filtro': estado,
        'busqueda': busqueda,
        'total_clientes': len(clientes_ordenados),
        'total_facturas': sum(datos['total_facturas'] for _, datos in clientes_ordenados),
        'titulo': 'Facturas Electrónicas por Cliente'
    }
    
    return render(request, 'facturacion/lista_facturas.html', context)


@login_required
@require_permission('facturacion_electronica.view_facturas_propias')
def mis_facturas(request):
    """
    Lista las facturas del cliente actual
    Solo ve sus propias facturas (de sus transacciones)
    """
    # Obtener clientes asociados al usuario actual
    from clientes.models import Cliente
    clientes_usuario = Cliente.objects.filter(usuarios=request.user)
    
    # Obtener transacciones de esos clientes
    transacciones_usuario = Transaccion.objects.filter(cliente__in=clientes_usuario)
    
    # Obtener facturas de esas transacciones
    facturas = FacturaElectronica.objects.filter(
        transaccion__in=transacciones_usuario
    ).select_related('transaccion').order_by('-fecha_emision')
    
    # ═══ AUTO-SINCRONIZAR FACTURAS PENDIENTES ═══
    # Buscar facturas sin CDC válido o en estado pendiente
    facturas_pendientes = facturas.filter(
        Q(cdc__isnull=True) | Q(cdc='0') | Q(estado__in=['confirmado', 'borrador'])
    )
    facturas_sin_pdf = facturas.filter(
        estado='aprobado'
    ).exclude(cdc__isnull=True).exclude(cdc='0').exclude(url_kude_pdf__contains='.pdf')
    
    # Sincronizar estados desde SQL Proxy
    for factura in facturas_pendientes:
        try:
            actualizar_estado_factura(factura)
            factura.refresh_from_db()
        except Exception as e:
            logger.warning(f"No se pudo sincronizar {factura.numero_factura}: {e}")
    
    # Buscar PDFs en el filesystem para facturas aprobadas sin URL completa
    from .utils import buscar_y_actualizar_pdf
    for factura in list(facturas_pendientes) + list(facturas_sin_pdf):
        if factura.estado == 'aprobado' and factura.cdc and factura.cdc != '0':
            try:
                buscar_y_actualizar_pdf(factura)
            except Exception as e:
                logger.warning(f"Error buscando PDF para {factura.numero_factura}: {e}")
    
    # Refrescar la consulta después de las actualizaciones
    facturas = FacturaElectronica.objects.filter(
        transaccion__in=transacciones_usuario
    ).select_related('transaccion').order_by('-fecha_emision')
    
    # Paginación
    paginator = Paginator(facturas, 10)
    page = request.GET.get('page')
    facturas_page = paginator.get_page(page)
    
    context = {
        'facturas': facturas_page,
        'total_facturas': facturas.count(),
        'titulo': 'Mis Facturas Electrónicas'
    }
    return render(request, 'facturacion/mis_facturas.html', context)


# ═══════════════════════════════════════════════════════════════════════════
# DETALLE DE FACTURA
# ═══════════════════════════════════════════════════════════════════════════

@login_required
def detalle_factura(request, factura_id):
    """
    Muestra el detalle de una factura
    - Clientes solo pueden ver sus propias facturas
    - Staff con permisos puede ver todas
    
    Requiere uno de estos permisos:
    - view_facturas_propias (clientes)
    - view_facturas_asignadas (operadores)
    - view_todas_facturas (administradores)
    """
    # Verificar permisos
    tiene_permiso = (
        request.user.has_perm('facturacion_electronica.view_facturas_propias') or
        request.user.has_perm('facturacion_electronica.view_facturas_asignadas') or
        request.user.has_perm('facturacion_electronica.view_todas_facturas')
    )
    
    if not tiene_permiso:
        messages.error(request, 'No tiene permisos para ver facturas electrónicas.')
        return redirect('interfaz:home')
    
    factura = get_object_or_404(
        FacturaElectronica.objects.select_related('transaccion'),
        pk=factura_id
    )
    
    # AUTO-SINCRONIZAR: Si la factura está en estado procesando o sin CDC válido, actualizar desde SQL Proxy
    if factura.estado in ['confirmado', 'borrador'] or not factura.cdc or factura.cdc == '0':
        try:
            from .utils import actualizar_estado_factura
            actualizar_estado_factura(factura)
            factura.refresh_from_db()
            logger.info(f"🔄 Factura {factura.numero_factura} sincronizada - Estado: {factura.estado}, CDC: {factura.cdc[:20] if factura.cdc and factura.cdc != '0' else 'pendiente'}...")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"No se pudo sincronizar factura {factura.numero_factura}: {e}")
    
    # AUTO-BUSCAR PDF: Si está aprobada pero no tiene URL del PDF completa, buscar en filesystem
    if factura.estado == 'aprobado' and factura.cdc and factura.cdc != '0':
        if not factura.url_kude_pdf or '.pdf' not in factura.url_kude_pdf:
            try:
                from .utils import buscar_y_actualizar_pdf
                buscar_y_actualizar_pdf(factura)
                factura.refresh_from_db()
            except Exception as e:
                logger.warning(f"No se pudo buscar PDF para {factura.numero_factura}: {e}")
    
    # Verificar permisos
    if request.user.is_staff:
        # Staff con permiso puede ver todas
        if not request.user.has_perm('facturacion_electronica.view_todas_facturas'):
            # Si no tiene permiso global, verificar si tiene permiso de asignados
            if not request.user.has_perm('facturacion_electronica.view_facturas_asignadas'):
                messages.error(request, 'No tiene permiso para ver facturas.')
                return redirect('inicio')
    else:
        # Cliente solo puede ver sus propias facturas (a través de su Cliente)
        from clientes.models import Cliente
        clientes_usuario = Cliente.objects.filter(usuarios=request.user)
        
        # Verificar que la transacción pertenezca a alguno de los clientes del usuario
        if factura.transaccion.cliente not in clientes_usuario:
            messages.error(request, 'No puede ver facturas de otros usuarios.')
            return redirect('facturacion:mis_facturas')
    
    context = {
        'factura': factura,
        'titulo': f'Factura {factura.numero_factura}'
    }
    return render(request, 'facturacion/detalle_factura.html', context)


# ═══════════════════════════════════════════════════════════════════════════
# GENERACIÓN DE FACTURAS
# ═══════════════════════════════════════════════════════════════════════════

@login_required
@require_permission('facturacion_electronica.generar_factura')
def generar_factura(request, transaccion_id):
    """
    Genera una factura electrónica para una transacción
    Solo para staff con permisos
    """
    transaccion = get_object_or_404(Transaccion, pk=transaccion_id)
    
    # Verificar que no tenga factura ya
    if hasattr(transaccion, 'factura'):
        messages.warning(request, 'Esta transacción ya tiene una factura generada.')
        return redirect('facturacion:detalle_factura', factura_id=transaccion.factura.id)
    
    # Verificar que la transacción esté completada
    if transaccion.estado != 'completada':
        messages.error(request, 'Solo se pueden facturar transacciones completadas.')
        return redirect('transacciones:detalle', pk=transaccion_id)
    
    try:
        factura = generar_factura_desde_transaccion(transaccion)
        messages.success(
            request,
            f'Factura {factura.numero_factura} generada exitosamente. CDC: {factura.cdc or "Pendiente"}'
        )
        return redirect('facturacion:detalle_factura', factura_id=factura.id)
    except Exception as e:
        messages.error(request, f'Error al generar factura: {str(e)}')
        return redirect('transacciones:detalle', pk=transaccion_id)


# ═══════════════════════════════════════════════════════════════════════════
# DESCARGA DE DOCUMENTOS (PDF/XML)
# ═══════════════════════════════════════════════════════════════════════════

@login_required
@require_permission('facturacion_electronica.download_kude_pdf')
def descargar_pdf(request, factura_id):
    """
    Descarga el PDF desde KuDE y lo sirve al usuario
    - Actúa como proxy para manejar autenticación
    - Clientes pueden descargar sus propias facturas
    - Staff con permiso puede descargar todas
    """
    import urllib.request
    import urllib.error
    import base64
    from django.http import HttpResponse
    
    factura = get_object_or_404(FacturaElectronica, pk=factura_id)
    
    # Verificar permisos
    if not request.user.is_staff:
        # Cliente solo puede descargar sus propias facturas (a través de su Cliente)
        from clientes.models import Cliente
        clientes_usuario = Cliente.objects.filter(usuarios=request.user)
        
        # Verificar que la transacción pertenezca a alguno de los clientes del usuario
        if factura.transaccion.cliente not in clientes_usuario:
            messages.error(request, 'No puede descargar facturas de otros usuarios.')
            return redirect('facturacion:mis_facturas')
    
    # Verificar que la factura esté aprobada
    if factura.estado != 'aprobado':
        # Intentar sincronizar primero
        try:
            actualizar_estado_factura(factura)
            factura.refresh_from_db()
        except:
            pass
        
        if factura.estado != 'aprobado':
            messages.warning(request, 'La factura aún no está aprobada por SIFEN. Por favor espere.')
            return redirect('facturacion:detalle_factura', factura_id=factura_id)
    
    # Si ya tiene URL completa con .pdf, redirigir directamente
    if factura.url_kude_pdf and '.pdf' in factura.url_kude_pdf:
        pdf_url = factura.url_kude_pdf
    else:
        # Si no tiene URL o solo tiene directorio, intentar buscar el PDF en KuDE
        from .services import SQLProxyService
        service = SQLProxyService()
        pdf_url = service.buscar_pdf_en_kude(factura.numero_factura, factura.fecha_emision)
        
        if pdf_url:
            # PDF encontrado - actualizar URL
            factura.url_kude_pdf = pdf_url
            factura.save(update_fields=['url_kude_pdf'])
        else:
            # PDF no encontrado - dar mensaje al usuario
            messages.warning(
                request, 
                'El PDF aún se está generando en SIFEN. Este proceso puede tomar 1-3 minutos. '
                'Por favor, intente nuevamente en unos momentos o actualice la página.'
            )
            return redirect('facturacion:detalle_factura', factura_id=factura_id)
    
    # Descargar PDF desde KuDE con autenticación y servirlo al usuario
    try:
        from .config import KUDE_CONFIG
        
        # Convertir URL pública a URL interna si es necesario
        pdf_url_interna = pdf_url.replace('localhost', 'host.docker.internal')
        
        # Preparar autenticación
        credentials = f"{KUDE_CONFIG['username']}:{KUDE_CONFIG['password']}"
        encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        # Descargar el PDF
        req = urllib.request.Request(pdf_url_interna)
        req.add_header('Authorization', f'Basic {encoded}')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            pdf_content = response.read()
            
            # Crear respuesta HTTP con el PDF
            http_response = HttpResponse(pdf_content, content_type='application/pdf')
            http_response['Content-Disposition'] = f'attachment; filename="{factura.numero_factura}.pdf"'
            
            return http_response
            
    except urllib.error.HTTPError as e:
        messages.error(request, f'Error al descargar PDF: {e.code} {e.reason}')
        return redirect('facturacion:detalle_factura', factura_id=factura_id)
    except Exception as e:
        logger.error(f"[PDF] Error descargando PDF: {e}")
        messages.error(request, 'Error al descargar el PDF. Intente nuevamente.')
        return redirect('facturacion:detalle_factura', factura_id=factura_id)


@login_required
@require_permission('facturacion_electronica.download_kude_xml')
def descargar_xml(request, factura_id):
    """
    Redirige a la URL del XML en KuDE
    Solo para staff con permisos
    """
    factura = get_object_or_404(FacturaElectronica, pk=factura_id)
    
    # Verificar que la factura esté aprobada
    if factura.estado != 'aprobado':
        messages.warning(request, 'La factura aún no está aprobada por SIFEN. Por favor espere.')
        return redirect('facturacion:detalle_factura', factura_id=factura_id)
    
    if not factura.url_kude_xml:
        messages.warning(request, 'La factura aún no tiene XML disponible.')
        return redirect('facturacion:detalle_factura', factura_id=factura_id)
    
    return redirect(factura.url_kude_xml)


# ═══════════════════════════════════════════════════════════════════════════
# SINCRONIZACIÓN CON SIFEN
# ═══════════════════════════════════════════════════════════════════════════

@login_required
@require_permission('facturacion_electronica.sync_sifen')
def actualizar_estado(request, factura_id):
    """
    Sincroniza el estado de una factura con SIFEN
    Solo para staff con permisos
    """
    factura = get_object_or_404(FacturaElectronica, pk=factura_id)
    
    try:
        from .services import actualizar_estado_factura
        if actualizar_estado_factura(factura.id):
            messages.success(request, f'✅ Estado actualizado: {factura.estado_sifen or "Pendiente"}')
        else:
            messages.warning(request, '⚠️ No se pudo actualizar el estado. Intente nuevamente en unos segundos.')
    except Exception as e:
        messages.error(request, f'Error al actualizar estado: {str(e)}')
    
    return redirect('facturacion:detalle_factura', factura_id=factura_id)


# ═══════════════════════════════════════════════════════════════════════════
# ANULACIÓN DE FACTURAS
# ═══════════════════════════════════════════════════════════════════════════

@login_required
@require_permission('facturacion_electronica.cancelar_factura')
def cancelar_factura(request, factura_id):
    """
    Anula una factura electrónica en SIFEN
    Solo para supervisores/administradores con permisos críticos
    """
    factura = get_object_or_404(FacturaElectronica, pk=factura_id)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        
        if not motivo:
            messages.error(request, 'Debe proporcionar un motivo de anulación.')
            return redirect('facturacion:detalle_factura', factura_id=factura_id)
        
        try:
            service = SQLProxyService()
            service.conectar()
            result = service.cancelar_factura(factura.numero_factura, motivo)
            service.desconectar()
            
            if result.get('exito'):
                factura.estado = 'cancelada'
                factura.save()
                messages.success(request, f'Factura {factura.numero_factura} cancelada exitosamente.')
            else:
                messages.error(request, f'Error al cancelar: {result.get("error")}')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('facturacion:detalle_factura', factura_id=factura_id)
    
    context = {
        'factura': factura,
        'titulo': 'Cancelar Factura'
    }
    return render(request, 'facturacion/cancelar_factura.html', context)


# ═══════════════════════════════════════════════════════════════════════════
# REPORTES
# ═══════════════════════════════════════════════════════════════════════════

@login_required
@require_permission('facturacion_electronica.view_reporte_facturacion')
def reporte_facturacion(request):
    """
    Muestra reporte consolidado de facturación
    Solo para staff con permisos
    """
    from django.db.models import Count, Sum
    from datetime import datetime, timedelta
    
    # Estadísticas generales
    total_facturas = FacturaElectronica.objects.count()
    facturas_aprobadas = FacturaElectronica.objects.filter(estado_sifen='Aprobado').count()
    facturas_pendientes = FacturaElectronica.objects.filter(estado='borrador').count()
    facturas_rechazadas = FacturaElectronica.objects.filter(estado_sifen='Rechazado').count()
    
    # Facturas del mes actual
    hoy = datetime.now()
    inicio_mes = hoy.replace(day=1)
    facturas_mes = FacturaElectronica.objects.filter(
        fecha_emision__gte=inicio_mes
    ).count()
    
    # Facturas por estado
    por_estado = FacturaElectronica.objects.values('estado').annotate(
        cantidad=Count('id')
    ).order_by('estado')
    
    context = {
        'total_facturas': total_facturas,
        'facturas_aprobadas': facturas_aprobadas,
        'facturas_pendientes': facturas_pendientes,
        'facturas_rechazadas': facturas_rechazadas,
        'facturas_mes': facturas_mes,
        'por_estado': por_estado,
        'titulo': 'Reporte de Facturación'
    }
    return render(request, 'facturacion/reporte.html', context)


@login_required
def verificar_pdf_disponible(request, factura_id):
    """
    Endpoint AJAX para verificar si el PDF de una factura está disponible en KuDE.
    Actualiza la URL del PDF si lo encuentra.
    
    Returns:
        JSON con {disponible: true/false, url: string}
    """
    try:
        factura = get_object_or_404(FacturaElectronica, id=factura_id)
        
        # Si ya tiene URL válida con .pdf, retornar
        if factura.url_kude_pdf and '.pdf' in factura.url_kude_pdf:
            return JsonResponse({
                'disponible': True,
                'url': factura.url_kude_pdf,
                'mensaje': 'PDF ya disponible'
            })
        
        # Buscar PDF en KuDE
        service = SQLProxyService()
        pdf_url = service.buscar_pdf_en_kude(
            factura.numero_factura,
            factura.fecha_emision
        )
        
        if pdf_url:
            # Actualizar la factura
            factura.url_kude_pdf = pdf_url
            factura.save(update_fields=['url_kude_pdf'])
            
            logger.info(f"[PDF] ✅ PDF encontrado y actualizado para {factura.numero_factura}")
            
            return JsonResponse({
                'disponible': True,
                'url': pdf_url,
                'mensaje': 'PDF encontrado y actualizado'
            })
        else:
            return JsonResponse({
                'disponible': False,
                'mensaje': 'PDF aún no está disponible. Intente en unos segundos.'
            })
            
    except Exception as e:
        logger.error(f"[PDF] Error verificando PDF: {e}")
        return JsonResponse({
            'disponible': False,
            'error': str(e)
        }, status=500)
