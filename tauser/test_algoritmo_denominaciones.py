"""
Script de prueba para el algoritmo de denominaciones con backtracking.
Ejecutar con: python manage.py shell < tauser/test_algoritmo_denominaciones.py
"""
from decimal import Decimal
from tauser.services import calcular_desglose_optimo

# Mock de inventarios para pruebas
class MockInventario:
    def __init__(self, id, valor, cantidad, codigo):
        self.id = id
        self.cantidad = cantidad
        self.denominacion = type('obj', (object,), {
            'valor': Decimal(str(valor)),
            'divisa': type('obj', (object,), {'simbolo': '$'})()
        })()
        self.codigo = codigo

print("\n" + "="*60)
print("PRUEBAS DEL ALGORITMO DE DENOMINACIONES")
print("="*60)

# ==================== TEST 1: Caso simple (greedy funciona) ====================
print("\n[TEST 1] Caso simple - Greedy debería funcionar")
print("-" * 60)
inventarios1 = [
    MockInventario(1, 100, 5, "USD-100"),
    MockInventario(2, 50, 10, "USD-50"),
    MockInventario(3, 20, 20, "USD-20"),
    MockInventario(4, 10, 30, "USD-10"),
    MockInventario(5, 5, 40, "USD-5"),
]
monto1 = Decimal('275')  # 2x100 + 1x50 + 1x20 + 1x5
resultado1 = calcular_desglose_optimo(inventarios1, monto1)
print(f"Monto solicitado: ${monto1}")
print(f"¿Posible?: {resultado1['posible']}")
print(f"Algoritmo usado: {resultado1.get('algoritmo_usado', 'N/A')}")
print(f"Desglose:")
for datos in resultado1['desglose'].values():
    print(f"  - {datos['cantidad']}x ${datos['valor_unitario']} = ${datos['subtotal']}")
print(f"Sobrante: ${resultado1['sobrante']}")
assert resultado1['posible'], "❌ Test 1 falló: debería ser posible"
print("✅ Test 1 PASADO")

# ==================== TEST 2: Caso donde greedy falla pero backtracking funciona ====================
print("\n[TEST 2] Caso donde greedy falla - Backtracking debería funcionar")
print("-" * 60)
inventarios2 = [
    MockInventario(1, 30, 1, "USD-30"),  # Si greedy usa este, queda 10 sin poder cubrirse
    MockInventario(2, 20, 2, "USD-20"),  # Solución correcta: 2x20
]
monto2 = Decimal('40')
resultado2 = calcular_desglose_optimo(inventarios2, monto2)
print(f"Monto solicitado: ${monto2}")
print(f"¿Posible?: {resultado2['posible']}")
print(f"Algoritmo usado: {resultado2.get('algoritmo_usado', 'N/A')}")
print(f"Desglose:")
for datos in resultado2['desglose'].values():
    print(f"  - {datos['cantidad']}x ${datos['valor_unitario']} = ${datos['subtotal']}")
print(f"Sobrante: ${resultado2['sobrante']}")
assert resultado2['posible'], "❌ Test 2 falló: backtracking debería encontrar solución"
assert resultado2.get('algoritmo_usado') == 'backtracking', "❌ Test 2: debería usar backtracking"
print("✅ Test 2 PASADO")

# ==================== TEST 3: Caso imposible ====================
print("\n[TEST 3] Caso imposible - Ningún algoritmo debería funcionar")
print("-" * 60)
inventarios3 = [
    MockInventario(1, 50, 2, "USD-50"),
    MockInventario(2, 20, 1, "USD-20"),
]
monto3 = Decimal('35')  # No se puede formar con 50s y 20s
resultado3 = calcular_desglose_optimo(inventarios3, monto3)
print(f"Monto solicitado: ${monto3}")
print(f"¿Posible?: {resultado3['posible']}")
print(f"Algoritmo usado: {resultado3.get('algoritmo_usado', 'N/A')}")
print(f"Mejor intento cubrió: ${resultado3['monto_cubierto']}")
print(f"Sobrante: ${resultado3['sobrante']}")
assert not resultado3['posible'], "❌ Test 3 falló: no debería ser posible"
print("✅ Test 3 PASADO")

# ==================== TEST 4: Caso complejo con múltiples denominaciones ====================
print("\n[TEST 4] Caso complejo - Backtracking con múltiples opciones")
print("-" * 60)
inventarios4 = [
    MockInventario(1, 25, 3, "USD-25"),
    MockInventario(2, 10, 5, "USD-10"),
    MockInventario(3, 5, 8, "USD-5"),
    MockInventario(4, 1, 20, "USD-1"),
]
monto4 = Decimal('63')  # Múltiples soluciones: 2x25 + 1x10 + 1x3, etc.
resultado4 = calcular_desglose_optimo(inventarios4, monto4)
print(f"Monto solicitado: ${monto4}")
print(f"¿Posible?: {resultado4['posible']}")
print(f"Algoritmo usado: {resultado4.get('algoritmo_usado', 'N/A')}")
print(f"Desglose:")
for datos in resultado4['desglose'].values():
    print(f"  - {datos['cantidad']}x ${datos['valor_unitario']} = ${datos['subtotal']}")
print(f"Sobrante: ${resultado4['sobrante']}")
assert resultado4['posible'], "❌ Test 4 falló: debería ser posible"
print("✅ Test 4 PASADO")

# ==================== TEST 5: Cantidad limitada ====================
print("\n[TEST 5] Cantidad limitada - Usar inventario exacto")
print("-" * 60)
inventarios5 = [
    MockInventario(1, 100, 1, "USD-100"),  # Solo 1 billete de cada uno
    MockInventario(2, 50, 1, "USD-50"),
    MockInventario(3, 20, 1, "USD-20"),
    MockInventario(4, 10, 1, "USD-10"),
]
monto5 = Decimal('180')  # 1x100 + 1x50 + 1x20 + 1x10 = exactamente lo que hay
resultado5 = calcular_desglose_optimo(inventarios5, monto5)
print(f"Monto solicitado: ${monto5}")
print(f"¿Posible?: {resultado5['posible']}")
print(f"Algoritmo usado: {resultado5.get('algoritmo_usado', 'N/A')}")
print(f"Desglose:")
total_billetes = 0
for datos in resultado5['desglose'].values():
    print(f"  - {datos['cantidad']}x ${datos['valor_unitario']} = ${datos['subtotal']}")
    total_billetes += datos['cantidad']
print(f"Total billetes usados: {total_billetes}")
print(f"Sobrante: ${resultado5['sobrante']}")
assert resultado5['posible'], "❌ Test 5 falló: debería ser posible"
assert total_billetes == 4, "❌ Test 5: debería usar exactamente 4 billetes"
print("✅ Test 5 PASADO")

print("\n" + "="*60)
print("✅ TODOS LOS TESTS PASARON CORRECTAMENTE")
print("="*60)
print("\nAlgoritmo implementado correctamente:")
print("- Greedy optimizado para casos comunes (rápido)")
print("- Backtracking para casos complejos (garantiza solución si existe)")
print("- Poda para mejorar rendimiento del backtracking")
print("- Minimiza cantidad de billetes usados")
