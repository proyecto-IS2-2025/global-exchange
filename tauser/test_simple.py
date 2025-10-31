# -*- coding: utf-8 -*-
"""
Script de prueba para el algoritmo de denominaciones con backtracking.
"""
from decimal import Decimal
from tauser.services import calcular_desglose_optimo

# Mock de inventarios para pruebas
class MockDenominacion:
    def __init__(self, valor):
        self.valor = Decimal(str(valor))
        self.divisa = MockDivisa()

class MockDivisa:
    def __init__(self):
        self.simbolo = '$'

class MockInventario:
    def __init__(self, id_val, valor, cantidad):
        self.id = id_val
        self.cantidad = cantidad
        self.denominacion = MockDenominacion(valor)

print("="*60)
print("PRUEBAS DEL ALGORITMO DE DENOMINACIONES")
print("="*60)

# TEST 1: Caso simple (greedy funciona)
print("\n[TEST 1] Caso simple")
inventarios1 = [
    MockInventario(1, 100, 5),
    MockInventario(2, 50, 10),
    MockInventario(3, 20, 20),
]
resultado1 = calcular_desglose_optimo(inventarios1, Decimal('270'))
print(f"Posible: {resultado1['posible']}, Algoritmo: {resultado1.get('algoritmo_usado')}")
assert resultado1['posible'], "Test 1 FALLO"
print("Test 1 OK")

# TEST 2: Caso donde greedy falla
print("\n[TEST 2] Greedy falla, backtracking funciona")
inventarios2 = [
    MockInventario(1, 30, 1),
    MockInventario(2, 20, 2),
]
resultado2 = calcular_desglose_optimo(inventarios2, Decimal('40'))
print(f"Posible: {resultado2['posible']}, Algoritmo: {resultado2.get('algoritmo_usado')}")
assert resultado2['posible'], "Test 2 FALLO"
assert resultado2.get('algoritmo_usado') == 'backtracking', "Test 2: deberia usar backtracking"
print("Test 2 OK")

# TEST 3: Caso imposible
print("\n[TEST 3] Caso imposible")
inventarios3 = [
    MockInventario(1, 50, 2),
    MockInventario(2, 20, 1),
]
resultado3 = calcular_desglose_optimo(inventarios3, Decimal('35'))
print(f"Posible: {resultado3['posible']}, Algoritmo: {resultado3.get('algoritmo_usado')}")
assert not resultado3['posible'], "Test 3 FALLO"
print("Test 3 OK")

print("\n" + "="*60)
print("TODOS LOS TESTS PASARON")
print("="*60)
