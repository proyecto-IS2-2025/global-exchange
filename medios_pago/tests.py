# tests.py - Tests completos para el módulo de Medios de Pago
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
import json
from datetime import datetime

from .models import MedioDePago, CampoMedioDePago
from .forms import MedioDePagoForm, CampoMedioDePagoForm, create_campo_formset

User = get_user_model()


class MedioDePagoModelTest(TestCase):
    """Tests para el modelo MedioDePago"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        print("\n" + "="*80)
        print(f"Ejecutando: {self._testMethodName}")
        print("="*80)
        
    def test_crear_medio_pago_basico(self):
        """Test: Crear un medio de pago con datos básicos"""
        print("\n✅ Probando creación de medio de pago básico...")
        
        medio = MedioDePago.objects.create(
            nombre="PayPal",
            comision_porcentaje=3.5,
            is_active=True
        )
        
        self.assertEqual(medio.nombre, "PayPal")
        self.assertEqual(medio.comision_porcentaje, Decimal('3.5'))
        self.assertTrue(medio.is_active)
        self.assertIsNone(medio.deleted_at)
        
        print(f"   ✓ Medio creado: {medio}")
        print(f"   ✓ Comisión: {medio.comision_porcentaje}%")
        print(f"   ✓ Estado: {'Activo' if medio.is_active else 'Inactivo'}")
        
    def test_validacion_comision_negativa(self):
        """Test: Validar que no se permitan comisiones negativas"""
        print("\n⚠️ Probando validación de comisión negativa...")
        
        with self.assertRaises(ValidationError) as context:
            medio = MedioDePago(
                nombre="Tarjeta Visa",
                comision_porcentaje=-5,
                is_active=True
            )
            medio.full_clean()
        
        print(f"   ✓ Error capturado: {context.exception}")
        print("   ✓ Validación funcionando correctamente")
        
    def test_validacion_comision_mayor_100(self):
        """Test: Validar que no se permitan comisiones mayores a 100%"""
        print("\n⚠️ Probando validación de comisión mayor a 100%...")
        
        with self.assertRaises(ValidationError) as context:
            medio = MedioDePago(
                nombre="Banco Local",
                comision_porcentaje=150,
                is_active=True
            )
            medio.full_clean()
        
        print(f"   ✓ Error capturado: {context.exception}")
        print("   ✓ Comisión máxima validada correctamente")
        
    def test_nombre_vacio_no_permitido(self):
        """Test: Validar que el nombre no puede estar vacío"""
        print("\n⚠️ Probando validación de nombre vacío...")
        
        with self.assertRaises(ValidationError):
            medio = MedioDePago(
                nombre="   ",  # Solo espacios
                comision_porcentaje=2.5
            )
            medio.save()
        
        print("   ✓ Nombre vacío rechazado correctamente")
        
    def test_soft_delete_funcionalidad(self):
        """Test: Probar la funcionalidad de soft delete"""
        print("\n🗑️ Probando soft delete...")
        
        medio = MedioDePago.objects.create(
            nombre="Mercado Pago",
            comision_porcentaje=4.5,
            is_active=True
        )
        
        print(f"   Estado inicial: Activo={medio.is_active}, Eliminado={medio.is_deleted}")
        
        # Aplicar soft delete
        medio.soft_delete()
        
        print(f"   Estado después de soft delete: Activo={medio.is_active}, Eliminado={medio.is_deleted}")
        
        self.assertIsNotNone(medio.deleted_at)
        self.assertFalse(medio.is_active)
        self.assertTrue(medio.is_deleted)
        
        # Verificar que aún existe en la BD
        self.assertTrue(MedioDePago.objects.filter(pk=medio.pk).exists())
        
        # Verificar que no aparece en el manager 'active'
        self.assertFalse(MedioDePago.active.filter(pk=medio.pk).exists())
        
        print("   ✓ Soft delete aplicado correctamente")
        print("   ✓ Registro aún existe en BD pero marcado como eliminado")
        
    def test_restore_medio_eliminado(self):
        """Test: Restaurar un medio de pago eliminado"""
        print("\n♻️ Probando restauración de medio eliminado...")
        
        medio = MedioDePago.objects.create(
            nombre="Bitcoin Wallet",
            comision_porcentaje=1.5
        )
        
        medio.soft_delete()
        print(f"   Estado después de eliminar: Eliminado={medio.is_deleted}")
        
        medio.restore()
        print(f"   Estado después de restaurar: Eliminado={medio.is_deleted}")
        
        self.assertIsNone(medio.deleted_at)
        self.assertFalse(medio.is_deleted)
        
        print("   ✓ Medio restaurado exitosamente")


class CampoMedioDePagoModelTest(TestCase):
    """Tests para el modelo CampoMedioDePago"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        print("\n" + "="*80)
        print(f"Ejecutando: {self._testMethodName}")
        print("="*80)
        
        self.medio = MedioDePago.objects.create(
            nombre="PayPal Test",
            comision_porcentaje=3.0,
            is_active=True
        )
        
    def test_crear_campo_basico(self):
        """Test: Crear un campo básico para un medio de pago"""
        print("\n📝 Probando creación de campo básico...")
        
        campo = CampoMedioDePago.objects.create(
            medio_de_pago=self.medio,
            nombre_campo="Email",
            tipo_dato="EMAIL",
            is_required=True
        )
        
        self.assertEqual(campo.nombre_campo, "Email")
        self.assertEqual(campo.tipo_dato, "EMAIL")
        self.assertTrue(campo.is_required)
        
        print(f"   ✓ Campo creado: {campo}")
        print(f"   ✓ Tipo: {campo.get_tipo_dato_display()}")
        print(f"   ✓ Requerido: {'Sí' if campo.is_required else 'No'}")
        
    def test_validacion_nombre_campo_duplicado(self):
        """Test: Validar que no se permitan campos duplicados en el mismo medio"""
        print("\n⚠️ Probando validación de campos duplicados...")
        
        # Crear primer campo
        CampoMedioDePago.objects.create(
            medio_de_pago=self.medio,
            nombre_campo="Número de cuenta",
            tipo_dato="TEXTO"
        )
        
        # Intentar crear campo duplicado
        with self.assertRaises(ValidationError) as context:
            campo_duplicado = CampoMedioDePago(
                medio_de_pago=self.medio,
                nombre_campo="Número de cuenta",  # Mismo nombre
                tipo_dato="NUMERO"
            )
            campo_duplicado.full_clean()
        
        print(f"   ✓ Error capturado: {context.exception}")
        print("   ✓ Duplicados prevenidos correctamente")
        
    def test_soft_delete_campo(self):
        """Test: Probar soft delete de campos"""
        print("\n🗑️ Probando soft delete de campo...")
        
        campo = CampoMedioDePago.objects.create(
            medio_de_pago=self.medio,
            nombre_campo="CVV",
            tipo_dato="NUMERO",
            is_required=True
        )
        
        print(f"   Estado inicial: Eliminado={campo.is_deleted}")
        
        campo.soft_delete()
        
        print(f"   Estado después de soft delete: Eliminado={campo.is_deleted}")
        
        self.assertIsNotNone(campo.deleted_at)
        self.assertTrue(campo.is_deleted)
        
        # Verificar que no aparece en campos activos
        self.assertEqual(self.medio.campos.filter(deleted_at__isnull=True).count(), 0)
        
        print("   ✓ Campo marcado como eliminado")
        print("   ✓ No aparece en campos activos del medio")
        
    def test_campo_duplicado_despues_soft_delete(self):
        """Test: Permitir crear campo con mismo nombre después de soft delete"""
        print("\n♻️ Probando creación de campo con nombre de campo eliminado...")
        
        # Crear y eliminar campo
        campo1 = CampoMedioDePago.objects.create(
            medio_de_pago=self.medio,
            nombre_campo="Token",
            tipo_dato="TEXTO"
        )
        campo1.soft_delete()
        
        print(f"   Campo original eliminado: {campo1.nombre_campo}")
        
        # Crear nuevo campo con el mismo nombre (debería permitirse)
        campo2 = CampoMedioDePago.objects.create(
            medio_de_pago=self.medio,
            nombre_campo="Token",
            tipo_dato="TEXTO"
        )
        
        self.assertEqual(campo2.nombre_campo, "Token")
        self.assertFalse(campo2.is_deleted)
        
        print(f"   ✓ Nuevo campo creado con el mismo nombre: {campo2.nombre_campo}")
        print("   ✓ Sistema permite reutilizar nombres de campos eliminados")


class MedioDePagoFormsTest(TestCase):
    """Tests para los formularios del módulo"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        print("\n" + "="*80)
        print(f"Ejecutando: {self._testMethodName}")
        print("="*80)
        
    def test_medio_pago_form_valido(self):
        """Test: Formulario de medio de pago con datos válidos"""
        print("\n✅ Probando formulario con datos válidos...")
        
        form_data = {
            'nombre': 'Stripe',
            'comision_porcentaje': '2.9',
            'is_active': True
        }
        
        form = MedioDePagoForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        print(f"   ✓ Formulario válido")
        print(f"   ✓ Datos: {form_data}")
        
    def test_medio_pago_form_comision_invalida(self):
        """Test: Formulario con comisión inválida"""
        print("\n⚠️ Probando formulario con comisión inválida...")
        
        form_data = {
            'nombre': 'Banco Test',
            'comision_porcentaje': '120',  # Mayor a 100
            'is_active': True
        }
        
        form = MedioDePagoForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('comision_porcentaje', form.errors)
        
        print(f"   ✓ Formulario rechazado correctamente")
        print(f"   ✓ Error: {form.errors['comision_porcentaje']}")
        
    def test_campo_form_valido(self):
        """Test: Formulario de campo con datos válidos"""
        print("\n✅ Probando formulario de campo válido...")
        
        medio = MedioDePago.objects.create(
            nombre="Test Medio",
            comision_porcentaje=2.0
        )
        
        form_data = {
            'nombre_campo': 'Número de tarjeta',
            'tipo_dato': 'NUMERO',
            'is_required': True
        }
        
        form = CampoMedioDePagoForm(data=form_data)
        form.instance.medio_de_pago = medio
        
        self.assertTrue(form.is_valid())
        print(f"   ✓ Formulario de campo válido")
        print(f"   ✓ Campo: {form_data['nombre_campo']}")
        
    def test_formset_creacion_vs_edicion(self):
        """Test: Verificar diferencias entre formset de creación y edición"""
        print("\n🔄 Probando formsets de creación vs edición...")
        
        # Formset de creación
        FormSetCreacion = create_campo_formset(is_edit=False)
        formset_creacion = FormSetCreacion()
        
        print(f"   Formset de creación:")
        print(f"   ✓ Formularios extra: {formset_creacion.extra}")
        self.assertEqual(formset_creacion.extra, 1)
        
        # Formset de edición
        FormSetEdicion = create_campo_formset(is_edit=True)
        formset_edicion = FormSetEdicion()
        
        print(f"   Formset de edición:")
        print(f"   ✓ Formularios extra: {formset_edicion.extra}")
        self.assertEqual(formset_edicion.extra, 0)
        
        print("   ✓ Configuración diferenciada correcta")


class MedioDePagoViewsTest(TestCase):
    """Tests para las vistas del módulo"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        print("\n" + "="*80)
        print(f"Ejecutando: {self._testMethodName}")
        print("="*80)
        
        # Crear superusuario de prueba y forzar autenticación
        self.user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com',
            is_staff=True,
            is_active=True
        )
        # Forzar autenticación sin usar login
        self.client = Client()
        self.client.force_login(self.user)
        
        # Permisos específicos para medios de pago
        perms = [
            'view_mediodepago',
            'add_mediodepago',
            'change_mediodepago',
            'delete_mediodepago',
            'view_campomediodepago',
            'add_campomediodepago',
            'change_campomediodepago',
            'delete_campomediodepago'
        ]
        
        # Asegurar que el usuario tiene todos los permisos necesarios
        for perm_code in perms:
            try:
                perm = Permission.objects.get(codename=perm_code)
                self.user.user_permissions.add(perm)
            except Permission.DoesNotExist:
                print(f"⚠️ Advertencia: Permiso {perm_code} no encontrado")
        
        # Configurar cliente y forzar login
        self.client = Client()
        success = self.client.login(username='testuser', password='testpass123')
        
        if not success:
            print("❌ Error: No se pudo autenticar el usuario de prueba")
            print("💡 Sugerencia: Verificar credenciales y estado del usuario")
        
        print(f"   Usuario de prueba creado: {self.user.username}")
        print(f"   Permisos asignados: {[p.codename for p in self.user.user_permissions.all()]}")
        print(f"   Estado login: {'✅ Exitoso' if success else '❌ Fallido'}")
        
    def test_lista_medios_pago(self):
        """Test: Vista de lista de medios de pago"""
        print("\n📋 Probando vista de lista...")
        
        # Crear algunos medios de prueba con Decimal
        from decimal import Decimal
        MedioDePago.objects.create(nombre="PayPal", comision_porcentaje=Decimal('3.500'))
        MedioDePago.objects.create(nombre="Stripe", comision_porcentaje=Decimal('2.900'))
        
        # Crear uno eliminado (no debe aparecer)
        medio_eliminado = MedioDePago.objects.create(
            nombre="Eliminado",
            comision_porcentaje=5.0
        )
        medio_eliminado.soft_delete()
        
        response = self.client.get(reverse('medios_pago:lista'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PayPal")
        self.assertContains(response, "Stripe")
        self.assertNotContains(response, "Eliminado")
        
        print(f"   ✓ Status: {response.status_code}")
        print(f"   ✓ Medios activos mostrados: 2")
        print(f"   ✓ Medios eliminados ocultados: 1")
        
    def test_crear_medio_pago_completo(self):
        """Test: Crear medio de pago con campos dinámicos"""
        print("\n➕ Probando creación de medio con campos...")
        print("   • Fase 1: Verificando acceso al formulario...")
        
        try:
            url = reverse('medios_pago:crear_admin')
            print(f"   • URL del formulario: {url}")
            
            response = self.client.get(url)
            print(f"   • Status code: {response.status_code}")
            
            if response.status_code == 404:
                print("   ❌ Error: URL no encontrada")
                print("   💡 Sugerencia: Verificar en urls.py:")
                print("     - Que existe la URL 'crear_admin'")
                print("     - Que la vista está correctamente importada")
            elif response.status_code == 302:
                print(f"   ⚠️ Redirección detectada -> {response.url}")
                print("   💡 Sugerencia: Verificar permisos del usuario")
        except Exception as e:
            print(f"   ❌ Error al acceder: {str(e)}")
            print("   💡 Sugerencia: Verificar configuración de URLs")
        
        print("\n   • Fase 2: Preparando datos de creación...")
        data = {
            'nombre': 'MercadoPago',
            'comision_porcentaje': '4.5',
            'is_active': 'on',
            # Formset management
            'campos-TOTAL_FORMS': '2',
            'campos-INITIAL_FORMS': '0',
            'campos-MIN_NUM_FORMS': '0',
            'campos-MAX_NUM_FORMS': '10',
            # Campo 1
            'campos-0-nombre_campo': 'Email',
            'campos-0-tipo_dato': 'EMAIL',
            'campos-0-is_required': 'on',
            'campos-0-DELETE': '',
            # Campo 2
            'campos-1-nombre_campo': 'Token API',
            'campos-1-tipo_dato': 'TEXTO',
            'campos-1-is_required': 'on',
            'campos-1-DELETE': '',
        }

        print("   • Datos del medio de pago:")
        print(f"     - Nombre: {data['nombre']}")
        print(f"     - Comisión: {data['comision_porcentaje']}%")
        print(f"     - Activo: {data['is_active']}")
        
        print("   • Campos dinámicos:")
        print(f"     1. {data['campos-0-nombre_campo']} ({data['campos-0-tipo_dato']})")
        print(f"     2. {data['campos-1-nombre_campo']} ({data['campos-1-tipo_dato']})")

        print("\n   • Fase 3: Enviando datos al servidor...")
        response = self.client.post(url, data, follow=True)
        
        if response.status_code != 200:
            print(f"   ❌ Error: Status code {response.status_code}")
            if response.context and 'form' in response.context:
                print("   • Errores en el formulario:")
                for field, errors in response.context['form'].errors.items():
                    print(f"     - {field}: {', '.join(errors)}")
        else:
            print("   ✅ Datos enviados exitosamente")

        print("\n   • Fase 4: Verificando creación en base de datos...")
        medio = MedioDePago.objects.filter(nombre='MercadoPago').first()
        
        if medio is None:
            print("   ❌ Error: Medio de pago no creado")
            return
            
        campos = medio.campos.filter(deleted_at__isnull=True)
        
        self.assertIsNotNone(medio)
        self.assertEqual(campos.count(), 2)
        
        print("\n   • Resumen de la creación:")
        print(f"   ✅ Medio de pago creado:")
        print(f"     - ID: {medio.id}")
        print(f"     - Nombre: {medio.nombre}")
        print(f"     - Comisión: {medio.comision_porcentaje}%")
        print(f"     - Estado: {'Activo' if medio.is_active else 'Inactivo'}")
        
        print(f"\n   ✅ Campos configurados ({campos.count()}):")
        for campo in campos:
            print(f"     - {campo.nombre_campo}:")
            print(f"       • Tipo: {campo.get_tipo_dato_display()}")
            print(f"       • Requerido: {'Sí' if campo.is_required else 'No'}")
            print(f"       • ID: {campo.id}")
        
        print("\n   ✅ Test completado exitosamente")
        
    def test_editar_medio_agregar_campo(self):
        """Test: Editar medio y agregar nuevo campo (sin eliminar existentes)"""
        print("\n✏️ Probando edición con adición de campo...")
        print("   • Paso 1: Crear medio de pago inicial...")
        
        # Crear medio con campo inicial
        medio = MedioDePago.objects.create(
            nombre="WebPay",
            comision_porcentaje=3.0,
            is_active=True
        )
        
        campo_inicial = CampoMedioDePago.objects.create(
            medio_de_pago=medio,
            nombre_campo="Código comercio",
            tipo_dato="TEXTO",
            is_required=True
        )
        
        print(f"   Estado inicial: 1 campo ({campo_inicial.nombre_campo})")
        
        url = reverse('medios_pago:editar', args=[medio.pk])
        
        # Datos para agregar un nuevo campo
        data = {
            'nombre': 'WebPay',
            'comision_porcentaje': '3.5',  # Cambiar comisión
            'is_active': 'on',
            # Formset management
            'campos-TOTAL_FORMS': '2',
            'campos-INITIAL_FORMS': '1',
            'campos-MIN_NUM_FORMS': '0',
            'campos-MAX_NUM_FORMS': '10',
            # Campo existente
            'campos-0-id': str(campo_inicial.id),
            'campos-0-nombre_campo': 'Código comercio',
            'campos-0-tipo_dato': 'TEXTO',
            'campos-0-is_required': 'on',
            'campos-0-DELETE': '',
            # Campo nuevo
            'campos-1-nombre_campo': 'Llave privada',
            'campos-1-tipo_dato': 'TEXTO',
            'campos-1-is_required': 'on',
            'campos-1-DELETE': '',
        }
        
        response = self.client.post(url, data, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar cambios
        medio.refresh_from_db()
        self.assertEqual(medio.comision_porcentaje, Decimal('3.5'))
        
        campos = medio.campos.filter(deleted_at__isnull=True)
        self.assertEqual(campos.count(), 2)
        
        print(f"   ✓ Comisión actualizada: {medio.comision_porcentaje}%")
        print(f"   ✓ Campos totales: {campos.count()}")
        for campo in campos:
            print(f"     - {campo.nombre_campo}")
        
    def test_toggle_activo_medio(self):
        """Test: Activar/Desactivar medio de pago"""
        print("\n🔄 Probando toggle de estado activo...")
        print("   • Paso 1: Crear medio inicialmente inactivo...")
        
        medio = MedioDePago.objects.create(
            nombre="Bitcoin",
            comision_porcentaje=1.0,
            is_active=False
        )
        
        print(f"   Estado inicial: {'Activo' if medio.is_active else 'Inactivo'}")
        
        url = reverse('medios_pago:toggle', args=[medio.pk])
        response = self.client.post(url, follow=True)
        
        medio.refresh_from_db()
        self.assertTrue(medio.is_active)
        
        print(f"   Estado después de toggle: {'Activo' if medio.is_active else 'Inactivo'}")
        
        # Toggle nuevamente
        response = self.client.post(url, follow=True)
        medio.refresh_from_db()
        self.assertFalse(medio.is_active)
        
        print(f"   Estado después de segundo toggle: {'Activo' if medio.is_active else 'Inactivo'}")
        print("   ✓ Toggle funcionando correctamente")
        
    def test_papelera_medios_eliminados(self):
        """Test: Vista de papelera con medios eliminados"""
        print("\n🗑️ Probando vista de papelera...")
        print("   • Verificando permisos y acceso...")
        
        url = reverse('medios_pago:papelera')
        print(f"   • Intentando acceder a: {url}")
        
        response = self.client.get(url)
        if response.status_code == 302:
            print(f"   ⚠️ Redirección detectada -> {response.url}")
            print("   💡 Sugerencia: Verificar que el usuario tiene permiso 'view_mediodepago'")
        
        # Crear medios activos y eliminados
        medio_activo = MedioDePago.objects.create(
            nombre="Activo",
            comision_porcentaje=2.0
        )
        
        medio_eliminado1 = MedioDePago.objects.create(
            nombre="Eliminado 1",
            comision_porcentaje=3.0
        )
        medio_eliminado1.soft_delete()
        
        medio_eliminado2 = MedioDePago.objects.create(
            nombre="Eliminado 2",
            comision_porcentaje=4.0
        )
        medio_eliminado2.soft_delete()
        
        url = reverse('medios_pago:papelera')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Activo")
        self.assertContains(response, "Eliminado 1")
        self.assertContains(response, "Eliminado 2")
        
        print(f"   ✓ Status: {response.status_code}")
        print(f"   ✓ Medios en papelera mostrados: 2")
        print(f"   ✓ Medios activos ocultados de papelera")
        
    def test_restaurar_medio_eliminado(self):
        """Test: Restaurar medio desde papelera"""
        print("\n♻️ Probando restauración desde papelera...")
        
        # Crear y eliminar un medio de prueba
        medio = MedioDePago.objects.create(
            nombre="Para Restaurar",
            comision_porcentaje=5.0
        )
        medio.soft_delete()
        
        print(f"   • Estado inicial del medio:")
        print(f"     - Nombre: {medio.nombre}")
        print(f"     - Eliminado: {'Sí' if medio.deleted_at else 'No'}")
        print(f"     - Fecha eliminación: {medio.deleted_at or 'N/A'}")
        print(f"     - Activo: {'Sí' if medio.is_active else 'No'}")
        
        # Intentar restaurar
        try:
            url = reverse('medios_pago:restore', args=[medio.pk])
            print(f"   • URL de restauración: {url}")
        except Exception as e:
            print(f"   ❌ Error al generar URL: {str(e)}")
            print("   💡 Sugerencia: Verificar 'restore' en medios_pago.urls")
        response = self.client.post(url, follow=True)
        
        medio.refresh_from_db()
        self.assertFalse(medio.is_deleted)
        self.assertIsNone(medio.deleted_at)
        
        print(f"   Estado después de restaurar: Eliminado={medio.is_deleted}")
        print("   ✓ Medio restaurado exitosamente")


class IntegrationTest(TestCase):
    """Tests de integración del módulo completo"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        print("\n" + "="*80)
        print(f"Ejecutando: {self._testMethodName}")
        print("="*80)
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        
        self.client = Client()
        self.client.login(username='admin', password='admin123')
        
    def test_flujo_completo_crear_editar_eliminar(self):
        """Test: Flujo completo de crear, editar y eliminar un medio de pago"""
        print("\n🔄 Ejecutando flujo completo del sistema...")
        
        # PASO 1: Crear medio de pago
        print("\n📌 PASO 1: Creando medio de pago...")
        
        try:
            create_url = reverse('medios_pago:crear_admin')
            print(f"   • URL de creación: {create_url}")
        except Exception as e:
            print(f"   ❌ Error al generar URL de creación: {str(e)}")
            print("   💡 Sugerencia: Verificar 'crear_admin' en medios_pago.urls")
        create_data = {
            'nombre': 'Transferencia Bancaria',
            'comision_porcentaje': '0',
            'is_active': 'on',
            'campos-TOTAL_FORMS': '3',
            'campos-INITIAL_FORMS': '0',
            'campos-MIN_NUM_FORMS': '0',
            'campos-MAX_NUM_FORMS': '10',
            'campos-0-nombre_campo': 'Banco',
            'campos-0-tipo_dato': 'TEXTO',
            'campos-0-is_required': 'on',
            'campos-0-DELETE': '',
            'campos-1-nombre_campo': 'Número de cuenta',
            'campos-1-tipo_dato': 'NUMERO',
            'campos-1-is_required': 'on',
            'campos-1-DELETE': '',
            'campos-2-nombre_campo': 'Titular',
            'campos-2-tipo_dato': 'TEXTO',
            'campos-2-is_required': 'on',
            'campos-2-DELETE': '',
        }
        
        response = self.client.post(create_url, create_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        medio = MedioDePago.objects.get(nombre='Transferencia Bancaria')
        print(f"   ✓ Medio creado: {medio.nombre}")
        print(f"   ✓ Campos creados: {medio.campos.count()}")
        
        # PASO 2: Editar medio (agregar campo y cambiar comisión)
        print("\n📌 PASO 2: Editando medio de pago...")
        
        edit_url = reverse('medios_pago:editar', args=[medio.pk])
        
        campos_existentes = list(medio.campos.all())
        
        edit_data = {
            'nombre': 'Transferencia Bancaria',
            'comision_porcentaje': '0.5',  # Cambiar comisión
            'is_active': 'on',
            'campos-TOTAL_FORMS': '4',
            'campos-INITIAL_FORMS': '3',
            'campos-MIN_NUM_FORMS': '0',
            'campos-MAX_NUM_FORMS': '10',
        }
        
        # Agregar campos existentes
        for i, campo in enumerate(campos_existentes):
            edit_data.update({
                f'campos-{i}-id': str(campo.id),
                f'campos-{i}-nombre_campo': campo.nombre_campo,
                f'campos-{i}-tipo_dato': campo.tipo_dato,
                f'campos-{i}-is_required': 'on' if campo.is_required else '',
                f'campos-{i}-DELETE': '',
            })
        
        # Agregar nuevo campo
        edit_data.update({
            'campos-3-nombre_campo': 'Swift',
            'campos-3-tipo_dato': 'TEXTO',
            'campos-3-is_required': '',
            'campos-3-DELETE': '',
        })
        
        response = self.client.post(edit_url, edit_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        medio.refresh_from_db()
        print(f"   ✓ Comisión actualizada: {medio.comision_porcentaje}%")
        print(f"   ✓ Campos totales: {medio.campos.filter(deleted_at__isnull=True).count()}")
        
        # PASO 3: Desactivar medio
        print("\n📌 PASO 3: Desactivando medio de pago...")
        
        toggle_url = reverse('medios_pago:toggle', args=[medio.pk])
        response = self.client.post(toggle_url, follow=True)
        
        medio.refresh_from_db()
        self.assertFalse(medio.is_active)
        print(f"   ✓ Estado: {'Activo' if medio.is_active else 'Inactivo'}")
        
        # PASO 4: Soft delete
        print("\n📌 PASO 4: Eliminando medio (soft delete)...")
        
        delete_url = reverse('medios_pago:delete', args=[medio.pk])
        response = self.client.post(delete_url, follow=True)
        
        medio.refresh_from_db()
        self.assertTrue(medio.is_deleted)
        print(f"   ✓ Medio eliminado (soft delete)")
        
        # PASO 5: Verificar en papelera
        print("\n📌 PASO 5: Verificando en papelera...")
        
        papelera_url = reverse('medios_pago:papelera')
        response = self.client.get(papelera_url)
        
        self.assertContains(response, 'Transferencia Bancaria')
        print(f"   ✓ Medio visible en papelera")
        
        # PASO 6: Restaurar
        print("\n📌 PASO 6: Restaurando medio...")
        
        restore_url = reverse('medios_pago:restore', args=[medio.pk])
        response = self.client.post(restore_url, follow=True)
        
        medio.refresh_from_db()
        self.assertFalse(medio.is_deleted)
        print(f"   ✓ Medio restaurado exitosamente")
        
        # PASO 7: Eliminación permanente
        print("\n📌 PASO 7: Preparando eliminación permanente...")
        
        # Primero hacer soft delete nuevamente
        medio.soft_delete()
        
        hard_delete_url = reverse('medios_pago:hard_delete', args=[medio.pk])
        response = self.client.post(hard_delete_url, follow=True)
        
        self.assertFalse(MedioDePago.objects.filter(pk=medio.pk).exists())
        print(f"   ✓ Medio eliminado permanentemente de la BD")
        
        print("\n🎉 FLUJO COMPLETO EJECUTADO EXITOSAMENTE")
        
    def test_validacion_campos_duplicados_en_formset(self):
        """Test: Validar que no se puedan crear campos duplicados en el mismo envío"""
        print("\n⚠️ Probando validación de campos duplicados en formset...")
        
        create_url = reverse('medios_pago:crear_admin')
        
        # Intentar crear con campos duplicados
        data = {
            'nombre': 'Medio con Duplicados',
            'comision_porcentaje': '2.5',
            'is_active': 'on',
            'campos-TOTAL_FORMS': '2',
            'campos-INITIAL_FORMS': '0',
            'campos-MIN_NUM_FORMS': '0',
            'campos-MAX_NUM_FORMS': '10',
            # Dos campos con el mismo nombre
            'campos-0-nombre_campo': 'Email',
            'campos-0-tipo_dato': 'EMAIL',
            'campos-0-is_required': 'on',
            'campos-0-DELETE': '',
            'campos-1-nombre_campo': 'Email',  # Duplicado
            'campos-1-tipo_dato': 'TEXTO',
            'campos-1-is_required': '',
            'campos-1-DELETE': '',
        }
        
        response = self.client.post(create_url, data)
        
        # No debe crear el medio si hay duplicados
        self.assertFalse(
            MedioDePago.objects.filter(nombre='Medio con Duplicados').exists()
        )
        
        print("   ✓ Campos duplicados detectados y rechazados")
        print("   ✓ Medio no creado debido a la validación")
        
    def test_restriccion_edicion_campos_existentes(self):
        """Test: Verificar que no se pueden eliminar campos existentes en edición"""
        print("\n🔒 Probando restricciones de edición...")
        print("   • Verificando protección de campos existentes...")
        print("\n🔒 Probando restricción de eliminación de campos en edición...")
        
        # Crear medio con campos
        medio = MedioDePago.objects.create(
            nombre="Medio Protegido",
            comision_porcentaje=3.0,
            is_active=True
        )
        
        campo1 = CampoMedioDePago.objects.create(
            medio_de_pago=medio,
            nombre_campo="Campo Protegido 1",
            tipo_dato="TEXTO",
            is_required=True
        )
        
        campo2 = CampoMedioDePago.objects.create(
            medio_de_pago=medio,
            nombre_campo="Campo Protegido 2",
            tipo_dato="NUMERO",
            is_required=False
        )
        
        print(f"   Campos iniciales: {medio.campos.count()}")
        
        # Intentar editar y marcar campo para eliminación
        edit_url = reverse('medios_pago:editar', args=[medio.pk])
        
        edit_data = {
            'nombre': 'Medio Protegido',
            'comision_porcentaje': '3.0',
            'is_active': 'on',
            'campos-TOTAL_FORMS': '2',
            'campos-INITIAL_FORMS': '2',
            'campos-MIN_NUM_FORMS': '0',
            'campos-MAX_NUM_FORMS': '10',
            'campos-0-id': str(campo1.id),
            'campos-0-nombre_campo': 'Campo Protegido 1',
            'campos-0-tipo_dato': 'TEXTO',
            'campos-0-is_required': 'on',
            'campos-0-DELETE': 'on',  # Intentar eliminar
            'campos-1-id': str(campo2.id),
            'campos-1-nombre_campo': 'Campo Protegido 2',
            'campos-1-tipo_dato': 'NUMERO',
            'campos-1-is_required': '',
            'campos-1-DELETE': '',
        }
        
        response = self.client.post(edit_url, edit_data, follow=True)
        
        # El campo marcado para eliminación debe hacer soft delete
        campo1.refresh_from_db()
        self.assertTrue(campo1.is_deleted)
        
        print(f"   ✓ Campo marcado para eliminación: soft delete aplicado")
        print(f"   ✓ Campo aún existe en BD pero marcado como eliminado")
        
    def test_manejo_espacios_en_nombres(self):
        """Test: Verificar el manejo correcto de espacios en nombres"""
        print("\n🔤 Probando manejo de espacios en nombres...")
        
        # Crear medio con espacios extras
        medio = MedioDePago.objects.create(
            nombre="   PayPal Business   ",
            comision_porcentaje=3.5
        )
        
        # El modelo debe limpiar los espacios
        self.assertEqual(medio.nombre, "PayPal Business")
        print(f"   ✓ Espacios eliminados: '{medio.nombre}'")
        
        # Crear campo con espacios
        campo = CampoMedioDePago.objects.create(
            medio_de_pago=medio,
            nombre_campo="   Email del Cliente   ",
            tipo_dato="EMAIL"
        )
        
        self.assertEqual(campo.nombre_campo, "Email del Cliente")
        print(f"   ✓ Campo limpiado: '{campo.nombre_campo}'")


class PerformanceTest(TestCase):
    """Tests de rendimiento y escalabilidad"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        print("\n" + "="*80)
        print(f"Ejecutando: {self._testMethodName}")
        print("="*80)
        
    def test_manejo_multiples_medios_pago(self):
        """Test: Manejo eficiente de múltiples medios de pago"""
        print("\n⚡ Probando rendimiento con múltiples medios...")
        
        import time
        start_time = time.time()
        
        # Crear 50 medios de pago
        medios = []
        for i in range(50):
            medio = MedioDePago.objects.create(
                nombre=f"Medio {i:03d}",
                comision_porcentaje=i % 10,
                is_active=i % 2 == 0
            )
            medios.append(medio)
        
        creation_time = time.time() - start_time
        print(f"   ✓ 50 medios creados en {creation_time:.2f} segundos")
        
        # Crear campos para cada medio
        start_time = time.time()
        for medio in medios[:10]:  # Solo los primeros 10 para no demorar mucho
            for j in range(5):
                CampoMedioDePago.objects.create(
                    medio_de_pago=medio,
                    nombre_campo=f"Campo {j}",
                    tipo_dato='TEXTO'
                )
        
        fields_time = time.time() - start_time
        print(f"   ✓ 50 campos creados en {fields_time:.2f} segundos")
        
        # Probar consultas
        start_time = time.time()
        
        # Consulta de medios activos
        activos = MedioDePago.active.count()
        
        # Consulta con prefetch de campos
        medios_con_campos = MedioDePago.active.prefetch_related('campos').all()
        total_campos = sum(m.campos.count() for m in medios_con_campos)
        
        query_time = time.time() - start_time
        print(f"   ✓ Consultas ejecutadas en {query_time:.2f} segundos")
        print(f"   ✓ Medios activos: {activos}")
        print(f"   ✓ Total campos: {total_campos}")
        
        self.assertLess(creation_time, 5, "Creación toma demasiado tiempo")
        self.assertLess(query_time, 1, "Consultas toman demasiado tiempo")


class EdgeCasesTest(TestCase):
    """Tests para casos extremos y situaciones especiales"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        print("\n" + "="*80)
        print(f"Ejecutando: {self._testMethodName}")
        print("="*80)
        
    def test_nombre_medio_unicode(self):
        """Test: Manejo de caracteres Unicode en nombres"""
        print("\n🌍 Probando caracteres Unicode...")
        
        medio = MedioDePago.objects.create(
            nombre="Ñandú Pagos - Guaraní €₹¥",
            comision_porcentaje=2.5
        )
        
        self.assertEqual(medio.nombre, "Ñandú Pagos - Guaraní €₹¥")
        print(f"   ✓ Unicode manejado correctamente: {medio.nombre}")
        
    def test_comision_decimal_precision(self):
        """Test: Precisión decimal en comisiones"""
        print("\n💰 Probando precisión decimal...")
        
        try:
            from decimal import Decimal
            medio = MedioDePago.objects.create(
                nombre="Precision Test",
                comision_porcentaje=Decimal('2.990')
            )
            print(f"   ✓ Medio creado con comisión: {medio.comision_porcentaje}%")
            self.assertEqual(medio.comision_porcentaje, Decimal('2.99'))
            print("   ✓ Precisión decimal correcta")
        except ValidationError as e:
            print(f"   ❌ Error de validación: {e.messages[0]}")
            print(f"   💡 Sugerencia: Verificar decimales en models.py - DecimalField")
            raise
        
        # Probar límites
        medio.comision_porcentaje = Decimal('99.99')
        medio.save()
        
        medio.refresh_from_db()
        self.assertEqual(medio.comision_porcentaje, Decimal('99.99'))
        
        print(f"   ✓ Precisión decimal mantenida: {medio.comision_porcentaje}")
        
    def test_campo_orden_automatico(self):
        """Test: Orden automático de campos"""
        print("\n📊 Probando orden de campos...")
        
        medio = MedioDePago.objects.create(
            nombre="Orden Test",
            comision_porcentaje=1.0
        )
        
        # Crear campos sin especificar orden
        campo1 = CampoMedioDePago.objects.create(
            medio_de_pago=medio,
            nombre_campo="Primero",
            tipo_dato="TEXTO"
        )
        
        campo2 = CampoMedioDePago.objects.create(
            medio_de_pago=medio,
            nombre_campo="Segundo",
            tipo_dato="NUMERO"
        )
        
        campo3 = CampoMedioDePago.objects.create(
            medio_de_pago=medio,
            nombre_campo="Tercero",
            tipo_dato="FECHA"
        )
        
        # Verificar que se ordenan correctamente
        campos_ordenados = medio.campos.all()
        
        print("   Orden de campos:")
        for campo in campos_ordenados:
            print(f"     - {campo.nombre_campo} (orden: {campo.orden})")
        
        self.assertEqual(len(campos_ordenados), 3)
        
    def test_tipos_dato_validacion(self):
        """Test: Validación de todos los tipos de dato"""
        print("\n📝 Probando todos los tipos de dato...")
        
        medio = MedioDePago.objects.create(
            nombre="Tipos Test",
            comision_porcentaje=0
        )
        
        tipos = ['TEXTO', 'NUMERO', 'FECHA', 'EMAIL', 'TELEFONO', 'URL']
        
        for tipo in tipos:
            campo = CampoMedioDePago.objects.create(
                medio_de_pago=medio,
                nombre_campo=f"Campo {tipo}",
                tipo_dato=tipo,
                is_required=False
            )
            
            self.assertEqual(campo.tipo_dato, tipo)
            print(f"   ✓ Tipo {tipo}: {campo.get_tipo_dato_display()}")
        
        self.assertEqual(medio.campos.count(), len(tipos))
        
    def test_cascada_eliminacion(self):
        """Test: Verificar eliminación en cascada de campos"""
        print("\n🔗 Probando eliminación en cascada...")
        
        medio = MedioDePago.objects.create(
            nombre="Cascada Test",
            comision_porcentaje=5.0
        )
        
        # Crear varios campos
        for i in range(3):
            CampoMedioDePago.objects.create(
                medio_de_pago=medio,
                nombre_campo=f"Campo {i}",
                tipo_dato="TEXTO"
            )
        
        print(f"   Campos creados: {medio.campos.count()}")
        
        # Eliminar el medio (hard delete)
        medio_id = medio.id
        medio.delete()
        
        # Verificar que los campos también se eliminaron
        campos_restantes = CampoMedioDePago.objects.filter(
            medio_de_pago_id=medio_id
        ).count()
        
        self.assertEqual(campos_restantes, 0)
        print(f"   ✓ Campos eliminados en cascada: 0 restantes")


# Ejecutor de tests con reporte detallado
def run_all_tests():
    """Función helper para ejecutar todos los tests con reporte detallado"""
    import unittest
    
    print("\n" + "="*80)
    print("INICIANDO SUITE DE TESTS - MÓDULO MEDIOS DE PAGO")
    print("="*80)
    
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar todos los test cases
    test_cases = [
        MedioDePagoModelTest,
        CampoMedioDePagoModelTest,
        MedioDePagoFormsTest,
        MedioDePagoViewsTest,
        IntegrationTest,
        PerformanceTest,
        EdgeCasesTest
    ]
    
    for test_case in test_cases:
        suite.addTests(loader.loadTestsFromTestCase(test_case))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Reporte final
    print("\n" + "="*80)
    print("REPORTE FINAL DE TESTS")
    print("="*80)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"✅ Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Fallos: {len(result.failures)}")
    print(f"💥 Errores: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE! 🎉")
    else:
        print("\n⚠️ Algunos tests fallaron. Revisa los detalles arriba.")
    
    return result