# simulador/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from divisas.models import Divisa, TasaCambio, CotizacionSegmento
from clientes.models import AsignacionCliente, Segmento 
from django.db.models import ObjectDoesNotExist
from .context_processors import simulador_context as get_simulador_context
from django.core.serializers.json import DjangoJSONEncoder

def simulador_view(request):
    """
    Renderiza la plantilla del simulador y pasa el contexto necesario.
    """
    context = get_simulador_context(request)
    return render(request, 'simulador/simulador.html', context)

@csrf_exempt
@require_POST
def calcular_simulacion_api(request):
    """
    Vista que recibe los datos y realiza el cálculo de la simulación.
    Devuelve un objeto JSON con el resultado.
    """
    try:
        data = json.loads(request.body)
        tipo_operacion = data.get('tipo_operacion')
        monto = Decimal(str(data.get('monto')))
        moneda_code = data.get('moneda')
        
        # Restricción: No permitir operaciones con Guaraní (código 116)
        if moneda_code == 'PYG':
            return JsonResponse({
                'success': False, 
                'error': 'No se permiten operaciones con Guaraní (PYG) en el simulador.'
            }, status=400)
        
        # 1. Obtener el segmento del usuario
        segmento_obj = None
        if request.user.is_authenticated:
            try:
                asignacion = AsignacionCliente.objects.select_related(
                    'cliente__segmento').filter(usuario=request.user).first()
                if asignacion and asignacion.cliente and asignacion.cliente.segmento:
                    segmento_obj = asignacion.cliente.segmento
                    print(f"Usuario {request.user} tiene segmento: {segmento_obj.name}")
            except AsignacionCliente.DoesNotExist:
                print(f"Usuario {request.user} no tiene asignación de cliente")
                pass
        
        # Si no hay segmento de usuario, usamos el "Minorista" por defecto
        if not segmento_obj:
            try:
                segmento_obj = Segmento.objects.get(name='Minorista')
                print(f"Usando segmento por defecto: {segmento_obj.name}")
            except ObjectDoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Segmento "Minorista" no encontrado. Favor, crear el segmento.'
                }, status=500)

        # 2. Obtener la divisa
        try:
            divisa_obj = Divisa.objects.get(code=moneda_code, is_active=True)
            print(f"Divisa encontrada: {divisa_obj.code} - {divisa_obj.nombre}")
        except Divisa.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': f'Divisa {moneda_code} no encontrada o no activa.'
            }, status=404)

        # 3. Obtener la cotización más reciente para la divisa y el segmento
        cotizacion = CotizacionSegmento.objects.ultima_para(
            divisa=divisa_obj,
            segmento=segmento_obj
        )

        if not cotizacion:
            # Intentar obtener cualquier cotización para la divisa
            cotizaciones = CotizacionSegmento.objects.filter(
                divisa=divisa_obj
            ).order_by('-fecha')[:1]
            
            if cotizaciones:
                cotizacion = cotizaciones[0]
                print(f"Usando cotización general para {divisa_obj.code} ya que no hay para el segmento {segmento_obj.name}")
            else:
                return JsonResponse({
                    'success': False, 
                    'error': f'No hay cotizaciones disponibles para la divisa {divisa_obj.code}.'
                }, status=404)
        
        print(f"Cotización encontrada: {cotizacion}")
        print(f"Valor compra: {cotizacion.valor_compra_unit}, Valor venta: {cotizacion.valor_venta_unit}")
        print(f"Descuento aplicado: {cotizacion.porcentaje_descuento}%")

        resultado = Decimal('0.00')
        tasa_aplicada = Decimal('0.00')
        comision_aplicada = Decimal('0.00')

        if tipo_operacion == 'compra':  # Cliente compra divisa (negocio vende)
            tasa_aplicada = cotizacion.valor_venta_unit
            resultado = monto / tasa_aplicada  # Monto en Gs → Divisa extranjera
            comision_aplicada = cotizacion.comision_venta_ajustada
        else:  # venta - Cliente vende divisa (negocio compra)
            tasa_aplicada = cotizacion.valor_compra_unit
            resultado = monto * tasa_aplicada  # Divisa extranjera → Gs
            comision_aplicada = cotizacion.comision_compra_ajustada
        
        # 5. Formatear y devolver la respuesta JSON usando DjangoJSONEncoder
        return JsonResponse({
            'success': True,
            'segmento': segmento_obj.name,
            'monto_original': monto,
            'monto_resultado': resultado,
            'tasa_aplicada': tasa_aplicada,
            'comision_aplicada': comision_aplicada,
            'porcentaje_descuento': cotizacion.porcentaje_descuento,
            'moneda_code': moneda_code,
            'moneda_simbolo': cotizacion.divisa.simbolo,
            'moneda_nombre': cotizacion.divisa.nombre
        }, encoder=DjangoJSONEncoder)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Formato JSON inválido.'}, status=400)
    except (Divisa.DoesNotExist, ObjectDoesNotExist) as e:
        return JsonResponse({'success': False, 'error': f'Error en la base de datos: {str(e)}'}, status=404)
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'}, status=500)