import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
import django
django.setup()

from ganancias.models import RegistroGanancia
from django.db.models.functions import TruncDate
from django.db.models import Sum
from decimal import Decimal

ganancias = RegistroGanancia.objects.filter(tipo_ganancia='spread')
fechas = ganancias.annotate(fecha_solo=TruncDate('fecha_transaccion')).values('fecha_solo').distinct().order_by('fecha_solo')

print('Fechas encontradas:', list(fechas))
print('\nDatos por fecha:')
for item in fechas:
    fecha = item['fecha_solo']
    compras = ganancias.filter(fecha_transaccion__date=fecha, transaccion__tipo_operacion='compra').aggregate(total=Sum('monto_spread'))['total'] or Decimal('0.00')
    ventas = ganancias.filter(fecha_transaccion__date=fecha, transaccion__tipo_operacion='venta').aggregate(total=Sum('monto_spread'))['total'] or Decimal('0.00')
    total = compras + ventas
    print(f'Fecha: {fecha}, Compras: {compras}, Ventas: {ventas}, Total: {total}')
