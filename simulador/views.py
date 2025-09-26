#simulador
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from divisas.models import Divisa, TasaCambio, CotizacionSegmento
from clientes.models import AsignacionCliente, Segmento, Cliente  # ### CAMBIO: import Cliente
from django.db.models import ObjectDoesNotExist
from .context_processors import simulador_context as get_simulador_context
from django.core.serializers.json import DjangoJSONEncoder


def simulador_view(request):
    """
    Renderiza la plantilla principal del simulador de divisas.

    Esta vista prepara el contexto necesario para la plantilla,
    incluyendo una lista de divisas disponibles para la simulación.

    :param request: El objeto HttpRequest.
    :type request: django.http.HttpRequest
    :return: Un objeto HttpResponse que renderiza la plantilla del simulador.
    :rtype: django.http.HttpResponse
    """
    context = get_simulador_context(request)
    return render(request, 'simulador/simulador.html', context)


@csrf_exempt
@require_POST
def calcular_simulacion_api(request):
    """
    API endpoint para calcular una simulación de cambio de divisas.

    Procesa una solicitud POST con los detalles de una operación de cambio
    (tipo, monto y moneda) y devuelve un resultado calculado en formato JSON.

    Flujo de cálculo:
    1. Deserializa los datos JSON de la solicitud.
    2. Valida la operación, prohibiendo el uso del Guaraní (PYG).
    3. Determina el segmento del cliente basado en la sesión, la asignación de usuario
       o, por defecto, el segmento 'general'.
    4. Obtiene la cotización de la divisa más reciente para el segmento del cliente.
    5. Realiza el cálculo de la conversión y la comisión ajustada según el tipo de operación.
    6. Formatea el resultado en un diccionario JSON y lo devuelve como respuesta.

    :param request: El objeto HttpRequest con datos JSON en el cuerpo.
    :type request: django.http.HttpRequest
    :return: Un objeto JsonResponse con el resultado de la simulación o un error.
    :rtype: django.http.JsonResponse
    :raises json.JSONDecodeError: Si el cuerpo de la solicitud no es un JSON válido.
    :raises Divisa.DoesNotExist: Si la divisa especificada no se encuentra o está inactiva.
    :raises ObjectDoesNotExist: Si el segmento 'general' no existe en la base de datos.
    :raises Exception: Para manejar cualquier otro error inesperado.
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

        # 1. Obtener el segmento desde cliente activo en sesión
        segmento_obj = None
        cliente_id = request.session.get("cliente_id")

        if cliente_id:
            try:
                cliente_activo = Cliente.objects.get(id=cliente_id, esta_activo=True)
                if cliente_activo.segmento:
                    segmento_obj = cliente_activo.segmento
                    print(f"Usando segmento desde cliente activo: {segmento_obj.name}")
            except Cliente.DoesNotExist:
                pass

        # 2. Si no hay cliente en sesión, tomar primera asignación como fallback
        if not segmento_obj and request.user.is_authenticated:
            asignacion = AsignacionCliente.objects.select_related("cliente__segmento").filter(
                usuario=request.user).first()
            if asignacion and asignacion.cliente and asignacion.cliente.segmento:
                segmento_obj = asignacion.cliente.segmento
                print(f"Usando segmento de asignación: {segmento_obj.name}")

        # 3. Si aún no hay segmento, usar 'general'
        if not segmento_obj:
            try:
                segmento_obj, _ = Segmento.objects.get_or_create(name="general")
                print(f"Usando segmento por defecto: {segmento_obj.name}")
            except ObjectDoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Segmento "general" no encontrado. Favor, crear el segmento.'
                }, status=500)

        # 4. Obtener la divisa
        try:
            divisa_obj = Divisa.objects.get(code=moneda_code, is_active=True)
            print(f"Divisa encontrada: {divisa_obj.code} - {divisa_obj.nombre}")
        except Divisa.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Divisa {moneda_code} no encontrada o no activa.'
            }, status=404)

        # 5. Obtener la cotización más reciente para la divisa y el segmento
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
                print(
                    f"Usando cotización general para {divisa_obj.code} ya que no hay para el segmento {segmento_obj.name}")
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

        # 6. Formatear y devolver la respuesta JSON usando DjangoJSONEncoder
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
