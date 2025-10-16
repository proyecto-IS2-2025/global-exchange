"""
Tests unitarios para el módulo de notificaciones.

Cubre:
    - Modelos: ConfiguracionGeneral, NotificacionTasa, Notificacion
    - Formularios: ConfiguracionGeneralForm, NotificacionTasaForm
    - Vistas: GestionNotificacionesView y todas las FBVs
    - Validaciones: Duplicados, campos condicionales, tipo de alerta
"""

from decimal import Decimal
from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from notificaciones.models import (
    ConfiguracionGeneral,
    NotificacionTasa,
    Notificacion,
    CANAL_CHOICES,
    TIPO_ALERTA_CHOICES,
    OPERACION_CHOICES,
    UMBRAL_CONDICION_CHOICES,
    ESTADO_LECTURA_CHOICES
)
from notificaciones.forms import ConfiguracionGeneralForm, NotificacionTasaForm
from clientes.models import Cliente, Segmento
from divisas.models import Divisa

User = get_user_model()


# ============================================================
# MODELS
# ============================================================
class NotificacionesModelsTest(TestCase):
    """Tests para los modelos del módulo de notificaciones."""
    
    def setUp(self):
        """Configuración inicial para todos los tests."""
        print("\n" + "="*80)
        print("CONFIGURACIÓN INICIAL")
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass123')
        self.segmento = Segmento.objects.create(name='general')
        self.cliente = Cliente.objects.create(
            cedula='1234567',
            segmento=self.segmento,
            nombre_completo='Cliente Test',
            esta_activo=True
        )
        # Asignar usuario al cliente
        from clientes.models import AsignacionCliente
        AsignacionCliente.objects.create(usuario=self.user, cliente=self.cliente)
        
        self.divisa = Divisa.objects.create(code='USD', nombre='Dólar', simbolo='$')
        print(f"Usuario: {self.user.username}, Cliente: {self.cliente.nombre_completo}")
        print("="*80)
    
    def test_configuracion_general_creacion(self):
        """Test: Crear configuración general de notificaciones."""
        print("\n" + "="*80)
        print("Ejecutando: test_configuracion_general_creacion")
        config = ConfiguracionGeneral.objects.create(
            usuario=self.user,
            habilitar_notificaciones=True,
            canal_notificacion='sistema_correo'
        )
        print(f"Config creada: {config}")
        self.assertTrue(config.habilitar_notificaciones)
        self.assertEqual(config.canal_notificacion, 'sistema_correo')
        self.assertIn(self.user.username, str(config))
        print("✓ Configuración general creada correctamente")
    
    def test_configuracion_general_str(self):
        """Test: Representación en string de ConfiguracionGeneral."""
        print("\n" + "="*80)
        print("Ejecutando: test_configuracion_general_str")
        config = ConfiguracionGeneral.objects.create(usuario=self.user)
        resultado = str(config)
        print(f"Resultado __str__: {resultado}")
        self.assertIn(self.user.username, resultado)
        print("✓ __str__ de ConfiguracionGeneral funciona correctamente")
    
    def test_notificacion_tasa_creacion_general(self):
        """Test: Crear notificación de tipo general."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_creacion_general")
        alerta = NotificacionTasa.objects.create(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='USD',
            tipo_alerta='general',
            tipo_operacion='ambos',
            activa=True
        )
        print(f"Alerta creada: {alerta}")
        self.assertEqual(alerta.divisa, 'USD')
        self.assertEqual(alerta.tipo_alerta, 'general')
        self.assertTrue(alerta.activa)
        print("✓ Notificación tipo general creada correctamente")
    
    def test_notificacion_tasa_creacion_umbral(self):
        """Test: Crear notificación de tipo umbral."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_creacion_umbral")
        alerta = NotificacionTasa.objects.create(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='USD',
            tipo_alerta='umbral',
            tipo_operacion='compra',
            condicion_umbral='mayor',
            monto_umbral=Decimal('7500.0000'),
            activa=True
        )
        print(f"Alerta umbral: {alerta}")
        print(f"Condición: {alerta.condicion_umbral}, Monto: {alerta.monto_umbral}")
        self.assertEqual(alerta.tipo_alerta, 'umbral')
        self.assertEqual(alerta.monto_umbral, Decimal('7500.0000'))
        self.assertEqual(alerta.condicion_umbral, 'mayor')
        print("✓ Notificación tipo umbral creada correctamente")
    
    def test_notificacion_tasa_str(self):
        """Test: Representación en string de NotificacionTasa."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_str")
        alerta = NotificacionTasa.objects.create(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='EUR',
            tipo_alerta='general',
            tipo_operacion='venta'
        )
        resultado = str(alerta)
        print(f"Resultado __str__: {resultado}")
        self.assertIn('EUR', resultado)
        self.assertIn(self.cliente.nombre_completo, resultado)
        print("✓ __str__ de NotificacionTasa funciona correctamente")
    
    def test_notificacion_tasa_property_segmento(self):
        """Test: Propiedad segmento de NotificacionTasa."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_property_segmento")
        alerta = NotificacionTasa.objects.create(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='USD',
            tipo_alerta='general',
            tipo_operacion='ambos'
        )
        print(f"Segmento del cliente: {alerta.segmento}")
        self.assertEqual(alerta.segmento, self.segmento)
        print("✓ Propiedad segmento funciona correctamente")
    
    def test_notificacion_tasa_property_operacion_display(self):
        """Test: Propiedad operacion_display de NotificacionTasa."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_property_operacion_display")
        alerta = NotificacionTasa.objects.create(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='USD',
            tipo_alerta='general',
            tipo_operacion='compra'
        )
        display = alerta.operacion_display
        print(f"Operación display: {display}")
        self.assertEqual(display, 'Compra')
        print("✓ Propiedad operacion_display funciona correctamente")
    
    def test_notificacion_tasa_validacion_umbral_sin_ambos(self):
        """Test: Validar que umbral no permita tipo_operacion='ambos'."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_validacion_umbral_sin_ambos")
        alerta = NotificacionTasa(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='USD',
            tipo_alerta='umbral',
            tipo_operacion='ambos',  # ❌ No permitido para umbral
            condicion_umbral='mayor',
            monto_umbral=Decimal('7000.0000')
        )
        with self.assertRaises(ValidationError) as context:
            alerta.full_clean()
        print(f"Error esperado capturado: {context.exception}")
        self.assertIn('tipo_operacion', str(context.exception))
        print("✓ Validación de umbral sin 'ambos' funciona correctamente")
    
    def test_notificacion_tasa_validacion_umbral_requiere_campos(self):
        """Test: Validar que umbral requiera condicion_umbral y monto_umbral."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_validacion_umbral_requiere_campos")
        alerta = NotificacionTasa(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='USD',
            tipo_alerta='umbral',
            tipo_operacion='compra'
            # ❌ Faltan condicion_umbral y monto_umbral
        )
        with self.assertRaises(ValidationError) as context:
            alerta.full_clean()
        print(f"Error esperado capturado: {context.exception}")
        print("✓ Validación de campos requeridos para umbral funciona correctamente")
    
    def test_notificacion_creacion(self):
        """Test: Crear una notificación individual."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_creacion")
        alerta_base = NotificacionTasa.objects.create(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='USD',
            tipo_alerta='general',
            tipo_operacion='ambos'
        )
        notif = Notificacion.objects.create(
            usuario=self.user,
            alerta_base=alerta_base,
            mensaje='La tasa de USD ha cambiado',
            estado_lectura='pendiente',
            correo_enviado=False
        )
        print(f"Notificación creada: {notif}")
        self.assertEqual(notif.usuario, self.user)
        self.assertEqual(notif.estado_lectura, 'pendiente')
        self.assertFalse(notif.correo_enviado)
        print("✓ Notificación individual creada correctamente")
    
    def test_notificacion_str(self):
        """Test: Representación en string de Notificacion."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_str")
        notif = Notificacion.objects.create(
            usuario=self.user,
            mensaje='Test de notificación con mensaje largo para verificar el truncamiento',
            estado_lectura='pendiente'
        )
        resultado = str(notif)
        print(f"Resultado __str__: {resultado}")
        self.assertIn(self.user.username, resultado)
        self.assertTrue(len(resultado) < 100)  # Verifica truncamiento
        print("✓ __str__ de Notificacion funciona correctamente")
    
    def test_notificacion_ordering(self):
        """Test: Orden de notificaciones por fecha_creacion descendente."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_ordering")
        notif1 = Notificacion.objects.create(
            usuario=self.user,
            mensaje='Notificación 1'
        )
        notif2 = Notificacion.objects.create(
            usuario=self.user,
            mensaje='Notificación 2'
        )
        notificaciones = Notificacion.objects.all()
        print(f"Orden: {[n.id for n in notificaciones]}")
        self.assertEqual(notificaciones[0].id, notif2.id)
        print("✓ Orden de notificaciones funciona correctamente")


# ============================================================
# FORMS
# ============================================================
class NotificacionesFormsTest(TestCase):
    """Tests para los formularios del módulo de notificaciones."""
    
    def setUp(self):
        """Configuración inicial para todos los tests."""
        print("\n" + "="*80)
        print("CONFIGURACIÓN INICIAL FORMS")
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass123')
        self.segmento = Segmento.objects.create(name='general')
        self.cliente = Cliente.objects.create(
            cedula='1234567',
            segmento=self.segmento,
            nombre_completo='Cliente Test',
            esta_activo=True
        )
        # Asignar usuario al cliente
        from clientes.models import AsignacionCliente
        AsignacionCliente.objects.create(usuario=self.user, cliente=self.cliente)
        
        self.divisa_usd = Divisa.objects.create(code='USD', nombre='Dólar', simbolo='$', is_active=True)
        self.divisa_eur = Divisa.objects.create(code='EUR', nombre='Euro', simbolo='€', is_active=True)
        # PYG debe ser excluido del formulario
        self.divisa_pyg = Divisa.objects.create(code='PYG', nombre='Guaraní', simbolo='₲', is_active=True)
        print("="*80)
    
    def test_configuracion_general_form_valido(self):
        """Test: Formulario de configuración general válido."""
        print("\n" + "="*80)
        print("Ejecutando: test_configuracion_general_form_valido")
        form = ConfiguracionGeneralForm(data={
            'habilitar_notificaciones': True,
            'canal_notificacion': 'sistema_correo'
        })
        print(f"Form válido: {form.is_valid()}")
        self.assertTrue(form.is_valid(), f"❌ Form no válido: {form.errors}")
        print("✓ Formulario de configuración general válido")
    
    def test_notificacion_tasa_form_general_valido(self):
        """Test: Formulario de notificación tipo general válido."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_form_general_valido")
        form = NotificacionTasaForm(data={
            'divisa': self.divisa_usd.id,
            'tipo_alerta': 'general',
            'tipo_operacion': 'ambos'
        })
        print(f"Form válido: {form.is_valid()}")
        if not form.is_valid():
            print(f"Errores: {form.errors}")
        self.assertTrue(form.is_valid(), f"❌ Form no válido: {form.errors}")
        print("✓ Formulario de notificación general válido")
    
    def test_notificacion_tasa_form_umbral_valido(self):
        """Test: Formulario de notificación tipo umbral válido."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_form_umbral_valido")
        form = NotificacionTasaForm(data={
            'divisa': self.divisa_usd.id,
            'tipo_alerta': 'umbral',
            'tipo_operacion': 'compra',
            'condicion_umbral': 'mayor',
            'monto_umbral': '7500.0000'
        })
        print(f"Form válido: {form.is_valid()}")
        if not form.is_valid():
            print(f"Errores: {form.errors}")
        self.assertTrue(form.is_valid(), f"❌ Form no válido: {form.errors}")
        print("✓ Formulario de notificación umbral válido")
    
    def test_notificacion_tasa_form_umbral_con_ambos_invalido(self):
        """Test: Formulario umbral con tipo_operacion='ambos' es inválido."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_form_umbral_con_ambos_invalido")
        form = NotificacionTasaForm(data={
            'divisa': self.divisa_usd.id,
            'tipo_alerta': 'umbral',
            'tipo_operacion': 'ambos',  # ❌ No permitido para umbral
            'condicion_umbral': 'mayor',
            'monto_umbral': '7500.0000'
        })
        print(f"Form válido: {form.is_valid()}")
        self.assertFalse(form.is_valid(), "❌ Form debería ser inválido")
        self.assertIn('tipo_operacion', form.errors)
        print(f"Error esperado: {form.errors['tipo_operacion']}")
        print("✓ Validación de umbral sin 'ambos' funciona en formulario")
    
    def test_notificacion_tasa_form_umbral_sin_monto_invalido(self):
        """Test: Formulario umbral sin monto_umbral es inválido."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_form_umbral_sin_monto_invalido")
        form = NotificacionTasaForm(data={
            'divisa': self.divisa_usd.id,
            'tipo_alerta': 'umbral',
            'tipo_operacion': 'compra',
            'condicion_umbral': 'mayor'
            # ❌ Falta monto_umbral
        })
        print(f"Form válido: {form.is_valid()}")
        self.assertFalse(form.is_valid(), "❌ Form debería ser inválido")
        print(f"Errores: {form.errors}")
        print("✓ Validación de monto requerido funciona en formulario")
    
    def test_notificacion_tasa_form_excluye_pyg(self):
        """Test: Formulario excluye la divisa PYG."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_form_excluye_pyg")
        form = NotificacionTasaForm()
        divisas_disponibles = [d.code for d in form.fields['divisa'].queryset]
        print(f"Divisas disponibles: {divisas_disponibles}")
        self.assertIn('USD', divisas_disponibles)
        self.assertIn('EUR', divisas_disponibles)
        self.assertNotIn('PYG', divisas_disponibles, "❌ PYG no debería estar disponible")
        print("✓ PYG excluido correctamente del formulario")
    
    def test_notificacion_tasa_form_excluye_transaccion_cancelada(self):
        """Test: Formulario excluye tipo de alerta 'transaccion_cancelada'."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_form_excluye_transaccion_cancelada")
        form = NotificacionTasaForm()
        tipos_disponibles = [choice[0] for choice in form.fields['tipo_alerta'].choices]
        print(f"Tipos de alerta disponibles: {tipos_disponibles}")
        self.assertIn('general', tipos_disponibles)
        self.assertIn('umbral', tipos_disponibles)
        self.assertNotIn('transaccion_cancelada', tipos_disponibles, 
                         "❌ transaccion_cancelada no debería estar disponible")
        print("✓ transaccion_cancelada excluido correctamente del formulario")
    
    def test_notificacion_tasa_form_clean_divisa_convierte_a_code(self):
        """Test: Método clean_divisa convierte objeto Divisa a código string."""
        print("\n" + "="*80)
        print("Ejecutando: test_notificacion_tasa_form_clean_divisa_convierte_a_code")
        form = NotificacionTasaForm(data={
            'divisa': self.divisa_usd.id,
            'tipo_alerta': 'general',
            'tipo_operacion': 'ambos'
        })
        self.assertTrue(form.is_valid())
        codigo_divisa = form.cleaned_data['divisa']
        print(f"Código de divisa retornado: {codigo_divisa} (tipo: {type(codigo_divisa).__name__})")
        self.assertEqual(codigo_divisa, 'USD')
        self.assertIsInstance(codigo_divisa, str)
        print("✓ Conversión de Divisa a código funciona correctamente")


# ============================================================
# VIEWS
# ============================================================
class NotificacionesViewsTest(TestCase):
    """Tests para las vistas del módulo de notificaciones."""
    
    def setUp(self):
        """Configuración inicial para todos los tests."""
        print("\n" + "="*80)
        print("CONFIGURACIÓN INICIAL VIEWS")
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass123')
        self.segmento = Segmento.objects.create(name='general')
        self.cliente = Cliente.objects.create(
            cedula='1234567',
            segmento=self.segmento,
            nombre_completo='Cliente Test',
            esta_activo=True
        )
        # Asignar usuario al cliente
        from clientes.models import AsignacionCliente
        AsignacionCliente.objects.create(usuario=self.user, cliente=self.cliente)
        
        self.divisa = Divisa.objects.create(code='USD', nombre='Dólar', simbolo='$', is_active=True)
        self.client = Client()
        self.client.force_login(self.user)
        print(f"Usuario logueado: {self.user.username}")
        print("="*80)
    
    def test_gestion_notificaciones_view_get(self):
        """Test: Vista de gestión de notificaciones GET."""
        print("\n" + "="*80)
        print("Ejecutando: test_gestion_notificaciones_view_get")
        url = reverse('notificaciones:gestion_notificaciones')
        response = self.client.get(url)
        print(f"Status: {response.status_code}")
        print(f"Keys en contexto: {list(response.context.keys())}")
        self.assertEqual(response.status_code, 200)
        self.assertIn('form_general', response.context)
        self.assertIn('notificaciones', response.context)
        self.assertIn('form_nueva_alerta', response.context)
        print("✓ Vista de gestión GET funciona correctamente")
    
    def test_gestion_notificaciones_crea_config_general(self):
        """Test: Vista crea ConfiguracionGeneral automáticamente."""
        print("\n" + "="*80)
        print("Ejecutando: test_gestion_notificaciones_crea_config_general")
        url = reverse('notificaciones:gestion_notificaciones')
        self.client.get(url)
        exists = ConfiguracionGeneral.objects.filter(usuario=self.user).exists()
        print(f"ConfiguracionGeneral existe: {exists}")
        self.assertTrue(exists)
        print("✓ ConfiguracionGeneral creada automáticamente")
    
    def test_guardar_configuracion_general(self):
        """Test: Guardar configuración general via POST."""
        print("\n" + "="*80)
        print("Ejecutando: test_guardar_configuracion_general")
        url = reverse('notificaciones:gestion_notificaciones')
        # Crear config inicial
        ConfiguracionGeneral.objects.create(usuario=self.user)
        # Actualizar via POST
        response = self.client.post(url, {
            'guardar_general': '',
            'habilitar_notificaciones': 'on',
            'canal_notificacion': 'sistema_correo'
        })
        print(f"Status: {response.status_code}")
        self.assertEqual(response.status_code, 302)  # Redirect
        config = ConfiguracionGeneral.objects.get(usuario=self.user)
        print(f"Config actualizada: habilitar={config.habilitar_notificaciones}, canal={config.canal_notificacion}")
        self.assertTrue(config.habilitar_notificaciones)
        self.assertEqual(config.canal_notificacion, 'sistema_correo')
        print("✓ Configuración general guardada correctamente")
    
    def test_crear_alerta_requiere_cliente_en_sesion(self):
        """Test: Crear alerta requiere cliente_id en sesión."""
        print("\n" + "="*80)
        print("Ejecutando: test_crear_alerta_requiere_cliente_en_sesion")
        url = reverse('notificaciones:gestion_notificaciones')
        # Sin cliente_id en sesión
        response = self.client.post(url, {
            'guardar_alerta': '',
            'divisa': self.divisa.id,
            'tipo_alerta': 'general',
            'tipo_operacion': 'ambos'
        })
        print(f"Status: {response.status_code}")
        alertas_count = NotificacionTasa.objects.filter(usuario=self.user).count()
        print(f"Alertas creadas: {alertas_count}")
        self.assertEqual(alertas_count, 0)
        print("✓ Validación de cliente en sesión funciona correctamente")
    
    def test_crear_alerta_general(self):
        """Test: Crear alerta de tipo general via POST."""
        print("\n" + "="*80)
        print("Ejecutando: test_crear_alerta_general")
        # Agregar cliente a sesión
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()
        
        url = reverse('notificaciones:gestion_notificaciones')
        response = self.client.post(url, {
            'guardar_alerta': '',
            'divisa': self.divisa.id,
            'tipo_alerta': 'general',
            'tipo_operacion': 'ambos'
        })
        print(f"Status: {response.status_code}")
        self.assertEqual(response.status_code, 302)  # Redirect
        
        alerta = NotificacionTasa.objects.get(usuario=self.user)
        print(f"Alerta creada: {alerta}")
        self.assertEqual(alerta.divisa, 'USD')
        self.assertEqual(alerta.tipo_alerta, 'general')
        print("✓ Alerta general creada correctamente")
    
    def test_crear_alerta_umbral(self):
        """Test: Crear alerta de tipo umbral via POST."""
        print("\n" + "="*80)
        print("Ejecutando: test_crear_alerta_umbral")
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()
        
        url = reverse('notificaciones:gestion_notificaciones')
        response = self.client.post(url, {
            'guardar_alerta': '',
            'divisa': self.divisa.id,
            'tipo_alerta': 'umbral',
            'tipo_operacion': 'compra',
            'condicion_umbral': 'mayor',
            'monto_umbral': '7500.0000'
        })
        print(f"Status: {response.status_code}")
        self.assertEqual(response.status_code, 302)
        
        alerta = NotificacionTasa.objects.get(usuario=self.user)
        print(f"Alerta umbral: condicion={alerta.condicion_umbral}, monto={alerta.monto_umbral}")
        self.assertEqual(alerta.tipo_alerta, 'umbral')
        self.assertEqual(alerta.monto_umbral, Decimal('7500.0000'))
        print("✓ Alerta umbral creada correctamente")
    
    def test_toggle_notificacion(self):
        """Test: Alternar estado activo de una alerta."""
        print("\n" + "="*80)
        print("Ejecutando: test_toggle_notificacion")
        alerta = NotificacionTasa.objects.create(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='USD',
            tipo_alerta='general',
            tipo_operacion='ambos',
            activa=True
        )
        print(f"Estado inicial: activa={alerta.activa}")
        
        url = reverse('notificaciones:toggle_notificacion', kwargs={'pk': alerta.pk})
        response = self.client.get(url)
        print(f"Status: {response.status_code}")
        
        alerta.refresh_from_db()
        print(f"Estado después de toggle: activa={alerta.activa}")
        self.assertFalse(alerta.activa)
        print("✓ Toggle de notificación funciona correctamente")
    
    def test_eliminar_notificacion(self):
        """Test: Eliminar una alerta."""
        print("\n" + "="*80)
        print("Ejecutando: test_eliminar_notificacion")
        alerta = NotificacionTasa.objects.create(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='USD',
            tipo_alerta='general',
            tipo_operacion='ambos'
        )
        alerta_id = alerta.id
        print(f"Alerta creada con ID: {alerta_id}")
        
        url = reverse('notificaciones:eliminar_notificacion', kwargs={'pk': alerta_id})
        response = self.client.post(url)
        print(f"Status: {response.status_code}")
        
        exists = NotificacionTasa.objects.filter(id=alerta_id).exists()
        print(f"Alerta existe después de eliminar: {exists}")
        self.assertFalse(exists)
        print("✓ Eliminación de notificación funciona correctamente")
    
    def test_editar_notificacion_get(self):
        """Test: Vista de edición GET."""
        print("\n" + "="*80)
        print("Ejecutando: test_editar_notificacion_get")
        alerta = NotificacionTasa.objects.create(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='USD',
            tipo_alerta='general',
            tipo_operacion='ambos'
        )
        
        url = reverse('notificaciones:editar_notificacion', kwargs={'pk': alerta.pk})
        response = self.client.get(url)
        print(f"Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('alerta', response.context)
        print("✓ Vista de edición GET funciona correctamente")
    
    def test_editar_notificacion_post(self):
        """Test: Editar una alerta via POST."""
        print("\n" + "="*80)
        print("Ejecutando: test_editar_notificacion_post")
        alerta = NotificacionTasa.objects.create(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='USD',
            tipo_alerta='general',
            tipo_operacion='ambos'
        )
        print(f"Operación inicial: {alerta.tipo_operacion}")
        
        url = reverse('notificaciones:editar_notificacion', kwargs={'pk': alerta.pk})
        response = self.client.post(url, {
            'divisa': self.divisa.id,
            'tipo_alerta': 'general',
            'tipo_operacion': 'compra'  # Cambiar a compra
        })
        print(f"Status: {response.status_code}")
        
        alerta.refresh_from_db()
        print(f"Operación después de editar: {alerta.tipo_operacion}")
        self.assertEqual(alerta.tipo_operacion, 'compra')
        print("✓ Edición de notificación funciona correctamente")
    
    def test_no_puede_editar_transaccion_cancelada(self):
        """Test: No permite editar alertas tipo 'transaccion_cancelada'."""
        print("\n" + "="*80)
        print("Ejecutando: test_no_puede_editar_transaccion_cancelada")
        alerta = NotificacionTasa.objects.create(
            usuario=self.user,
            cliente_asociado=self.cliente,
            divisa='USD',
            tipo_alerta='transaccion_cancelada',
            tipo_operacion='compra'
        )
        
        url = reverse('notificaciones:editar_notificacion', kwargs={'pk': alerta.pk})
        response = self.client.get(url)
        print(f"Status: {response.status_code}")
        self.assertEqual(response.status_code, 302)  # Redirect con error
        print("✓ Prevención de edición de transaccion_cancelada funciona correctamente")
    
    def test_marcar_notificacion_leida(self):
        """Test: Marcar una notificación como leída."""
        print("\n" + "="*80)
        print("Ejecutando: test_marcar_notificacion_leida")
        notif = Notificacion.objects.create(
            usuario=self.user,
            mensaje='Test notificación',
            estado_lectura='pendiente'
        )
        print(f"Estado inicial: {notif.estado_lectura}")
        
        url = reverse('notificaciones:marcar_leida', kwargs={'pk': notif.pk})
        response = self.client.post(url)
        print(f"Status: {response.status_code}")
        
        notif.refresh_from_db()
        print(f"Estado después: {notif.estado_lectura}")
        self.assertEqual(notif.estado_lectura, 'leida')
        print("✓ Marcar como leída funciona correctamente")
    
    def test_limpiar_todas_notificaciones(self):
        """Test: Limpiar todas las notificaciones pendientes."""
        print("\n" + "="*80)
        print("Ejecutando: test_limpiar_todas_notificaciones")
        Notificacion.objects.create(usuario=self.user, mensaje='Notif 1', estado_lectura='pendiente')
        Notificacion.objects.create(usuario=self.user, mensaje='Notif 2', estado_lectura='pendiente')
        Notificacion.objects.create(usuario=self.user, mensaje='Notif 3', estado_lectura='leida')
        
        pendientes_antes = Notificacion.objects.filter(usuario=self.user, estado_lectura='pendiente').count()
        print(f"Pendientes antes: {pendientes_antes}")
        
        url = reverse('notificaciones:limpiar_todas')
        response = self.client.post(url)
        print(f"Status: {response.status_code}")
        
        pendientes_despues = Notificacion.objects.filter(usuario=self.user, estado_lectura='pendiente').count()
        print(f"Pendientes después: {pendientes_despues}")
        self.assertEqual(pendientes_despues, 0)
        print("✓ Limpiar todas funciona correctamente")
    
    def test_historial_notificaciones(self):
        """Test: Vista de historial de notificaciones."""
        print("\n" + "="*80)
        print("Ejecutando: test_historial_notificaciones")
        Notificacion.objects.create(usuario=self.user, mensaje='Notif 1')
        Notificacion.objects.create(usuario=self.user, mensaje='Notif 2')
        
        url = reverse('notificaciones:historial')
        response = self.client.get(url)
        print(f"Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        self.assertIn('notificaciones', response.context)
        notificaciones_list = response.context['notificaciones'].object_list
        count = len(notificaciones_list) if isinstance(notificaciones_list, list) else notificaciones_list.count()
        print(f"Notificaciones en contexto: {count}")
        print("✓ Historial de notificaciones funciona correctamente")
    
    def test_historial_filtro_por_estado(self):
        """Test: Filtrar historial por estado."""
        print("\n" + "="*80)
        print("Ejecutando: test_historial_filtro_por_estado")
        Notificacion.objects.create(usuario=self.user, mensaje='Pendiente', estado_lectura='pendiente')
        Notificacion.objects.create(usuario=self.user, mensaje='Leída', estado_lectura='leida')
        
        url = reverse('notificaciones:historial') + '?estado=pendiente'
        response = self.client.get(url)
        notificaciones = response.context['notificaciones'].object_list
        count = len(notificaciones) if isinstance(notificaciones, list) else notificaciones.count()
        print(f"Notificaciones filtradas: {count}")
        self.assertEqual(count, 1)
        self.assertEqual(notificaciones[0].estado_lectura, 'pendiente')
        print("✓ Filtro por estado funciona correctamente")


# ============================================================
# INTEGRATION TESTS
# ============================================================
class NotificacionesIntegrationTest(TestCase):
    """Tests de integración para flujos completos."""
    
    def setUp(self):
        """Configuración inicial."""
        print("\n" + "="*80)
        print("CONFIGURACIÓN INICIAL INTEGRATION")
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass123')
        self.segmento = Segmento.objects.create(name='general')
        self.cliente = Cliente.objects.create(
            cedula='1234567',
            segmento=self.segmento,
            nombre_completo='Cliente Test',
            esta_activo=True
        )
        # Asignar usuario al cliente
        from clientes.models import AsignacionCliente
        AsignacionCliente.objects.create(usuario=self.user, cliente=self.cliente)
        
        self.divisa = Divisa.objects.create(code='USD', nombre='Dólar', simbolo='$', is_active=True)
        self.client = Client()
        self.client.force_login(self.user)
        print("="*80)
    
    def test_flujo_completo_creacion_y_gestion_alerta(self):
        """Test: Flujo completo de creación, edición y eliminación de alerta."""
        print("\n" + "="*80)
        print("Ejecutando: test_flujo_completo_creacion_y_gestion_alerta")
        
        # 1. Crear alerta
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()
        
        url_crear = reverse('notificaciones:gestion_notificaciones')
        self.client.post(url_crear, {
            'guardar_alerta': '',
            'divisa': self.divisa.id,
            'tipo_alerta': 'general',
            'tipo_operacion': 'ambos'
        })
        alerta = NotificacionTasa.objects.get(usuario=self.user)
        print(f"1. Alerta creada: {alerta}")
        
        # 2. Editar alerta
        url_editar = reverse('notificaciones:editar_notificacion', kwargs={'pk': alerta.pk})
        self.client.post(url_editar, {
            'divisa': self.divisa.id,
            'tipo_alerta': 'general',
            'tipo_operacion': 'compra'
        })
        alerta.refresh_from_db()
        print(f"2. Alerta editada: operacion={alerta.tipo_operacion}")
        self.assertEqual(alerta.tipo_operacion, 'compra')
        
        # 3. Toggle activa/inactiva
        url_toggle = reverse('notificaciones:toggle_notificacion', kwargs={'pk': alerta.pk})
        self.client.get(url_toggle)
        alerta.refresh_from_db()
        print(f"3. Alerta después de toggle: activa={alerta.activa}")
        self.assertFalse(alerta.activa)
        
        # 4. Eliminar alerta
        url_eliminar = reverse('notificaciones:eliminar_notificacion', kwargs={'pk': alerta.pk})
        self.client.post(url_eliminar)
        exists = NotificacionTasa.objects.filter(id=alerta.id).exists()
        print(f"4. Alerta existe después de eliminar: {exists}")
        self.assertFalse(exists)
        
        print("✓ Flujo completo de gestión de alerta funciona correctamente")
    
    def test_flujo_completo_notificaciones_usuario(self):
        """Test: Flujo completo de gestión de notificaciones de usuario."""
        print("\n" + "="*80)
        print("Ejecutando: test_flujo_completo_notificaciones_usuario")
        
        # 1. Crear notificaciones
        notif1 = Notificacion.objects.create(
            usuario=self.user,
            mensaje='Notificación 1',
            estado_lectura='pendiente'
        )
        notif2 = Notificacion.objects.create(
            usuario=self.user,
            mensaje='Notificación 2',
            estado_lectura='pendiente'
        )
        print(f"1. Notificaciones creadas: {Notificacion.objects.filter(usuario=self.user).count()}")
        
        # 2. Marcar una como leída
        url_marcar = reverse('notificaciones:marcar_leida', kwargs={'pk': notif1.pk})
        self.client.post(url_marcar)
        notif1.refresh_from_db()
        print(f"2. Notificación 1 estado: {notif1.estado_lectura}")
        self.assertEqual(notif1.estado_lectura, 'leida')
        
        # 3. Ver historial
        url_historial = reverse('notificaciones:historial')
        response = self.client.get(url_historial)
        print(f"3. Historial status: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        
        # 4. Limpiar todas las pendientes
        url_limpiar = reverse('notificaciones:limpiar_todas')
        self.client.post(url_limpiar)
        pendientes = Notificacion.objects.filter(usuario=self.user, estado_lectura='pendiente').count()
        print(f"4. Notificaciones pendientes después de limpiar: {pendientes}")
        self.assertEqual(pendientes, 0)
        
        print("✓ Flujo completo de gestión de notificaciones funciona correctamente")
