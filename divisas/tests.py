from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from divisas.models import Divisa, TasaCambio, CotizacionSegmento
from divisas.forms import DivisaForm, TasaCambioForm
from divisas.services import generar_cotizaciones_por_segmento, ultimas_por_segmento
from clientes.models import Segmento
from django.test import TransactionTestCase

User = get_user_model()


# ============================================================
# MODELS
# ============================================================
class DivisasModelsTest(TestCase):
    def test_divisa_save_normaliza_code_y_simbolo(self):
        print("\n================================================================================")
        print("Ejecutando: test_divisa_save_normaliza_code_y_simbolo")
        d = Divisa.objects.create(code=" usd ", nombre="Dólar", simbolo=" $ ")
        print(f"Guardado: code={d.code}, simbolo={d.simbolo}, decimales={d.decimales}")
        self.assertEqual(d.code, "USD", "❌ El código no se normalizó correctamente")
        self.assertEqual(d.simbolo, "$", "❌ El símbolo no se normalizó correctamente")

    def test_divisa_str(self):
        print("\n================================================================================")
        print("Ejecutando: test_divisa_str")
        d = Divisa.objects.create(code="EUR", nombre="Euro", simbolo="€", is_active=True)
        s = str(d)
        print(f"Resultado __str__: {s}")
        self.assertIn("EUR - Euro", s, "❌ El __str__ de Divisa no contiene lo esperado")

    def test_tasacambio_str(self):
        print("\n================================================================================")
        print("Ejecutando: test_tasacambio_str")
        d = Divisa.objects.create(code="GBP", nombre="Libra", simbolo="£")
        t = TasaCambio.objects.create(divisa=d, precio_base=Decimal("10.5"))
        print(f"Resultado __str__: {t}")
        self.assertIn("GBP", str(t), "❌ El __str__ de TasaCambio no contiene el código de divisa")

    def test_cotizacionsegmento_calcular_valores(self):
        print("\n================================================================================")
        print("Ejecutando: test_cotizacionsegmento_calcular_valores")
        d = Divisa.objects.create(code="PYG", nombre="Guaraní", simbolo="₲")
        seg = Segmento.objects.create(name="general")
        cot = CotizacionSegmento(
            divisa=d,
            segmento=seg,
            precio_base=Decimal("100"),
            comision_compra=Decimal("2"),
            comision_venta=Decimal("3"),
            porcentaje_descuento=Decimal("50"),
        )
        cot.calcular_valores()
        print(f"Compra={cot.valor_compra_unit}, Venta={cot.valor_venta_unit}")
        self.assertLess(cot.valor_compra_unit, cot.precio_base, "❌ Compra no menor al precio base")
        self.assertGreater(cot.valor_venta_unit, cot.precio_base, "❌ Venta no mayor al precio base")

    def test_cotizacionsegmento_str(self):
        print("\n================================================================================")
        print("Ejecutando: test_cotizacionsegmento_str")
        d = Divisa.objects.create(code="ARS", nombre="Peso", simbolo="$")
        seg = Segmento.objects.create(name="general")
        cot = CotizacionSegmento.objects.create(
            divisa=d,
            segmento=seg,
            precio_base=Decimal("1"),
            comision_compra=Decimal("0.1"),
            comision_venta=Decimal("0.1"),
            porcentaje_descuento=0,
            valor_compra_unit=Decimal("0.9"),
            valor_venta_unit=Decimal("1.1"),
        )
        print(f"Resultado __str__: {cot}")
        self.assertIn("ARS", str(cot), "❌ El __str__ no contiene el código de divisa")


# ============================================================
# FORMS
# ============================================================
class DivisasFormsTest(TestCase):
    def test_divisa_form_normaliza_code(self):
        print("\n================================================================================")
        print("Ejecutando: test_divisa_form_normaliza_code")
        form = DivisaForm(data={"nombre": "Euro", "code": " eur ", "simbolo": " € ", "decimales": 2})
        self.assertTrue(form.is_valid(), f"❌ Form no válido: {form.errors}")
        obj = form.save()
        print(f"Resultado: code={obj.code}, simbolo={obj.simbolo}")
        self.assertEqual(obj.code, "EUR")
        self.assertEqual(obj.simbolo, "€")

    def test_tasacambio_form_valido(self):
        print("\n================================================================================")
        print("Ejecutando: test_tasacambio_form_valido")
        d = Divisa.objects.create(code="USD", nombre="Dólar")
        form = TasaCambioForm(
            data={"precio_base": Decimal("1.5"), "comision_compra": Decimal("0.2"), "comision_venta": Decimal("0.3")},
            divisa=d,
        )
        print("Form válido:", form.is_valid())
        self.assertTrue(form.is_valid(), f"❌ Form debería ser válido: {form.errors}")

    def test_tasacambio_form_invalido(self):
        print("\n================================================================================")
        print("Ejecutando: test_tasacambio_form_invalido")
        d = Divisa.objects.create(code="USD", nombre="Dólar")
        form = TasaCambioForm(
            data={"precio_base": Decimal("-1"), "comision_compra": Decimal("-1"), "comision_venta": Decimal("-1")},
            divisa=d,
        )
        print("Form válido:", form.is_valid())
        self.assertFalse(form.is_valid(), "❌ Form debería ser inválido con valores negativos")


# ============================================================
# SERVICES
# ============================================================
class DivisasServicesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester", "t@t.com", "123", is_superuser=True)
        self.divisa = Divisa.objects.create(code="USD", nombre="Dólar")
        self.tasa = TasaCambio.objects.create(divisa=self.divisa, precio_base=Decimal("1.0"))
        self.seg = Segmento.objects.create(name="general")

    def test_generar_cotizaciones_por_segmento_crea(self):
        print("\n================================================================================")
        print("Ejecutando: test_generar_cotizaciones_por_segmento_crea")
        generar_cotizaciones_por_segmento(self.divisa, self.tasa, self.user)
        count = CotizacionSegmento.objects.filter(divisa=self.divisa).count()
        print(f"Total generados: {count}")
        self.assertGreater(count, 0, "❌ No se generaron cotizaciones")

    def test_ultimas_por_segmento_retorna_unico(self):
        print("\n================================================================================")
        print("Ejecutando: test_ultimas_por_segmento_retorna_unico")
        generar_cotizaciones_por_segmento(self.divisa, self.tasa, self.user)
        resultados = ultimas_por_segmento(self.divisa)
        print(f"Segmentos retornados: {[c.segmento_id for c in resultados]}")
        segs = [c.segmento_id for c in resultados]
        self.assertEqual(len(segs), len(set(segs)), "❌ Hay duplicados en las últimas cotizaciones")

    def test_ultimas_por_segmento_filtra_fecha(self):
        print("\n================================================================================")
        print("Ejecutando: test_ultimas_por_segmento_filtra_fecha")
        generar_cotizaciones_por_segmento(self.divisa, self.tasa, self.user)
        futuros = ultimas_por_segmento(self.divisa, hasta=timezone.now())
        print(f"Cantidad obtenida con filtro hasta ahora: {futuros.count()}")
        self.assertTrue(all(c.fecha <= timezone.now() for c in futuros), "❌ Cotizaciones con fecha posterior")


# ============================================================
# SIGNALS
# ============================================================
class DivisasSignalsTest(TransactionTestCase):
    def test_crea_cotizaciones_al_crear_tasa(self):
        print("\n================================================================================")
        print("Ejecutando: test_crea_cotizaciones_al_crear_tasa")
        user = User.objects.create_user("tester", "t@t.com", "123", is_superuser=True)
        divisa = Divisa.objects.create(code="EUR", nombre="Euro")
        Segmento.objects.create(name="general")
        with transaction.atomic():
            TasaCambio.objects.create(divisa=divisa, precio_base=Decimal("2"))
        count = CotizacionSegmento.objects.filter(divisa=divisa).count()
        print(f"Cotizaciones generadas por signal: {count}")
        self.assertGreater(count, 0, "❌ El signal no generó cotizaciones")


# ============================================================
# VIEWS
# ============================================================
class DivisasViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("admin", "a@a.com", "123", is_staff=True, is_superuser=True)
        self.client = Client()
        self.client.force_login(self.user)
        self.divisa = Divisa.objects.create(code="USD", nombre="Dólar", is_active=True)
        self.seg = Segmento.objects.create(name="general")

    def test_divisa_list_view(self):
        print("\n================================================================================")
        print("Ejecutando: test_divisa_list_view")
        url = reverse("divisas:lista")
        resp = self.client.get(url)
        print(f"Status: {resp.status_code}, Divisas en contexto: {len(resp.context['divisas'])}")
        self.assertEqual(resp.status_code, 200, "❌ La vista lista no respondió 200 OK")

    def test_divisa_create_view(self):
        print("\n================================================================================")
        print("Ejecutando: test_divisa_create_view")
        url = reverse("divisas:crear")
        resp = self.client.post(url, {"nombre": "Euro", "code": "eur", "simbolo": "€", "decimales": 2})
        print(f"Status: {resp.status_code}")
        self.assertEqual(resp.status_code, 302, "❌ No redirigió tras crear divisa")
        self.assertTrue(Divisa.objects.filter(code="EUR").exists(), "❌ No se creó la divisa")

    def test_tasacambio_create_view(self):
        print("\n================================================================================")
        print("Ejecutando: test_tasacambio_create_view")
        url = reverse("divisas:tasa_nueva", kwargs={"divisa_id": self.divisa.id})
        resp = self.client.post(url, {"precio_base": "1.5", "comision_compra": "0.1", "comision_venta": "0.2"})
        print(f"Status: {resp.status_code}")
        self.assertEqual(resp.status_code, 302, "❌ No redirigió tras crear tasa")
        self.assertTrue(TasaCambio.objects.filter(divisa=self.divisa).exists(), "❌ No se creó la tasa de cambio")

    def test_visualizador_tasas(self):
        print("\n================================================================================")
        print("Ejecutando: test_visualizador_tasas")
        url = reverse("divisas:visualizador_tasas")
        resp = self.client.get(url)
        print(f"Status: {resp.status_code}, Keys en contexto: {list(resp.context.keys())}")
        self.assertEqual(resp.status_code, 200, "❌ visualizador_tasas no devolvió 200")
        self.assertIn("divisas_data", resp.context, "❌ El contexto no contiene 'divisas_data'")
