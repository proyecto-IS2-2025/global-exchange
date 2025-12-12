from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import RegistroGanancia, ResumenGananciaDiaria, ResumenGananciaMensual
from transacciones.models import Transaccion
from divisas.models import Divisa
import json
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


@login_required
@permission_required('ganancias.view_tablero_ganancias', raise_exception=True)
def tablero_ganancias(request):
    """
    Vista principal del tablero de control de ganancias
    """
    # Clase auxiliar para datos de evolución
    class DatoEvolucion:
        def __init__(self, fecha, total):
            self.fecha = fecha
            self.total_spread = total
            self.total = total
    
    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    periodo = request.GET.get('periodo', 'mes_actual')  # dia, semana, mes_actual, mes_anterior, año
    divisa_id = request.GET.get('divisa')  # Nuevo filtro por divisa
    
    # Definir el rango de fechas según el período seleccionado
    hoy = timezone.now().date()
    
    if periodo == 'dia':
        fecha_inicio = hoy
        fecha_fin = hoy
    elif periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
        fecha_fin = hoy
    elif periodo == 'mes_actual':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
    elif periodo == 'mes_anterior':
        primer_dia_mes_actual = hoy.replace(day=1)
        ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
        fecha_inicio = ultimo_dia_mes_anterior.replace(day=1)
        fecha_fin = ultimo_dia_mes_anterior
    elif periodo == 'año':
        fecha_inicio = hoy.replace(month=1, day=1)
        fecha_fin = hoy
    elif periodo == 'todo':
        # Obtener la primera transacción registrada
        primera_ganancia = RegistroGanancia.objects.filter(
            transaccion__estado__in=['completado', 'pagada'],
            tipo_ganancia='spread'
        ).order_by('fecha_transaccion').first()
        
        if primera_ganancia:
            fecha_inicio = primera_ganancia.fecha_transaccion.date()
        else:
            fecha_inicio = hoy.replace(month=1, day=1)  # Si no hay datos, usar inicio del año
        fecha_fin = hoy
    elif fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    else:
        # Por defecto, mes actual
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
    
    # Obtener ganancias del período (solo margen, no comisiones)
    ganancias = RegistroGanancia.objects.filter(
        fecha_transaccion__date__gte=fecha_inicio,
        fecha_transaccion__date__lte=fecha_fin,
        transaccion__estado__in=['completado', 'pagada'],  # Solo transacciones válidas
        tipo_ganancia='spread'  # Solo ganancias por margen, no comisiones
    )
    
    # Aplicar filtro por divisa si está seleccionado
    if divisa_id:
        ganancias = ganancias.filter(divisa_referencia_id=divisa_id)
    
    # Calcular totales
    totales = ganancias.aggregate(
        total_comisiones=Sum('monto_comision'),
        total_spread=Sum('monto_spread'),
        total_general=Sum('monto_total'),
        cantidad_transacciones=Count('id')
    )
    
    # Ganancias por tipo de operación (compra vs venta)
    ganancias_por_operacion = ganancias.values('transaccion__tipo_operacion').annotate(
        total=Sum('monto_spread'),
        cantidad=Count('id')
    ).order_by('-total')
    
    # Calcular totales por tipo de operación
    total_compras = ganancias.filter(transaccion__tipo_operacion='compra').aggregate(
        total=Sum('monto_spread'),
        cantidad=Count('id')
    )
    # Asegurar valores por defecto
    if total_compras['total'] is None:
        total_compras['total'] = Decimal('0.00')
    if total_compras['cantidad'] is None:
        total_compras['cantidad'] = 0
    
    total_ventas = ganancias.filter(transaccion__tipo_operacion='venta').aggregate(
        total=Sum('monto_spread'),
        cantidad=Count('id')
    )
    # Asegurar valores por defecto
    if total_ventas['total'] is None:
        total_ventas['total'] = Decimal('0.00')
    if total_ventas['cantidad'] is None:
        total_ventas['cantidad'] = 0
    
    # Ganancias por divisa
    ganancias_por_divisa = ganancias.values(
        'divisa_referencia__code',
        'divisa_referencia__nombre'
    ).annotate(
        total=Sum('monto_total'),
        cantidad=Count('id')
    ).order_by('-total')
    
    # Ganancias por tipo
    ganancias_por_tipo = ganancias.values('tipo_ganancia').annotate(
        total=Sum('monto_total'),
        cantidad=Count('id')
    )
    
    # Evolución diaria
    evolucion_diaria = ResumenGananciaDiaria.objects.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).order_by('fecha')
    
    # Evolución diaria separada por tipo de operación
    # Obtener todas las fechas únicas con ganancias en el período
    from django.db.models.functions import TruncDate
    
    fechas_con_ganancias = ganancias.annotate(
        fecha_solo=TruncDate('fecha_transaccion')
    ).values('fecha_solo').distinct().order_by('fecha_solo')
    
    evolucion_compras = []
    evolucion_ventas = []
    
    for item in fechas_con_ganancias:
        fecha = item['fecha_solo']
        
        # Ganancias de compras del día
        ganancia_compras = ganancias.filter(
            fecha_transaccion__date=fecha,
            transaccion__tipo_operacion='compra'
        ).aggregate(total=Sum('monto_spread'))['total'] or Decimal('0.00')
        
        # Ganancias de ventas del día
        ganancia_ventas = ganancias.filter(
            fecha_transaccion__date=fecha,
            transaccion__tipo_operacion='venta'
        ).aggregate(total=Sum('monto_spread'))['total'] or Decimal('0.00')
        
        evolucion_compras.append(DatoEvolucion(fecha, ganancia_compras))
        evolucion_ventas.append(DatoEvolucion(fecha, ganancia_ventas))
    
    # Recalcular evolucion_diaria basándose en las fechas con ganancias
    evolucion_diaria_calculada = []
    for item in fechas_con_ganancias:
        fecha = item['fecha_solo']
        total_dia = ganancias.filter(
            fecha_transaccion__date=fecha
        ).aggregate(total=Sum('monto_spread'))['total'] or Decimal('0.00')
        
        evolucion_diaria_calculada.append(DatoEvolucion(fecha, total_dia))
    
    # Calcular período de comparación (mismo período anterior)
    dias_diferencia = (fecha_fin - fecha_inicio).days + 1
    fecha_inicio_anterior = fecha_inicio - timedelta(days=dias_diferencia)
    fecha_fin_anterior = fecha_inicio - timedelta(days=1)
    
    ganancias_periodo_anterior = RegistroGanancia.objects.filter(
        fecha_transaccion__date__gte=fecha_inicio_anterior,
        fecha_transaccion__date__lte=fecha_fin_anterior
    )
    
    totales_periodo_anterior = ganancias_periodo_anterior.aggregate(
        total_general=Sum('monto_total')
    )
    
    # Calcular variación porcentual (solo basado en spread, que es la ganancia real)
    variacion_porcentual = 0
    if totales_periodo_anterior['total_general'] and totales_periodo_anterior['total_general'] > 0:
        total_actual = totales['total_spread'] or Decimal('0.00')  # Solo spread es ganancia
        total_anterior = totales_periodo_anterior['total_general']
        variacion_porcentual = ((total_actual - total_anterior) / total_anterior * 100)
    
    # Top 10 transacciones con mayor ganancia
    top_transacciones = ganancias.select_related(
        'transaccion',
        'transaccion__cliente',
        'divisa_referencia'
    ).order_by('-monto_total')[:10]
    
    # Todas las transacciones del período (paginadas)
    todas_transacciones = ganancias.select_related(
        'transaccion',
        'transaccion__cliente',
        'divisa_referencia'
    ).order_by('-fecha_transaccion')
    
    # Promedio de ganancia por transacción (solo spread)
    promedio_por_transaccion = Decimal('0.00')
    if totales['cantidad_transacciones'] and totales['cantidad_transacciones'] > 0:
        promedio_por_transaccion = (totales['total_spread'] or Decimal('0.00')) / totales['cantidad_transacciones']
    
    # Obtener lista de divisas para el filtro
    divisas = Divisa.objects.filter(is_active=True).order_by('nombre')
    divisa_seleccionada = None
    if divisa_id:
        try:
            divisa_seleccionada = Divisa.objects.get(id=divisa_id)
        except Divisa.DoesNotExist:
            pass
    
    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'periodo': periodo,
        'divisas': divisas,
        'divisa_seleccionada': divisa_seleccionada,
        'totales': totales,
        'total_compras': total_compras,
        'total_ventas': total_ventas,
        'ganancias_por_operacion': ganancias_por_operacion,
        'ganancias_por_divisa': ganancias_por_divisa,
        'ganancias_por_tipo': ganancias_por_tipo,
        'evolucion_diaria': evolucion_diaria_calculada,
        'evolucion_compras': evolucion_compras,
        'evolucion_ventas': evolucion_ventas,
        'variacion_porcentual': variacion_porcentual,
        'top_transacciones': top_transacciones,
        'todas_transacciones': todas_transacciones,
        'promedio_por_transaccion': promedio_por_transaccion,
        'totales_periodo_anterior': totales_periodo_anterior,
    }
    
    return render(request, 'ganancias/tablero.html', context)


@login_required
@permission_required('ganancias.view_tablero_ganancias', raise_exception=True)
def api_ganancias_evolucion(request):
    """
    API para obtener datos de evolución de ganancias (para gráficos)
    """
    periodo = request.GET.get('periodo', 'mes_actual')
    tipo = request.GET.get('tipo', 'diaria')  # diaria, semanal, mensual
    
    hoy = timezone.now().date()
    
    # Definir rango de fechas
    if periodo == 'mes_actual':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
    elif periodo == 'mes_anterior':
        primer_dia_mes_actual = hoy.replace(day=1)
        ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
        fecha_inicio = ultimo_dia_mes_anterior.replace(day=1)
        fecha_fin = ultimo_dia_mes_anterior
    elif periodo == 'año':
        fecha_inicio = hoy.replace(month=1, day=1)
        fecha_fin = hoy
    else:
        fecha_inicio = hoy - timedelta(days=30)
        fecha_fin = hoy
    
    if tipo == 'diaria':
        datos = ResumenGananciaDiaria.objects.filter(
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin
        ).order_by('fecha').values(
            'fecha',
            'total_comisiones',
            'total_spread',
            'total_general',
            'cantidad_transacciones'
        )
        
        datos_json = list(datos)
        for item in datos_json:
            item['fecha'] = item['fecha'].strftime('%Y-%m-%d')
            item['total_comisiones'] = float(item['total_comisiones'])
            item['total_spread'] = float(item['total_spread'])
            item['total_general'] = float(item['total_general'])
    
    elif tipo == 'mensual':
        datos = ResumenGananciaMensual.objects.filter(
            año__gte=fecha_inicio.year,
            mes__gte=fecha_inicio.month if fecha_inicio.year == fecha_fin.year else 1
        ).order_by('año', 'mes').values(
            'año',
            'mes',
            'total_comisiones',
            'total_spread',
            'total_general',
            'cantidad_transacciones'
        )
        
        datos_json = list(datos)
        for item in datos_json:
            item['periodo'] = f"{item['mes']:02d}/{item['año']}"
            item['total_comisiones'] = float(item['total_comisiones'])
            item['total_spread'] = float(item['total_spread'])
            item['total_general'] = float(item['total_general'])
    
    else:
        datos_json = []
    
    return JsonResponse({
        'success': True,
        'datos': datos_json,
        'periodo': periodo,
        'tipo': tipo
    })


@login_required
@permission_required('ganancias.view_tablero_ganancias', raise_exception=True)
def api_ganancias_por_divisa(request):
    """
    API para obtener distribución de ganancias por divisa
    """
    periodo = request.GET.get('periodo', 'mes_actual')
    hoy = timezone.now().date()
    
    if periodo == 'mes_actual':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
    elif periodo == 'año':
        fecha_inicio = hoy.replace(month=1, day=1)
        fecha_fin = hoy
    else:
        fecha_inicio = hoy - timedelta(days=30)
        fecha_fin = hoy
    
    ganancias = RegistroGanancia.objects.filter(
        fecha_transaccion__date__gte=fecha_inicio,
        fecha_transaccion__date__lte=fecha_fin
    ).values(
        'divisa_referencia__code',
        'divisa_referencia__nombre'
    ).annotate(
        total=Sum('monto_total'),
        total_comisiones=Sum('monto_comision'),
        total_spread=Sum('monto_spread'),
        cantidad=Count('id')
    ).order_by('-total')
    
    datos = []
    for item in ganancias:
        datos.append({
            'divisa': item['divisa_referencia__code'],
            'nombre': item['divisa_referencia__nombre'],
            'total': float(item['total']),
            'total_comisiones': float(item['total_comisiones']),
            'total_spread': float(item['total_spread']),
            'cantidad': item['cantidad']
        })
    
    return JsonResponse({
        'success': True,
        'datos': datos
    })


@login_required
@permission_required('ganancias.view_comparacion_ganancias', raise_exception=True)
def comparacion_periodos(request):
    """
    Vista para comparar ganancias entre diferentes períodos
    """
    hoy = timezone.now().date()
    
    # Mes actual vs mes anterior
    primer_dia_mes_actual = hoy.replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
    primer_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)
    
    # Ganancias mes actual
    ganancias_mes_actual = RegistroGanancia.objects.filter(
        fecha_transaccion__date__gte=primer_dia_mes_actual,
        fecha_transaccion__date__lte=hoy
    ).aggregate(
        total=Sum('monto_total'),
        comisiones=Sum('monto_comision'),
        spread=Sum('monto_spread'),
        cantidad=Count('id')
    )
    
    # Ganancias mes anterior
    ganancias_mes_anterior = RegistroGanancia.objects.filter(
        fecha_transaccion__date__gte=primer_dia_mes_anterior,
        fecha_transaccion__date__lte=ultimo_dia_mes_anterior
    ).aggregate(
        total=Sum('monto_total'),
        comisiones=Sum('monto_comision'),
        spread=Sum('monto_spread'),
        cantidad=Count('id')
    )
    
    # Año actual vs año anterior
    primer_dia_año_actual = hoy.replace(month=1, day=1)
    primer_dia_año_anterior = primer_dia_año_actual.replace(year=hoy.year - 1)
    ultimo_dia_año_anterior = primer_dia_año_actual - timedelta(days=1)
    
    ganancias_año_actual = RegistroGanancia.objects.filter(
        fecha_transaccion__date__gte=primer_dia_año_actual,
        fecha_transaccion__date__lte=hoy
    ).aggregate(
        total=Sum('monto_total'),
        comisiones=Sum('monto_comision'),
        spread=Sum('monto_spread'),
        cantidad=Count('id')
    )
    
    ganancias_año_anterior = RegistroGanancia.objects.filter(
        fecha_transaccion__date__gte=primer_dia_año_anterior,
        fecha_transaccion__date__lte=ultimo_dia_año_anterior
    ).aggregate(
        total=Sum('monto_total'),
        comisiones=Sum('monto_comision'),
        spread=Sum('monto_spread'),
        cantidad=Count('id')
    )
    
    # Últimos 12 meses (comparación mensual)
    ultimos_12_meses = []
    for i in range(12):
        fecha_mes = hoy - timedelta(days=30 * i)
        año = fecha_mes.year
        mes = fecha_mes.month
        
        try:
            resumen = ResumenGananciaMensual.objects.get(año=año, mes=mes)
            ultimos_12_meses.append({
                'periodo': f"{mes:02d}/{año}",
                'total': resumen.total_general,
                'comisiones': resumen.total_comisiones,
                'spread': resumen.total_spread,
                'cantidad': resumen.cantidad_transacciones
            })
        except ResumenGananciaMensual.DoesNotExist:
            ultimos_12_meses.append({
                'periodo': f"{mes:02d}/{año}",
                'total': Decimal('0.00'),
                'comisiones': Decimal('0.00'),
                'spread': Decimal('0.00'),
                'cantidad': 0
            })
    
    ultimos_12_meses.reverse()
    
    context = {
        'ganancias_mes_actual': ganancias_mes_actual,
        'ganancias_mes_anterior': ganancias_mes_anterior,
        'ganancias_año_actual': ganancias_año_actual,
        'ganancias_año_anterior': ganancias_año_anterior,
        'ultimos_12_meses': ultimos_12_meses,
    }
    
    return render(request, 'ganancias/comparacion.html', context)


@login_required
@permission_required('ganancias.actualizar_ganancias', raise_exception=True)
def actualizar_ganancias(request):
    """
    Vista para actualizar los registros de ganancias y resúmenes
    """
    if request.method == 'POST':
        # Obtener todas las transacciones completadas sin registro de ganancia
        transacciones_completadas = Transaccion.objects.filter(
            estado='completado'
        ).exclude(
            ganancia__isnull=False
        )
        
        registros_creados = 0
        for transaccion in transacciones_completadas:
            registro = RegistroGanancia.calcular_ganancia_transaccion(transaccion)
            if registro:
                registros_creados += 1
        
        # Actualizar resúmenes diarios y mensuales
        fechas_actualizar = RegistroGanancia.objects.values_list(
            'fecha_transaccion__date', flat=True
        ).distinct()
        
        for fecha in fechas_actualizar:
            ResumenGananciaDiaria.actualizar_resumen(fecha)
            ResumenGananciaMensual.actualizar_resumen(fecha.year, fecha.month)
        
        return JsonResponse({
            'success': True,
            'message': f'Se crearon {registros_creados} registros de ganancia',
            'registros_creados': registros_creados
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)


@login_required
@permission_required('ganancias.export_ganancias', raise_exception=True)
def exportar_ganancias_excel(request):
    """
    Exporta las ganancias del período seleccionado a un archivo Excel
    """
    # Obtener parámetros de filtro (mismos que tablero_ganancias)
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    periodo = request.GET.get('periodo', 'mes_actual')
    divisa_id = request.GET.get('divisa')
    
    # Definir el rango de fechas
    hoy = timezone.now().date()
    
    if periodo == 'dia':
        fecha_inicio = hoy
        fecha_fin = hoy
    elif periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
        fecha_fin = hoy
    elif periodo == 'mes_actual':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
    elif periodo == 'mes_anterior':
        primer_dia_mes_actual = hoy.replace(day=1)
        ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
        fecha_inicio = ultimo_dia_mes_anterior.replace(day=1)
        fecha_fin = ultimo_dia_mes_anterior
    elif periodo == 'año':
        fecha_inicio = hoy.replace(month=1, day=1)
        fecha_fin = hoy
    elif periodo == 'todo':
        primera_ganancia = RegistroGanancia.objects.filter(
            transaccion__estado__in=['completado', 'pagada'],
            tipo_ganancia='spread'
        ).order_by('fecha_transaccion').first()
        
        if primera_ganancia:
            fecha_inicio = primera_ganancia.fecha_transaccion.date()
        else:
            fecha_inicio = hoy.replace(month=1, day=1)
        fecha_fin = hoy
    elif fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    else:
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
    
    # Obtener ganancias del período
    ganancias = RegistroGanancia.objects.filter(
        fecha_transaccion__date__gte=fecha_inicio,
        fecha_transaccion__date__lte=fecha_fin,
        transaccion__estado__in=['completado', 'pagada'],
        tipo_ganancia='spread'
    ).select_related(
        'transaccion',
        'transaccion__cliente',
        'divisa_referencia'
    ).order_by('-fecha_transaccion')
    
    if divisa_id:
        ganancias = ganancias.filter(divisa_referencia_id=divisa_id)
    
    # Crear libro de Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ganancias"
    
    # Estilos
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Título
    ws.merge_cells('A1:J1')
    title_cell = ws['A1']
    title_cell.value = f"Reporte de Ganancias - {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"
    title_cell.font = Font(bold=True, size=14)
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Encabezados
    headers = [
        'Fecha',
        'Nº Transacción',
        'Cliente',
        'Tipo Operación',
        'Divisa',
        'Monto Operación',
        'Tasa Aplicada',
        'Margen',
        'Ganancia (₲)',
        'Estado'
    ]
    
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border
    
    # Datos
    row = 4
    total_ganancia = Decimal('0.00')
    
    for ganancia in ganancias:
        ws.cell(row=row, column=1, value=ganancia.fecha_transaccion.strftime('%d/%m/%Y %H:%M'))
        ws.cell(row=row, column=2, value=ganancia.transaccion.numero_transaccion)
        ws.cell(row=row, column=3, value=ganancia.transaccion.cliente.nombre_completo)
        ws.cell(row=row, column=4, value=ganancia.transaccion.tipo_operacion.upper())
        ws.cell(row=row, column=5, value=ganancia.divisa_referencia.code)
        
        # Monto operación
        if ganancia.transaccion.tipo_operacion == 'compra':
            monto = ganancia.transaccion.monto_destino
        else:
            monto = ganancia.transaccion.monto_origen
        ws.cell(row=row, column=6, value=float(monto))
        
        ws.cell(row=row, column=7, value=float(ganancia.transaccion.tasa_de_cambio_aplicada))
        ws.cell(row=row, column=8, value=float(ganancia.transaccion.margen_spread or 0))
        ws.cell(row=row, column=9, value=float(ganancia.monto_spread))
        ws.cell(row=row, column=10, value=ganancia.transaccion.estado.upper())
        
        total_ganancia += ganancia.monto_spread
        
        # Aplicar bordes
        for col in range(1, 11):
            ws.cell(row=row, column=col).border = border
        
        row += 1
    
    # Fila de totales
    ws.cell(row=row, column=8, value="TOTAL:")
    ws.cell(row=row, column=8).font = Font(bold=True)
    ws.cell(row=row, column=9, value=float(total_ganancia))
    ws.cell(row=row, column=9).font = Font(bold=True)
    ws.cell(row=row, column=9).fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    
    # Ajustar anchos de columna
    ws.column_dimensions['A'].width = 18
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 12
    ws.column_dimensions['I'].width = 15
    ws.column_dimensions['J'].width = 12
    
    # Formato de números
    for r in range(4, row):
        ws.cell(row=r, column=6).number_format = '#,##0.00'
        ws.cell(row=r, column=7).number_format = '#,##0.00'
        ws.cell(row=r, column=8).number_format = '#,##0.00'
        ws.cell(row=r, column=9).number_format = '#,##0'
    
    ws.cell(row=row, column=9).number_format = '#,##0'
    
    # Preparar respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"ganancias_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response
