# simulador/context_processors.py
import json
from decimal import Decimal
from divisas.models import Divisa, CotizacionSegmento
from clientes.models import Cliente as ClienteModel, AsignacionCliente, Descuento
from django.db.models import F, OuterRef, Subquery, Max

def simulador_context(request):
    """
    Context processor que provee tasas, lista de divisas y descuentos por segmento.
    Excluye la divisa Guaraní (PYG) del listado.
    """
    segmento_usuario = ''  # Asignación por defecto
    if request.user.is_authenticated:
        try:
            # Usar AsignacionCliente directamente como en la vista
            asignacion = AsignacionCliente.objects.select_related('cliente__segmento').filter(usuario=request.user).first()
            if asignacion and asignacion.cliente and asignacion.cliente.segmento:
                segmento_usuario = asignacion.cliente.segmento.name
        except AsignacionCliente.DoesNotExist:
            pass

    # Obtener la lista de divisas activas para el frontend, excluyendo el Guaraní (código 116)
    divisas_activas = Divisa.objects.filter(is_active=True).exclude(code='116')
    divisas_list = [
        {'code': d.code, 'nombre': d.nombre, 'simbolo': d.simbolo} 
        for d in divisas_activas
    ]
    
    # Obtener las cotizaciones más recientes para cada segmento y divisa
    tasas_data = {}
    
    # Primero obtener todos los segmentos
    from clientes.models import Segmento
    segmentos = Segmento.objects.all()
    
    for segmento in segmentos:
        segmento_key = segmento.name.lower()
        tasas_data[segmento_key] = {}
        
        for divisa in divisas_activas:  # Usar divisas_activas que ya excluye el Guaraní
            # Obtener la última cotización para esta divisa y segmento
            cotizacion = CotizacionSegmento.objects.filter(
                divisa=divisa, 
                segmento=segmento
            ).order_by('-fecha').first()
            
            if cotizacion:
                tasas_data[segmento_key][divisa.code] = {
                    'valor_compra': float(cotizacion.valor_compra_unit),
                    'valor_venta': float(cotizacion.valor_venta_unit),
                    'precio_base': float(cotizacion.precio_base),
                    'porcentaje_descuento': float(cotizacion.porcentaje_descuento),
                    'comision_compra': float(cotizacion.comision_compra_ajustada),
                    'comision_venta': float(cotizacion.comision_venta_ajustada)
                }

    # Convertir datos a JSON para inyectarlos en el HTML
    tasas_data_json = json.dumps(tasas_data)
    divisas_list_json = json.dumps(divisas_list)

    return {
        'segmento_usuario': segmento_usuario,
        'tasas_data': tasas_data,
        'divisas_list': divisas_list,
        'tasas_data_json': tasas_data_json,
        'divisas_list_json': divisas_list_json,
    }
