"""
Script para verificar datos de cotizaciones en la base de datos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from divisas.models import Divisa, CotizacionSegmento
from clientes.models import Segmento
from django.utils import timezone
from datetime import timedelta

print("=" * 80)
print("VERIFICACIÓN DE DATOS DE COTIZACIONES")
print("=" * 80)

# Verificar divisas activas
divisas_activas = Divisa.objects.filter(is_active=True)
print(f"\n✓ Divisas activas encontradas: {divisas_activas.count()}")
for divisa in divisas_activas:
    print(f"  - {divisa.code}: {divisa.nombre}")

# Verificar segmentos
segmentos = Segmento.objects.all()
print(f"\n✓ Segmentos encontrados: {segmentos.count()}")
for segmento in segmentos:
    print(f"  - {segmento.name}")

# Verificar cotizaciones por segmento
print("\n" + "=" * 80)
print("COTIZACIONES POR DIVISA Y SEGMENTO (Últimos 30 días)")
print("=" * 80)

fecha_inicio = timezone.now() - timedelta(days=30)

for divisa in divisas_activas:
    print(f"\n{divisa.code} - {divisa.nombre}:")
    for segmento in segmentos:
        count = CotizacionSegmento.objects.filter(
            divisa=divisa,
            segmento=segmento,
            fecha__gte=fecha_inicio
        ).count()
        if count > 0:
            ultima = CotizacionSegmento.objects.filter(
                divisa=divisa,
                segmento=segmento
            ).order_by('-fecha').first()
            print(f"  Segmento '{segmento.name}': {count} cotizaciones")
            print(f"    Última: {ultima.fecha.strftime('%Y-%m-%d %H:%M')}")
            print(f"    Compra: {ultima.valor_compra_unit}, Venta: {ultima.valor_venta_unit}")

# Verificar total de cotizaciones
total_cotizaciones = CotizacionSegmento.objects.all().count()
print(f"\n✓ Total de cotizaciones en BD: {total_cotizaciones}")

if total_cotizaciones == 0:
    print("\n⚠ WARNING: No hay cotizaciones en la base de datos!")
    print("  Necesitas crear cotizaciones usando la interfaz de administración")
    print("  o crear tasas de cambio para las divisas.")
else:
    print("\n✓ Base de datos tiene cotizaciones")
