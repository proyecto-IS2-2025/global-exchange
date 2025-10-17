from decimal import Decimal, ROUND_DOWN, ROUND_UP
from divisas.models import Denominacion
import logging

logger = logging.getLogger(__name__)


def obtener_denominaciones_disponibles(divisa):
    """
    Obtiene las denominaciones activas de una divisa, ordenadas de mayor a menor.
    
    Args:
        divisa: Objeto Divisa
        
    Returns:
        QuerySet de Denominacion ordenado por valor descendente
    """
    return Denominacion.objects.filter(
        divisa=divisa,
        is_active=True
    ).order_by('-valor')


def ajustar_monto_a_denominaciones(monto, divisa, tipo_operacion='compra'):
    """
    Ajusta un monto para que pueda ser entregado con las denominaciones disponibles.
    
    Args:
        monto: Decimal - Monto a ajustar
        divisa: Objeto Divisa - Divisa del monto
        tipo_operacion: str - 'compra' (redondea hacia abajo) o 'venta' (redondea hacia arriba)
        
    Returns:
        tuple: (monto_ajustado, denominaciones_usadas)
        - monto_ajustado: Decimal - Monto redondeado que se puede entregar
        - denominaciones_usadas: list - Lista de tuplas (denominacion, cantidad)
    """
    try:
        # Si es PYG, no ajustar (se transfiere digitalmente)
        if divisa.code.upper() in ['PYG', '116']:
            logger.debug(f"[AJUSTE_DENOM] Divisa {divisa.code} es PYG, no se ajusta")
            return monto, []
        
        denominaciones = obtener_denominaciones_disponibles(divisa)
        
        if not denominaciones.exists():
            logger.warning(f"[AJUSTE_DENOM] No hay denominaciones para {divisa.code}, retornando monto original")
            return monto, []
        
        # Obtener la denominación más pequeña
        denominacion_minima = denominaciones.last()
        valor_minimo = denominacion_minima.valor
        
        logger.debug(f"[AJUSTE_DENOM] Ajustando {monto} {divisa.code}, denom_min={valor_minimo}")
        
        # Determinar dirección de redondeo
        if tipo_operacion == 'compra':
            # En compra: redondear HACIA ABAJO (cliente recibe menos o igual)
            # Esto asegura que siempre podamos entregar con billetes exactos
            monto_ajustado = (monto // valor_minimo) * valor_minimo
            logger.debug(f"[AJUSTE_DENOM] Compra: {monto} → {monto_ajustado} (hacia abajo)")
        else:
            # En venta: redondear HACIA ARRIBA (cliente entrega más o igual)
            # Esto asegura que el cliente nos entregue billetes completos
            if monto % valor_minimo == 0:
                monto_ajustado = monto
            else:
                monto_ajustado = ((monto // valor_minimo) + 1) * valor_minimo
            logger.debug(f"[AJUSTE_DENOM] Venta: {monto} → {monto_ajustado} (hacia arriba)")
        
        # Calcular desglose de denominaciones (algoritmo greedy)
        denominaciones_usadas = []
        monto_restante = monto_ajustado
        
        for denom in denominaciones:
            if monto_restante <= 0:
                break
            
            cantidad = int(monto_restante // denom.valor)
            if cantidad > 0:
                denominaciones_usadas.append((denom, cantidad))
                monto_restante -= (denom.valor * cantidad)
                logger.debug(f"[AJUSTE_DENOM] Usando {cantidad}x {denom.nombre}")
        
        if monto_restante > 0:
            logger.warning(f"[AJUSTE_DENOM] Resto no cubierto: {monto_restante} {divisa.code}")
        
        logger.info(f"[AJUSTE_DENOM] Ajuste final: {monto} → {monto_ajustado} {divisa.code}")
        
        return monto_ajustado, denominaciones_usadas
        
    except Exception as e:
        logger.error(f"[AJUSTE_DENOM] Error al ajustar monto: {e}", exc_info=True)
        return monto, []


def calcular_conversion_ajustada(monto_entrada, divisa_entrada, divisa_salida, tasa_cambio, tipo_operacion='compra'):
    """
    Calcula la conversión entre divisas ajustando el resultado a las denominaciones disponibles.
    
    Args:
        monto_entrada: Decimal - Monto a convertir
        divisa_entrada: Divisa - Divisa de origen
        divisa_salida: Divisa - Divisa de destino
        tasa_cambio: Decimal - Tasa de cambio a aplicar
        tipo_operacion: str - 'compra' o 'venta'
        
    Returns:
        dict: {
            'monto_calculado': Decimal - Monto calculado sin ajustar,
            'monto_ajustado': Decimal - Monto ajustado a denominaciones,
            'monto_entrada_ajustado': Decimal - Monto entrada recalculado (si fue necesario),
            'tasa_efectiva': Decimal - Tasa efectiva aplicada después del ajuste,
            'denominaciones': list - Denominaciones para entregar,
            'fue_ajustado': bool - Si se realizó ajuste
        }
    """
    try:
        # Cálculo inicial
        if tipo_operacion == 'compra':
            # Compra: cliente paga PYG, recibe divisa extranjera
            # monto_entrada = PYG, monto_salida = divisa extranjera
            monto_calculado = monto_entrada / tasa_cambio
        else:
            # Venta: cliente entrega divisa extranjera, recibe PYG
            # monto_entrada = divisa extranjera, monto_salida = PYG
            monto_calculado = monto_entrada * tasa_cambio
        
        logger.debug(f"[CALC_CONV] {tipo_operacion.upper()}: {monto_entrada} {divisa_entrada.code} = {monto_calculado} {divisa_salida.code} (tasa={tasa_cambio})")
        
        # Ajustar el monto de salida a las denominaciones
        monto_ajustado, denominaciones = ajustar_monto_a_denominaciones(
            monto_calculado,
            divisa_salida,
            tipo_operacion
        )
        
        fue_ajustado = (monto_calculado != monto_ajustado)
        
        # Recalcular el monto de entrada si hubo ajuste
        if fue_ajustado:
            if tipo_operacion == 'compra':
                # Recalcular cuánto debe pagar en PYG para recibir el monto ajustado
                monto_entrada_ajustado = monto_ajustado * tasa_cambio
            else:
                # Recalcular cuánto debe entregar en divisa para recibir el monto ajustado en PYG
                monto_entrada_ajustado = monto_ajustado / tasa_cambio
            
            # Calcular tasa efectiva
            if tipo_operacion == 'compra':
                tasa_efectiva = monto_entrada_ajustado / monto_ajustado if monto_ajustado > 0 else tasa_cambio
            else:
                tasa_efectiva = monto_ajustado / monto_entrada_ajustado if monto_entrada_ajustado > 0 else tasa_cambio
            
            logger.info(f"[CALC_CONV] AJUSTADO: Entrada {monto_entrada} → {monto_entrada_ajustado}, Salida {monto_calculado} → {monto_ajustado}, Tasa efectiva={tasa_efectiva}")
        else:
            monto_entrada_ajustado = monto_entrada
            tasa_efectiva = tasa_cambio
        
        # Redondear según la divisa
        decimales_entrada = 0 if divisa_entrada.code.upper() == 'PYG' else 2
        decimales_salida = 0 if divisa_salida.code.upper() == 'PYG' else 2
        
        from decimal import ROUND_HALF_UP
        
        monto_calculado = Decimal(monto_calculado).quantize(
            Decimal("1") if decimales_salida == 0 else Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
        
        monto_ajustado = Decimal(monto_ajustado).quantize(
            Decimal("1") if decimales_salida == 0 else Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
        
        monto_entrada_ajustado = Decimal(monto_entrada_ajustado).quantize(
            Decimal("1") if decimales_entrada == 0 else Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
        
        tasa_efectiva = Decimal(tasa_efectiva).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
        
        return {
            'monto_calculado': monto_calculado,
            'monto_ajustado': monto_ajustado,
            'monto_entrada_ajustado': monto_entrada_ajustado,
            'tasa_efectiva': tasa_efectiva,
            'denominaciones': denominaciones,
            'fue_ajustado': fue_ajustado,
        }
        
    except Exception as e:
        logger.error(f"[CALC_CONV] Error en cálculo de conversión: {e}", exc_info=True)
        return {
            'monto_calculado': Decimal('0'),
            'monto_ajustado': Decimal('0'),
            'monto_entrada_ajustado': monto_entrada,
            'tasa_efectiva': tasa_cambio,
            'denominaciones': [],
            'fue_ajustado': False,
        }


def formatear_denominaciones(denominaciones_usadas):
    """
    Formatea la lista de denominaciones para mostrar en la UI.
    
    Args:
        denominaciones_usadas: list de tuplas (Denominacion, cantidad)
        
    Returns:
        list de dict con información formateada
    """
    resultado = []
    for denom, cantidad in denominaciones_usadas:
        resultado.append({
            'nombre': denom.nombre,
            'valor': float(denom.valor),
            'cantidad': cantidad,
            'subtotal': float(denom.valor * cantidad),
            'simbolo': denom.divisa.simbolo,
        })
    return resultado