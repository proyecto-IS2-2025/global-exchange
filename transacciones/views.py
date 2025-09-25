from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import TransaccionForm
from .models import Transaccion
from clientes.models import Cliente, Segmento, AsignacionCliente # Importa los modelos necesarios
from divisas.models import Divisa, CotizacionSegmento # Importa los modelos de divisas y cotizaciones
from decimal import Decimal
import json
import datetime

@login_required
def iniciar_transaccion(request):
    """
    Vista que maneja el formulario para iniciar una nueva transacción.
    
    Si el método es GET, muestra el formulario.
    Si el método es POST, procesa los datos, calcula la transacción
    y redirige a la vista de previsualización.
    """
    if request.method == 'POST':
        form = TransaccionForm(request.POST)
        if form.is_valid():
            divisa_a_comprar_code = form.cleaned_data['divisa_a_comprar'].code
            monto_a_cambiar = form.cleaned_data['monto_a_cambiar']
            tipo_operacion = form.cleaned_data['tipo_operacion']

            # La divisa base es el Guaraní (PYG).
            divisa_base = get_object_or_404(Divisa, code='PYG')

            # Determinar divisa de origen y destino basado en el tipo de operación
            if tipo_operacion == 'compra': # El cliente COMPRA la divisa extranjera
                divisa_origen = divisa_base
                divisa_destino = get_object_or_404(Divisa, code=divisa_a_comprar_code)
                monto_origen = monto_a_cambiar
                moneda_code = divisa_a_comprar_code
            else: # El cliente VENDE la divisa extranjera
                divisa_origen = get_object_or_404(Divisa, code=divisa_a_comprar_code)
                divisa_destino = divisa_base
                monto_origen = monto_a_cambiar
                moneda_code = divisa_a_comprar_code
            
            try:
                # 1. Obtener el segmento del cliente (reutilizando lógica del simulador)
                segmento_obj = None
                cliente_id = request.session.get("cliente_id")
                if cliente_id:
                    try:
                        cliente_activo = Cliente.objects.get(id=cliente_id, esta_activo=True)
                        if cliente_activo.segmento:
                            segmento_obj = cliente_activo.segmento
                    except Cliente.DoesNotExist:
                        pass
                
                if not segmento_obj and request.user.is_authenticated:
                    from clientes.models import AsignacionCliente
                    asignacion = AsignacionCliente.objects.select_related("cliente__segmento").filter(usuario=request.user).first()
                    if asignacion and asignacion.cliente and asignacion.cliente.segmento:
                        segmento_obj = asignacion.cliente.segmento
                
                if not segmento_obj:
                    segmento_obj, _ = Segmento.objects.get_or_create(name="general")
                
                # 2. Obtener la divisa y la cotización más reciente
                divisa_obj = get_object_or_404(Divisa, code=moneda_code, is_active=True)
                cotizacion = CotizacionSegmento.objects.ultima_para(
                    divisa=divisa_obj,
                    segmento=segmento_obj
                )
                
                # Si no hay cotización para el segmento, usar una genérica
                if not cotizacion:
                    cotizaciones = CotizacionSegmento.objects.filter(divisa=divisa_obj).order_by('-fecha')[:1]
                    if cotizaciones:
                        cotizacion = cotizaciones[0]
                    else:
                        messages.error(request, f'No hay cotizaciones disponibles para la divisa {divisa_obj.code}.')
                        return redirect('iniciar_transaccion')

                # 3. Calcular el monto de destino y la tasa aplicada
                if tipo_operacion == 'compra':  # Cliente compra divisa (negocio vende)
                    tasa_aplicada = cotizacion.valor_venta_unit
                    monto_destino = monto_origen / tasa_aplicada
                else:  # Cliente vende divisa (negocio compra)
                    tasa_aplicada = cotizacion.valor_compra_unit
                    monto_destino = monto_origen * tasa_aplicada

                # Guardar los datos calculados en la sesión para la previsualización y confirmación
                request.session['transaccion_data'] = {
                    'divisa_origen_id': divisa_origen.id,
                    'divisa_destino_id': divisa_destino.id,
                    'monto_origen': str(monto_origen), # Guarda el valor convertido a string
                    'monto_destino': str(monto_destino), # Guarda el valor convertido a string
                    'tasa_de_cambio_aplicada': str(tasa_aplicada),
                }

                return redirect('previsualizar_transaccion')

            except Exception as e:
                messages.error(request, f"Error al procesar la transacción: {str(e)}")
                return redirect('iniciar_transaccion')
    
    else:
        form = TransaccionForm()
    
    return render(request, 'iniciar_transaccion.html', {'form': form})

@login_required
def previsualizar_transaccion(request):
    transaccion_data = request.session.get('transaccion_data')
    if not transaccion_data:
        messages.error(request, "No se encontraron datos de la transacción. Por favor, inicie una nueva.")
        return redirect('iniciar_transaccion')
    
    # Recuperar objetos de Divisa para mostrarlos en la plantilla
    divisa_origen = get_object_or_404(Divisa, id=transaccion_data['divisa_origen_id'])
    divisa_destino = get_object_or_404(Divisa, id=transaccion_data['divisa_destino_id'])

    context = {
        'divisa_origen': divisa_origen,
        'divisa_destino': divisa_destino,
        'monto_origen': transaccion_data['monto_origen'],
        'monto_destino': transaccion_data['monto_destino'],
        'tasa_de_cambio_aplicada': transaccion_data['tasa_de_cambio_aplicada']
    }
    return render(request, 'previsualizar_transaccion.html', context)

@login_required
def confirmar_transaccion(request):
    transaccion_data = request.session.get('transaccion_data')
    cliente_id = request.session.get('cliente_id')
    
    if not transaccion_data or not cliente_id:
        messages.error(request, "Datos de la transacción o cliente no encontrados. Por favor, reinicie.")
        return redirect('iniciar_transaccion')
    
    with transaction.atomic():
        try:
            # Obtiene el cliente activo directamente desde la sesión
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            messages.error(request, "El cliente activo seleccionado no es válido.")
            return redirect('iniciar_transaccion')

        # El resto de tu lógica para crear la transacción...
        nueva_transaccion = Transaccion(
            cliente=cliente,
            divisa_origen_id=transaccion_data['divisa_origen_id'],
            divisa_destino_id=transaccion_data['divisa_destino_id'],
            monto_origen=Decimal(transaccion_data['monto_origen']),
            monto_destino=Decimal(transaccion_data['monto_destino']),
            tasa_de_cambio_aplicada=Decimal(transaccion_data['tasa_de_cambio_aplicada']),
            estado=Transaccion.ESTADO_PENDIENTE
        )
        nueva_transaccion.save()
        
    del request.session['transaccion_data']
    messages.success(request, f"La transacción #{nueva_transaccion.id} ha sido creada con éxito. Estado: Pendiente")
    return redirect('transaccion_exitosa')

@login_required
def transaccion_exitosa(request):
    return render(request, 'transaccion_exitosa.html')

@login_required
def historial_transacciones(request):
    """
    Vista que muestra el historial de transacciones del cliente activo.
    """
    cliente_id = request.session.get('cliente_id')
    
    if not cliente_id:
        messages.warning(request, "No se encontró un cliente activo. Por favor, seleccione uno.")
        return redirect('iniciar_transaccion') # Redirecciona a la vista que elija un cliente
        
    try:
        cliente_activo = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        messages.error(request, "El cliente activo seleccionado no es válido.")
        return redirect('iniciar_transaccion')

    transacciones = Transaccion.objects.filter(
        cliente=cliente_activo
    ).order_by('-fecha_creacion').select_related('divisa_origen', 'divisa_destino')
    
    context = {
        'cliente_activo': cliente_activo,
        'transacciones': transacciones
    }
    return render(request, 'historial_transacciones.html', context)

@login_required
def historial_admin(request):
    """
    Vista para que el administrador vea y filtre todas las transacciones.
    """
    # Asegura que solo los administradores puedan acceder a esta vista
    if not request.user.is_superuser: # o cualquier otro grupo que defina a un admin
        return redirect('inicio') # o una página de acceso denegado

    transacciones = Transaccion.objects.all().order_by('-fecha_creacion')
    clientes = Cliente.objects.all().order_by('nombre_completo')

    # Lógica de filtrado
    cliente_id = request.GET.get('cliente_id')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if cliente_id:
        transacciones = transacciones.filter(cliente_id=cliente_id)

    if fecha_inicio:
        transacciones = transacciones.filter(fecha_creacion__gte=fecha_inicio)
    
    if fecha_fin:
        # Añade 1 día a la fecha fin para incluir transacciones de todo el día
        end_date = datetime.datetime.strptime(fecha_fin, '%Y-%m-%d').date() + datetime.timedelta(days=1)
        transacciones = transacciones.filter(fecha_creacion__lt=end_date)
    
    context = {
        'transacciones': transacciones,
        'clientes': clientes,
        'selected_cliente_id': cliente_id,
        'selected_fecha_inicio': fecha_inicio,
        'selected_fecha_fin': fecha_fin,
    }
    
    return render(request, 'historial_admin.html', context)
