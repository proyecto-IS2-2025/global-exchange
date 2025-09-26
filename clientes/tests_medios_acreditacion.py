# clientes/tests_medios_acreditacion.py - TESTS PARA MEDIOS DE ACREDITACIÓN DE CLIENTES

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
import json

# ====================================================================
# Importaciones de Modelos (de clientes y medios_pago)
# ====================================================================
from clientes.models import Cliente, AsignacionCliente, Segmento, ClienteMedioDePago, HistorialClienteMedioDePago
from medios_pago.models import MedioDePago, CampoMedioDePago, PREDEFINED_FIELDS
# Asumo que tienes un CustomUser definido, si no, usa User de django.contrib.auth
#from users.models import CustomUser as User 
from clientes.forms import ClienteMedioDePagoCompleteForm # Importación del Formulario clave

User = get_user_model() # Usar get_user_model() para mayor portabilidad

# ====================================================================


class MediosAcreditacionBaseTestCase(TestCase):
    """
    Configuración base para tests de medios de acreditación.
    Prepara un entorno de Django con un cliente activo para el operador.
    """
    
    def setUp(self):
        # 1. Crear usuario operador
        self.user = User.objects.create_user(
            username='operador_test',
            password='testpass123',
            email='operador@test.com'
        )
        
        # 2. Crear Segmento y Cliente (la entidad central)
        self.segmento = Segmento.objects.create(name='Empresarial')
        self.cliente = Cliente.objects.create(
            nombre_completo='Juan Pérez',
            cedula='12345678',
            segmento=self.segmento,
            esta_activo=True
        )
        
        # 3. Asignar el cliente al usuario para permitir la operación
        self._crear_asignacion()
        
        # 4. Crear los medios de pago base para las pruebas
        self._crear_medios_pago_prueba()

    def _crear_asignacion(self):
        """Asigna el cliente de prueba al usuario de prueba."""
        AsignacionCliente.objects.create(
            cliente=self.cliente,
            user=self.user,
            is_active=True
        )

    def _crear_medios_pago_prueba(self):
        """Crea los objetos MedioDePago y CampoMedioDePago necesarios para las pruebas."""
        
        # 1. Transferencia Bancaria Local (Requiere Cuenta y Tipo)
        self.medio_banco = MedioDePago.objects.create(
            nombre='Banco Local',
            tipo_medio='bank_local',
            comision_porcentaje=0.5, is_active=True
        )
        CampoMedioDePago.objects.create(
            medio_de_pago=self.medio_banco,
            campo_api='bank_account_number',
            nombre_campo='Número de Cuenta',
            is_required=True,
            tipo_dato='NUMERO'
        )
        CampoMedioDePago.objects.create(
            medio_de_pago=self.medio_banco,
            campo_api='account_holder_name',
            nombre_campo='Titular de Cuenta',
            is_required=True,
            tipo_dato='TEXTO'
        )
        
        # 2. Tarjeta de Crédito (Requiere Número y Titular)
        self.medio_tarjeta = MedioDePago.objects.create(
            nombre='Tarjeta Crédito',
            tipo_medio='stripe',
            comision_porcentaje=3.0, is_active=True
        )
        CampoMedioDePago.objects.create(
            medio_de_pago=self.medio_tarjeta,
            campo_api='card_number',
            nombre_campo='Número de Tarjeta',
            is_required=True,
            tipo_dato='NUMERO'
        )
        CampoMedioDePago.objects.create(
            medio_de_pago=self.medio_tarjeta,
            campo_api='account_holder_name',
            nombre_campo='Titular de Tarjeta',
            is_required=True,
            tipo_dato='TEXTO'
        )

        # 3. Medio Opcional (Solo requiere Nombre)
        self.medio_opcional = MedioDePago.objects.create(
            nombre='Medio Opcional (Solo Nombre)',
            tipo_medio='efectivo',
            comision_porcentaje=0.0, is_active=True
        )
        CampoMedioDePago.objects.create(
            medio_de_pago=self.medio_opcional,
            campo_api='account_holder_name',
            nombre_campo='Nombre del titular',
            is_required=True,
            tipo_dato='TEXTO'
        )
        
        # 4. Billetera Electrónica (Requiere Teléfono)
        self.medio_billetera = MedioDePago.objects.create(
            nombre='Billetera Electrónica',
            tipo_medio='billetera_electronica', # Nuevo tipo
            comision_porcentaje=1.0, is_active=True
        )
        CampoMedioDePago.objects.create(
            medio_de_pago=self.medio_billetera,
            # CORRECCIÓN CLAVE: 'phone_number' -> 'account_phone'
            campo_api='account_phone', 
            nombre_campo='Número de Teléfono',
            is_required=True,
            tipo_dato='TELEFONO'          ### CORRECCIÓN: NOMBRE Y TIPO EXPLÍCITOS
        )

    def _agregar_medio_pago(self, medio_base, data, expected_status=200):
        """Función auxiliar para simular la adición de un medio de pago por POST."""
        response = self.client.post(reverse('clientes:agregar_medio_pago', kwargs={'medio_id': medio_base.id}), data=data)
        self.assertEqual(response.status_code, expected_status, f"Fallo al agregar medio {medio_base.nombre}. Status: {response.status_code}")
        return response

    def _assert_medio_exists(self, count, **filters):
        """Función auxiliar para verificar la cantidad de medios de pago que cumplen un filtro."""
        self.assertEqual(ClienteMedioDePago.objects.filter(cliente=self.cliente, **filters).count(), count)

    def _get_medio(self, **filters):
        """Función auxiliar para obtener un solo medio de pago que cumple un filtro."""
        return ClienteMedioDePago.objects.get(cliente=self.cliente, **filters)


# ====================================================================
# TESTS DE LÓGICA DE PRINCIPALIDAD
# ====================================================================

class TestAsociacionMediosPrincipal(MediosAcreditacionBaseTestCase):
    """Pruebas centradas en la lógica de 'es_principal'."""

    def test_01_asociar_primer_medio_pago_exitoso(self):
        """
        🧪 TEST 01: Asociación exitosa del primer medio de pago.
        Lógica: Se debe crear un registro de ClienteMedioDePago.
        """
        print("\n--- INICIO: TEST 01 - Asociación exitosa del primer medio de pago ---")

        # Datos de prueba para el medio de banco (requiere 2 campos)
        datos_banco = {
            'campo_1': '1234567890', # bank_account_number
            'campo_2': 'Juan Pérez', # account_holder_name
            'es_activo': 'on',
            'es_principal': 'on'
        }
        
        self._agregar_medio_pago(self.medio_banco, datos_banco)
        
        # Verificar que el medio fue creado y es principal
        self._assert_medio_exists(1, medio_de_pago=self.medio_banco, es_principal=True)
        medio_creado = self._get_medio(medio_de_pago=self.medio_banco)
        
        self.assertTrue(medio_creado.es_activo)
        self.assertTrue(medio_creado.es_principal)
        self.assertEqual(medio_creado.datos_campos['bank_account_number'], '1234567890')
        print("✅ Resultado: Primer medio asociado correctamente como Principal.")

    def test_02_cambio_automatico_de_principal(self):
        """
        🧪 TEST 02: El segundo medio principal desactiva el anterior.
        Lógica: Solo puede haber un medio principal por cliente y tipo.
        """
        print("\n--- INICIO: TEST 02 - Cambio automático de principal ---")
        
        # 1. Asociar primer medio (Tarjeta 1) como principal
        self.client.post(reverse('clientes:agregar_medio_pago', kwargs={'medio_id': self.medio_tarjeta.id}), data={
            'campo_1': '1111', 'campo_2': 'Titular Uno', 'es_activo': 'on', 'es_principal': 'on'
        })
        
        primer_medio = self._get_medio(datos_campos__card_number='1111')
        self.assertTrue(primer_medio.es_principal, "Error: Primer medio no es principal.")

        # 2. Asociar segundo medio (Tarjeta 2) como principal
        self.client.post(reverse('clientes:agregar_medio_pago', kwargs={'medio_id': self.medio_tarjeta.id}), data={
            'campo_1': '2222', 'campo_2': 'Titular Dos', 'es_activo': 'on', 'es_principal': 'on'
        })
        
        segundo_medio = self._get_medio(datos_campos__card_number='2222')
        self.assertTrue(segundo_medio.es_principal, "Error: Segundo medio no es principal.")
        
        # 3. Recargar el primer medio y verificar que ya NO es principal
        primer_medio.refresh_from_db()
        self.assertFalse(primer_medio.es_principal, "Error: El medio anterior sigue siendo principal.")
        self._assert_medio_exists(1, medio_de_pago=self.medio_tarjeta, es_principal=True) # Solo 1 principal
        
        print("✅ Resultado: El segundo medio se convirtió en principal, desactivando el anterior.")

    def test_03_asociar_multiples_medios_diferentes_sin_forzar_principal(self):
        """
        🧪 TEST 03: Asociación de múltiples medios sin conflicto principal si no se fuerza.
        Lógica: Múltiples medios pueden existir, solo el primero será principal si se pide.
        """
        print("\n--- INICIO: TEST 03 - Múltiples medios diferentes ---")
        
        # 1. Banco (Principal)
        self.client.post(reverse('clientes:agregar_medio_pago', kwargs={'medio_id': self.medio_banco.id}), data={
            'campo_1': '101010', 'campo_2': 'Titular Banco', 'es_activo': 'on', 'es_principal': 'on'
        })
        
        # 2. Tarjeta (No principal explícitamente)
        self.client.post(reverse('clientes:agregar_medio_pago', kwargs={'medio_id': self.medio_tarjeta.id}), data={
            'campo_1': '4444', 'campo_2': 'Titular Tarjeta', 'es_activo': 'on', 'es_principal': 'off'
        })
        
        # 3. Billetera (No principal explícitamente)
        self.client.post(reverse('clientes:agregar_medio_pago', kwargs={'medio_id': self.medio_billetera.id}), data={
            'campo_1': '99999999', 'es_activo': 'on', 'es_principal': 'off'
        })
        
        # Verificaciones
        self._assert_medio_exists(1, medio_de_pago=self.medio_banco, es_principal=True)
        self._assert_medio_exists(0, medio_de_pago=self.medio_tarjeta, es_principal=True)
        self._assert_medio_exists(0, medio_de_pago=self.medio_billetera, es_principal=True)
        self._assert_medio_exists(3)
        
        print("✅ Resultado: Múltiples medios asociados, solo uno (el primero) quedó como principal.")

# ====================================================================
# TESTS DE VALIDACIÓN Y AUDITORÍA (Se asume que los fallos originales estaban aquí)
# ====================================================================

class TestValidacionYAuditoria(MediosAcreditacionBaseTestCase):
    """Pruebas centradas en la validación de datos y el registro de historial."""

    def test_04_validacion_campo_requerido_faltante(self):
        """
        🧪 TEST 04: Búsqueda de fallo - Campo requerido faltante.
        Lógica: El sistema debe rechazar la creación si falta un campo requerido.
        """
        print("\n--- INICIO: TEST 04 - Campo Requerido Faltante ---")
        
        # Datos de prueba para el medio de banco (solo se proporciona 1 de 2 campos requeridos)
        datos_incompletos = {
            'campo_1': '1234567890', # bank_account_number
            # Falta campo_2: account_holder_name
            'es_activo': 'on',
            'es_principal': 'on'
        }
        
        # Se espera un error de validación (Status 400 o un error en la vista)
        # La vista de Django debería devolver un error de formulario. Aquí verificamos que no se cree el objeto.
        self._agregar_medio_pago(self.medio_banco, datos_incompletos, expected_status=200) # Debería pasar por el proceso y fallar en el formulario.

        # Verificamos que el objeto *no* se haya creado
        self._assert_medio_exists(0, medio_de_pago=self.medio_banco)
        
        # Esto es más difícil de probar en unittest sin ver la implementación de la vista,
        # pero el hecho de que no se cree el objeto es la clave.
        print("✅ Resultado: La validación previno la creación del medio por falta de campo requerido.")

    def test_05_validacion_tipo_dato_invalido(self):
        """
        🧪 TEST 05: Búsqueda de fallo - Tipo de dato inválido.
        Lógica: El sistema debe rechazar la creación si el tipo de dato es incorrecto.
        """
        print("\n--- INICIO: TEST 05 - Tipo de Dato Inválido ---")
        
        # Datos de prueba para el medio de banco, donde el campo 'NUMERO' recibe un texto
        datos_invalidos = {
            'campo_1': 'ABCDEFGHIJ', # bank_account_number (espera NUMERO)
            'campo_2': 'Juan Pérez', # account_holder_name
            'es_activo': 'on',
            'es_principal': 'on'
        }
        
        self._agregar_medio_pago(self.medio_banco, datos_invalidos, expected_status=200)

        # Verificamos que el objeto *no* se haya creado
        self._assert_medio_exists(0, medio_de_pago=self.medio_banco)
        
        print("✅ Resultado: La validación previno la creación del medio por tipo de dato inválido.")

    def test_07_registro_historial_en_creacion(self):
        """
        🧪 TEST 07: Registro de Historial en Creación.
        Lógica: Se debe crear un registro en HistorialClienteMedioDePago al crear un medio.
        """
        print("\n--- INICIO: TEST 07 - Registro de Historial en Creación ---")
        
        # 1. Asociar medio de pago
        datos_tarjeta = {
            'campo_1': '5555', # card_number
            'campo_2': 'Historial Test', # account_holder_name
            'es_activo': 'on',
            'es_principal': 'on'
        }
        self._agregar_medio_pago(self.medio_tarjeta, datos_tarjeta)
        
        medio_creado = self._get_medio(datos_campos__card_number='5555')
        
        # 2. Verificar el historial
        historial = HistorialClienteMedioDePago.objects.filter(cliente_medio_pago=medio_creado, accion='CREADO')
        self.assertTrue(historial.exists())
        self.assertEqual(historial.count(), 1)
        
        registro = historial.first()
        self.assertEqual(registro.datos_anteriores, None)
        self.assertIsNotNone(registro.datos_nuevos)
        self.assertIn('card_number', registro.datos_nuevos)
        
        print("✅ Resultado: Se registró la acción 'CREADO' en el historial.")


# ====================================================================
# TESTS DE DUPLICADOS
# ====================================================================

class TestDuplicados(MediosAcreditacionBaseTestCase):
    """Tests para la lógica de duplicidad y campos opcionales."""

    def test_06_permitir_duplicados_con_diferencia_de_datos(self):
        """
        🧪 TEST 06: Permitir la asociación de múltiples medios del mismo TIPO (e.g., dos tarjetas) con datos diferentes.
        Lógica: El sistema debe permitir la asociación mientras el JSON de datos no sea idéntico.
        """
        print("\n--- INICIO: TEST 06 - Permiso de Múltiples Medios del Mismo Tipo ---")
        
        # 1. Primera Tarjeta (Número 1111)
        self.client.post(reverse('clientes:agregar_medio_pago', kwargs={'medio_id': self.medio_tarjeta.id}), data={
            'campo_1': '1111', 'campo_2': 'Titular Uno', 'es_activo': 'on', 'es_principal': 'on'
        })
        
        # 2. Segunda Tarjeta (Número 2222) - Mismo MedioDePago, diferente dato
        self.client.post(reverse('clientes:agregar_medio_pago', kwargs={'medio_id': self.medio_tarjeta.id}), data={
            'campo_1': '2222', 'campo_2': 'Titular Dos', 'es_activo': 'on', 'es_principal': 'off'
        })
        
        total_medios = ClienteMedioDePago.objects.filter(cliente=self.cliente, medio_de_pago=self.medio_tarjeta).count()
        self.assertEqual(total_medios, 2, "Error: No se crearon los dos medios de pago esperados.")
        
        print("✅ Resultado: Dos medios del mismo tipo con datos diferentes se crearon exitosamente.")

    def test_duplicado_identico_rechazado(self):
        """
        🧪 TEST 06a: No permitir la asociación de medios idénticos (mismo cliente, mismo medio, mismos datos).
        Lógica: El sistema debe rechazar la creación si el hash de datos es idéntico a uno existente.
        """
        print("\n--- INICIO: TEST 06a - Duplicado Idéntico Rechazado ---")
        
        # 1. Primera Billetera (Número 9999)
        self.client.post(reverse('clientes:agregar_medio_pago', kwargs={'medio_id': self.medio_billetera.id}), data={
            'campo_1': '99999999', 'es_activo': 'on', 'es_principal': 'on'
        })
        
        # 2. Segunda Billetera (Mismos datos)
        self.client.post(reverse('clientes:agregar_medio_pago', kwargs={'medio_id': self.medio_billetera.id}), data={
            'campo_1': '99999999', 'es_activo': 'on', 'es_principal': 'off'
        })
        
        total_medios = ClienteMedioDePago.objects.filter(cliente=self.cliente, medio_de_pago=self.medio_billetera).count()
        self.assertEqual(total_medios, 1, "Error: Se creó el medio duplicado idéntico.")
        
        print("✅ Resultado: El medio duplicado idéntico fue rechazado correctamente.")