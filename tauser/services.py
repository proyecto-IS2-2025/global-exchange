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
    
    Usa algoritmo greedy (billetes más grandes primero) como primera opción.
    Si greedy falla, intenta con backtracking para búsqueda exhaustiva.
    
    :param inventarios_disponibles: QuerySet de InventarioDenominacionTerminal
    :param monto_total: Decimal con el monto a desglosar
    :return: dict con 'posible', 'desglose', 'sobrante', 'algoritmo_usado'
    """
    monto_total = Decimal(str(monto_total))
    
    # Ordenar por valor descendente (billetes grandes primero)
    inventarios = sorted(
        inventarios_disponibles,
        key=lambda x: x.denominacion.valor,
        reverse=True
    )
    
    # ==================== INTENTO 1: ALGORITMO GREEDY ====================
    resultado_greedy = _calcular_desglose_greedy(inventarios, monto_total)
    
    if resultado_greedy['posible']:
        resultado_greedy['algoritmo_usado'] = 'greedy'
        logger.info(f"Desglose exitoso con algoritmo greedy para monto {monto_total}")
        return resultado_greedy
    
    # ==================== INTENTO 2: BACKTRACKING ====================
    logger.info(f"Greedy falló para monto {monto_total}. Intentando con backtracking...")
    resultado_backtracking = _calcular_desglose_backtracking(inventarios, monto_total)
    
    if resultado_backtracking['posible']:
        resultado_backtracking['algoritmo_usado'] = 'backtracking'
        logger.info(f"Desglose exitoso con backtracking para monto {monto_total}")
        return resultado_backtracking
    
    # ==================== NINGUNO FUNCIONÓ ====================
    logger.warning(
        f"No se pudo cubrir monto completo con ningún algoritmo. "
        f"Solicitado: {monto_total}, Mejor intento (greedy): {resultado_greedy['monto_cubierto']}, "
        f"Faltante: {resultado_greedy['sobrante']}"
    )
    
    # Retornar el mejor resultado (greedy tiene más billetes grandes, es más eficiente)
    resultado_greedy['algoritmo_usado'] = 'greedy_parcial'
    return resultado_greedy


def _calcular_desglose_greedy(inventarios, monto_total):
    """
    Algoritmo greedy: usa billetes más grandes primero.
    Rápido pero puede fallar en casos donde existe solución exacta con combinaciones.
    """
    monto_pendiente = Decimal(str(monto_total))
    desglose = {}
    
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
    
    posible = (monto_pendiente == 0)
    
    return {
        'posible': posible,
        'desglose': desglose,
        'sobrante': monto_pendiente,
        'monto_cubierto': monto_total - monto_pendiente
    }


def _calcular_desglose_backtracking(inventarios, monto_total):
    """
    Algoritmo con backtracking: búsqueda exhaustiva de todas las combinaciones.
    Más lento pero garantiza encontrar solución si existe.
    
    Usa programación dinámica optimizada para limitar búsqueda.
    """
    monto_total = Decimal(str(monto_total))
    mejor_solucion = None
    
    def backtrack(indice, monto_restante, desglose_actual, billetes_usados):
        nonlocal mejor_solucion
        
        # Caso base: monto exacto
        if monto_restante == 0:
            # Encontramos solución exacta
            if mejor_solucion is None or billetes_usados < mejor_solucion['total_billetes']:
                mejor_solucion = {
                    'desglose': dict(desglose_actual),
                    'total_billetes': billetes_usados
                }
            return True
        
        # Caso base: monto negativo o sin más denominaciones
        if monto_restante < 0 or indice >= len(inventarios):
            return False
        
        # Poda: si ya tenemos una solución y usamos demasiados billetes, no seguir
        if mejor_solucion and billetes_usados >= mejor_solucion['total_billetes']:
            return False
        
        inventario = inventarios[indice]
        valor_billete = inventario.denominacion.valor
        cantidad_disponible = inventario.cantidad
        
        # Calcular cantidad máxima posible de esta denominación
        max_cantidad = min(
            cantidad_disponible,
            int(monto_restante / valor_billete) + 1  # +1 por si acaso
        )
        
        # Probar desde usar la máxima cantidad hasta no usar ninguna
        # (empezar por más billetes aumenta chance de encontrar solución rápido)
        for cantidad in range(max_cantidad, -1, -1):
            if cantidad > 0:
                desglose_actual[inventario.id] = {
                    'inventario': inventario,
                    'cantidad': cantidad,
                    'valor_unitario': valor_billete,
                    'subtotal': valor_billete * cantidad
                }
            
            nuevo_monto = monto_restante - (valor_billete * cantidad)
            
            # Recursión con siguiente denominación
            if backtrack(indice + 1, nuevo_monto, desglose_actual, billetes_usados + cantidad):
                return True  # Encontramos solución exacta
            
            # Backtrack: deshacer cambio
            if cantidad > 0:
                del desglose_actual[inventario.id]
        
        return False
    
    # Iniciar búsqueda
    backtrack(0, monto_total, {}, 0)
    
    if mejor_solucion:
        return {
            'posible': True,
            'desglose': mejor_solucion['desglose'],
            'sobrante': Decimal('0'),
            'monto_cubierto': monto_total
        }
    else:
        return {
            'posible': False,
            'desglose': {},
            'sobrante': monto_total,
            'monto_cubierto': Decimal('0')
        }


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