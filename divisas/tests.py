# tests/test_cotizaciones.py
import datetime
from django.utils import timezone
from django.test import TestCase
from divisas.models import Divisa, CotizacionSegmento

class UltimaCotizacionTests(TestCase):
    def setUp(self):
        self.usd = Divisa.objects.create(code='USD', nombre='Dólar', is_active=True)
        # … crea dos segmentos (s1, s2) como corresponda
        from clientes.models import Segmento
        self.s1 = Segmento.objects.create(name='Minorista')
        self.s2 = Segmento.objects.create(name='Mayorista')

        t0 = timezone.now() - datetime.timedelta(hours=2)
        t1 = timezone.now() - datetime.timedelta(hours=1)
        t2 = timezone.now()

        # s1: dos registros en tiempos distintos
        CotizacionSegmento.objects.create(
            divisa=self.usd, segmento=self.s1, fecha=t0,
            precio_base=1433, comision_compra=130, comision_venta=123,
            porcentaje_descuento=0, valor_compra_unit=1433, valor_venta_unit=1556,
        )
        self.latest_s1 = CotizacionSegmento.objects.create(
            divisa=self.usd, segmento=self.s1, fecha=t2,
            precio_base=1433, comision_compra=130, comision_venta=123,
            porcentaje_descuento=10, valor_compra_unit=1316, valor_venta_unit=1543.7,
        )

        # s2: uno solo
        self.only_s2 = CotizacionSegmento.objects.create(
            divisa=self.usd, segmento=self.s2, fecha=t1,
            precio_base=1433, comision_compra=130, comision_venta=123,
            porcentaje_descuento=100, valor_compra_unit=1433, valor_venta_unit=1433,
        )

    def test_ultima_sin_fecha(self):
        obj = CotizacionSegmento.objects.ultima_para(self.usd, self.s1)
        assert obj == self.latest_s1

    def test_ultima_con_fecha_corte_incluyente(self):
        # fecha entre t1 y t2 → debería traer el de t1 para s1
        fecha_corte = self.only_s2.fecha  # ~ t1
        obj = CotizacionSegmento.objects.ultima_para(self.usd, self.s1, hasta=fecha_corte)
        # no existe en s1 algo con fecha==t1, así que debe retornar el de t0
        assert obj.fecha < fecha_corte

    def test_ultima_para_segmento_sin_registros(self):
        from clientes.models import Segmento
        s3 = Segmento.objects.create(name='Corporativo')
        obj = CotizacionSegmento.objects.ultima_para(self.usd, s3)
        assert obj is None

    def test_desempate_por_id(self):
        # Crea otra fila con misma fecha que latest_s1
        twin = CotizacionSegmento.objects.create(
            divisa=self.usd, segmento=self.s1, fecha=self.latest_s1.fecha,
            precio_base=1433, comision_compra=130, comision_venta=123,
            porcentaje_descuento=5, valor_compra_unit=..., valor_venta_unit=...,
        )
        obj = CotizacionSegmento.objects.ultima_para(self.usd, self.s1)
        # debe traer la de mayor id si la fecha es igual
        assert obj.id == max(twin.id, self.latest_s1.id)
