"""
Servicio para cálculo y manejo de denominaciones en operaciones TAUSER.
"""
from decimal import Decimal
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


def calcular_desglose_optimo(inventarios_disponibles, monto_total):
    """
    Calcula el desglose óptimo de denominaciones para un monto dado.
    
    Usa algoritmo greedy (billetes más grandes primero).
    
    :param inventarios_disponibles: QuerySet de InventarioDenominacionTerminal
    :param monto_total: Decimal con el monto a desglosar
    :return: dict con 'posible', 'desglose', 'sobrante'
    """
    monto_pendiente = Decimal(str(monto_total))
    desglose = {}
    
    # Ordenar por valor descendente (billetes grandes primero)
    inventarios = sorted(
        inventarios_disponibles,
        key=lambda x: x.denominacion.valor,
        reverse=True
    )
    
    for inventario in inventarios:
        if monto_pendiente <= 0:
            break
        
        valor_billete = inventario.denominacion.valor
        cantidad_disponible = inventario.cantidad
        
        # Calcular cuántos billetes de esta denominación se necesitan
        cantidad_necesaria = int(monto_pendiente / valor_billete)
        
        if cantidad_necesaria > 0:
            # Usar la menor cantidad entre necesaria y disponible
            cantidad_a_usar = min(cantidad_necesaria, cantidad_disponible)
            
            if cantidad_a_usar > 0:
                desglose[inventario.id] = {
                    'inventario': inventario,
                    'cantidad': cantidad_a_usar,
                    'valor_unitario': valor_billete,
                    'subtotal': valor_billete * cantidad_a_usar
                }
                
                monto_pendiente -= (valor_billete * cantidad_a_usar)
    
    # Verificar si se pudo cubrir el monto exacto
    posible = (monto_pendiente == 0)
    
    resultado = {
        'posible': posible,
        'desglose': desglose,
        'sobrante': monto_pendiente,
        'monto_cubierto': monto_total - monto_pendiente
    }
    
    if not posible:
        logger.warning(
            f"No se pudo cubrir monto completo. "
            f"Solicitado: {monto_total}, Cubierto: {resultado['monto_cubierto']}, "
            f"Faltante: {monto_pendiente}"
        )
    
    return resultado


def validar_desglose_cliente(desglose_cliente: Dict[int, int], monto_esperado: Decimal) -> Tuple[bool, str, Decimal]:
    """
    Valida que el desglose ingresado por el cliente sume el monto esperado.
    
    :param desglose_cliente: dict {denominacion_id: cantidad}
    :param monto_esperado: Decimal con el monto que debe sumar
    :return: (es_valido, mensaje_error, monto_calculado)
    """
    from divisas.models import Denominacion
    
    monto_total = Decimal('0')
    
    for denom_id, cantidad in desglose_cliente.items():
        if cantidad <= 0:
            continue
        
        try:
            denominacion = Denominacion.objects.get(id=denom_id, is_active=True)
            monto_total += denominacion.valor * cantidad
        except Denominacion.DoesNotExist:
            return False, f"Denominación inválida: {denom_id}", Decimal('0')
    
    if monto_total != monto_esperado:
        return False, (
            f"El desglose no coincide con el monto esperado. "
            f"Esperado: {monto_esperado}, Recibido: {monto_total}"
        ), monto_total
    
    return True, "Desglose válido", monto_total


def generar_resumen_desglose(desglose: Dict) -> List[Dict]:
    """
    Genera un resumen legible del desglose de denominaciones.
    
    :param desglose: dict retornado por calcular_desglose_optimo
    :return: lista de dicts con información formateada
    """
    resumen = []
    
    for datos in desglose.values():
        inventario = datos['inventario']
        resumen.append({
            'denominacion': inventario.denominacion,
            'valor_formateado': inventario.denominacion.valor_formateado,
            'cantidad': datos['cantidad'],
            'subtotal': datos['subtotal'],
            'subtotal_formateado': f"{inventario.denominacion.divisa.simbolo}{datos['subtotal']:,.2f}"
        })
    
    return resumen