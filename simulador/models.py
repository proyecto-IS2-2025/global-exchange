# simulador/models.py
from django.db import models

class Moneda(models.Model):
    nombre = models.CharField(max_length=50)
    simbolo = models.CharField(max_length=5)

class Tasa(models.Model):
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    comision_venta = models.DecimalField(max_digits=5, decimal_places=2)
    comision_compra = models.DecimalField(max_digits=5, decimal_places=2)

class CategoriaCliente(models.Model):
    nombre = models.CharField(max_length=50) # Ejemplo: 'VIP', 'Corporativo'
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2)