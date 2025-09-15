# simulador/models.py
from django.db import models

class Moneda(models.Model):
    """
    Representa una moneda en el sistema, como USD o EUR.

    Atributos:
        nombre (CharField): El nombre completo de la moneda (ej. 'Dólar Estadounidense').
        simbolo (CharField): El símbolo de la moneda (ej. '$').
    """
    nombre = models.CharField(max_length=50)
    simbolo = models.CharField(max_length=5)

class Tasa(models.Model):
    """
    Almacena las tasas de cambio y comisiones asociadas a una moneda.

    Esta clase no se usa directamente en la lógica de `views.py` pero
    sirve como un modelo de datos para tasas de cambio.

    Atributos:
        moneda (ForeignKey): La moneda a la que se aplica esta tasa.
        precio_base (DecimalField): El precio base de la moneda.
        comision_venta (DecimalField): La comisión aplicada a la venta de la moneda.
        comision_compra (DecimalField): La comisión aplicada a la compra de la moneda.
    """
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    comision_venta = models.DecimalField(max_digits=5, decimal_places=2)
    comision_compra = models.DecimalField(max_digits=5, decimal_places=2)

class CategoriaCliente(models.Model):
    """
    Define las categorías de clientes para aplicar descuentos.

    Atributos:
        nombre (CharField): El nombre de la categoría (ej. 'VIP', 'Corporativo').
        porcentaje_descuento (DecimalField): El porcentaje de descuento
                                            aplicado a esta categoría.
    """
    nombre = models.CharField(max_length=50) # Ejemplo: 'VIP', 'Corporativo'
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2)