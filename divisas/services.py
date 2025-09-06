# divisas/services.py
from decimal import Decimal
from django.db import transaction
from django.db.models import OuterRef, Subquery
from .models import CotizacionSegmento, TasaCambio, Divisa
from clientes.models import Segmento, Descuento

@transaction.atomic
def generar_cotizaciones_por_segmento(divisa: Divisa, tasa: TasaCambio, usuario):
    """
    Genera una fila por cada Segmento con snapshot de PB/comisiones y % descuento.
    'usuario' DEBE venir del request.user para llenar creado_por.
    """
    # trae % de descuento por segmento (si no existe -> 0)
    descuentos = Descuento.objects.filter(segmento=OuterRef('pk')).values('porcentaje_descuento')[:1]
    segmentos = Segmento.objects.all().annotate(pct_desc=Subquery(descuentos))

    for seg in segmentos:
        pct = seg.pct_desc or Decimal('0')
        item = CotizacionSegmento(
            divisa=divisa,
            segmento=seg,
            precio_base=tasa.precio_base,
            comision_compra=tasa.comision_compra,
            comision_venta=tasa.comision_venta,
            porcentaje_descuento=pct,
            creado_por=usuario,
        )
        item.calcular_valores()
        item.save()

def ultimas_por_segmento(divisa, hasta=None):
    qs = CotizacionSegmento.objects.filter(divisa=divisa)
    if hasta is not None:
        qs = qs.filter(fecha__lte=hasta)
    qs = qs.order_by('segmento_id', '-fecha', '-id').distinct('segmento_id')
    return qs