from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from transacciones.models import Transaccion, HistorialTransaccion
from divisas.models import Divisa, CotizacionSegmento
from clientes.models import Cliente, Segmento

User = get_user_model()


# ============================================================
# MODELS
# ============================================================
class TransaccionesModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="1234")
        self.cliente = Cliente.objects.create(nombre_completo="Cliente X", esta_activo=True)
        self.divisa_usd = Divisa.objects.create(code="USD", nombre="Dólar", decimales=2)
        self.divisa_pyg = Divisa.objects.create(code="PYG", nombre="Guaraní", decimales=0)

    def test_crear_transaccion_model(self):
        t = Transaccion.objects.create(
            tipo_operacion="venta",
            cliente=self.cliente,
            divisa_origen=self.divisa_usd,
            divisa_destino=self.divisa_pyg,
            monto_origen=Decimal("100"),
            monto_destino=Decimal("730000"),
            tasa_de_cambio_aplicada=Decimal("7300"),
            procesado_por=self.user,
            medio_pago_datos={"test": "ok"},   # requerido
        )
        self.assertTrue(t.numero_transaccion.startswith("TRX"),
                        f"❌ Número inválido: {t.numero_transaccion}")
        self.assertTrue(t.es_venta,
                        f"❌ Se esperaba es_venta=True, pero es_venta={t.es_venta}")
        self.assertTrue(t.puede_cancelarse,
                        "❌ Una transacción recién creada debería poder cancelarse")

    def test_cambiar_estado_transaccion(self):
        t = Transaccion.objects.create(
            tipo_operacion="compra",
            cliente=self.cliente,
            divisa_origen=self.divisa_pyg,
            divisa_destino=self.divisa_usd,
            monto_origen=Decimal("730000"),
            monto_destino=Decimal("100"),
            tasa_de_cambio_aplicada=Decimal("7300"),
            procesado_por=self.user,
            medio_pago_datos={"test": "ok"},   # requerido
        )
        t.cambiar_estado("pagada", observacion="Pago confirmado", usuario=self.user)
        self.assertEqual(t.estado, "pagada",
                         f"❌ Estado esperado='pagada', obtenido='{t.estado}'")
        self.assertTrue(
            HistorialTransaccion.objects.filter(transaccion=t, estado_nuevo="pagada").exists(),
            "❌ No se encontró historial con estado_nuevo='pagada'"
        )

    def test_cancelar_transaccion_automatica(self):
        t = Transaccion.objects.create(
            tipo_operacion="venta",
            cliente=self.cliente,
            divisa_origen=self.divisa_usd,
            divisa_destino=self.divisa_pyg,
            monto_origen=Decimal("100"),
            monto_destino=Decimal("730000"),
            tasa_de_cambio_aplicada=Decimal("7300"),
            estado="pendiente",
            procesado_por=self.user,
            medio_pago_datos={"test": "ok"},   # requerido
        )
        ok = t.cancelar_automaticamente("Cambio de tasa")
        t.refresh_from_db()
        self.assertTrue(ok, "❌ cancelar_automaticamente devolvió False")
        self.assertEqual(t.estado, "cancelada",
                         f"❌ Estado esperado='cancelada', obtenido='{t.estado}'")
        self.assertIn("CANCELACIÓN AUTOMÁTICA", t.observacion,
                      f"❌ Observación inválida: {t.observacion}")
        self.assertTrue(
            HistorialTransaccion.objects.filter(transaccion=t, estado_nuevo="cancelada").exists(),
            "❌ No se encontró historial con estado_nuevo='cancelada'"
        )


# ============================================================
# SIGNALS
# ============================================================
class TransaccionesSignalsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u2", password="1234")
        self.cliente = Cliente.objects.create(nombre_completo="Cliente Y", esta_activo=True)
        self.divisa_usd = Divisa.objects.create(code="USD", nombre="Dólar", decimales=2)
        self.divisa_pyg = Divisa.objects.create(code="PYG", nombre="Guaraní", decimales=0)
        self.segmento = Segmento.objects.create(name="general")

    def test_signal_cancela_transaccion_pendiente(self):
        # crear transacción pendiente
        t = Transaccion.objects.create(
            tipo_operacion="compra",
            cliente=self.cliente,
            divisa_origen=self.divisa_pyg,
            divisa_destino=self.divisa_usd,
            monto_origen=Decimal("730000"),
            monto_destino=Decimal("100"),
            tasa_de_cambio_aplicada=Decimal("7300"),
            estado="pendiente",
            procesado_por=self.user,
            medio_pago_datos={"test": "ok"},
        )
        # crear nueva cotización -> dispara signal
        cot = CotizacionSegmento.objects.create(
            divisa=self.divisa_usd,
            segmento=self.segmento,
            precio_base=Decimal("7400"),
            comision_compra=Decimal("0.1"),
            comision_venta=Decimal("0.1"),
            porcentaje_descuento=Decimal("0"),
            valor_compra_unit=Decimal("7390"),
            valor_venta_unit=Decimal("7410"),
            creado_por=self.user,
        )
        t.refresh_from_db()
        self.assertEqual(
            t.estado, "cancelada",
            f"❌ Estado esperado='cancelada' tras crear cotización, obtenido='{t.estado}'"
        )
        self.assertTrue(
            HistorialTransaccion.objects.filter(transaccion=t, estado_nuevo="cancelada").exists(),
            "❌ No se encontró historial con estado_nuevo='cancelada'"
        )

# ============================================================
# VIEWS
# ============================================================
class TransaccionesViewsTest(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username="staff", password="1234", is_staff=True)
        self.client = Client()
        self.client.force_login(self.staff_user)
        self.cliente = Cliente.objects.create(nombre_completo="Cliente Z", esta_activo=True)
        self.divisa_usd = Divisa.objects.create(code="USD", nombre="Dólar", decimales=2)
        self.divisa_pyg = Divisa.objects.create(code="PYG", nombre="Guaraní", decimales=0)

    def test_historial_admin_view(self):
        t = Transaccion.objects.create(
            tipo_operacion="venta",
            cliente=self.cliente,
            divisa_origen=self.divisa_usd,
            divisa_destino=self.divisa_pyg,
            monto_origen=Decimal("100"),
            monto_destino=Decimal("730000"),
            tasa_de_cambio_aplicada=Decimal("7300"),
            procesado_por=self.staff_user,
            medio_pago_datos={"test": "ok"},   # requerido
        )
        url = reverse("transacciones:historial_admin")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200,
                         f"❌ Respuesta esperada=200, obtenida={resp.status_code}")
        self.assertIn(t.numero_transaccion, resp.content.decode(),
                      f"❌ Número {t.numero_transaccion} no aparece en la vista")
