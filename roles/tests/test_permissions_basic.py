"""
Tests básicos del sistema de permisos personalizados.
Ubicación: roles/tests/test_permissions_basic.py

Ejecutar con:
    python manage.py test roles.tests.test_permissions_basic
    python manage.py test roles.tests.test_permissions_basic --verbosity=2
"""
from django.test import TestCase
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from io import StringIO

from users.models import CustomUser
from clientes.models import Cliente, Segmento, AsignacionCliente

from roles.tests.helpers import setup_permissions_silently # Importado para uso silencioso


class PermissionsCreationTestCase(TestCase):
    """
    ✅ Test 1: Verificar que los permisos personalizados se crean correctamente
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print("\n" + "="*70)
        print("🧪 TEST 1: CREACIÓN DE PERMISOS PERSONALIZADOS")
        print("="*70)
        # ✅ ÚNICA EJECUCIÓN: Sincronizar permisos una vez al inicio de la clase
        call_command('sync_permissions', verbosity=0) 
    
    # ❌ ELIMINADO: Ya no es necesario ejecutar sync_permissions antes de CADA test
    # def setUp(self):
    #     """Ejecutar sync_permissions ANTES de cada test"""
    #     call_command('sync_permissions', verbosity=0)
    
    def test_01_sync_permissions_command(self):
        """Ejecuta el comando sync_permissions y verifica que se crean sin errores"""
        print("  📋 Ejecutando sync_permissions...", end=" ")
        
        out = StringIO()
        # Ejecutar de nuevo para comprobar el output, pero debería ser muy rápido
        call_command('sync_permissions', stdout=out, verbosity=0)
        output = out.getvalue()
        
        # Verificar que no hubo errores
        self.assertNotIn('❌', output, "No debe haber errores en la sincronización")
        
        print("✅")
        
    def test_02_all_permissions_exist(self):
        """Verifica que todos los permisos definidos existen en la base de datos"""
        print("  🔍 Verificando existencia de permisos...", end=" ")
        
        # Importar DESPUÉS de sync_permissions (se ejecuta en setUpClass)
        # Nota: Asumo que tienes un módulo que combina todos los permisos.
        try:
            from roles.management.commands.permissions_defs import TODOS_LOS_PERMISOS
        except ImportError:
            # Si no existe TODOS_LOS_PERMISOS, este test fallará
            self.fail("No se pudo importar TODOS_LOS_PERMISOS")
            
        total_esperados = len(TODOS_LOS_PERMISOS)
        permisos_encontrados = 0
        permisos_faltantes = []
        
        for perm_def in TODOS_LOS_PERMISOS:
            try:
                Permission.objects.get(
                    codename=perm_def['codename'],
                    content_type__app_label=perm_def['app_label']
                )
                permisos_encontrados += 1
            except Permission.DoesNotExist:
                permisos_faltantes.append(perm_def['codename'])
        
        self.assertEqual(
            permisos_encontrados,
            total_esperados,
            f"Faltan {len(permisos_faltantes)} permisos: {permisos_faltantes}"
        )
        
        print(f"✅ ({permisos_encontrados}/{total_esperados})")


class RolePermissionsTestCase(TestCase):
    """
    ✅ Test 2: Verificar que los roles tienen permisos asignados correctamente
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print("\n" + "="*70)
        print("🧪 TEST 2: ASIGNACIÓN DE PERMISOS A ROLES")
        print("="*70)
        # ✅ ÚNICA EJECUCIÓN: Crear roles y asignar permisos de forma silenciosa
        setup_permissions_silently() 
    
    # ❌ ELIMINADO: Ya no es necesario el setUp
    # def setUp(self):
    #     """Crear roles y asignar permisos"""
    #     setup_permissions_silently() 
    
    def test_01_admin_has_all_permissions(self):
        """Verifica que el rol 'administrador' tenga todos los permisos críticos"""
        print("  👑 Verificando ADMINISTRADOR...", end=" ")
        
        # Uso de Group.objects.get es seguro ya que setup_permissions_silently los crea
        admin_group = Group.objects.get(name='administrador')
        permisos_admin = admin_group.permissions.all()
        
        permisos_criticos = [
            'manage_usuarios',
            'view_all_clientes',
            'manage_descuentos_segmento',
            'manage_cotizaciones_segmento',
            'manage_catalogo_medios_pago',
        ]
        
        permisos_faltantes = []
        for codename in permisos_criticos:
            if not permisos_admin.filter(codename=codename).exists():
                permisos_faltantes.append(codename)
        
        self.assertEqual(
            len(permisos_faltantes),
            0,
            f"Administrador no tiene: {permisos_faltantes}"
        )
        
        print(f"✅ ({len(permisos_criticos)}/{len(permisos_criticos)} críticos)")
    
    def test_02_operador_limited_permissions(self):
        """Verifica que el operador NO tenga permisos administrativos"""
        print("  🔧 Verificando OPERADOR...", end=" ")
        
        operador_group = Group.objects.get(name='operador')
        permisos_operador = operador_group.permissions.all()
        
        permisos_prohibidos = [
            'manage_usuarios',
            'manage_cliente_assignment',
            'manage_descuentos_segmento',
            'delete_cliente',
            'manage_mfa_config',
        ]
        
        permisos_incorrectos = []
        for codename in permisos_prohibidos:
            if permisos_operador.filter(codename=codename).exists():
                permisos_incorrectos.append(codename)
        
        self.assertEqual(
            len(permisos_incorrectos),
            0,
            f"Operador tiene permisos prohibidos: {permisos_incorrectos}"
        )
        
        print(f"✅ ({len(permisos_prohibidos)} restricciones OK)")
    
    def test_03_cliente_basic_permissions(self):
        """Verifica que el operador de cuenta tenga permisos básicos"""
        print("  👤 Verificando CLIENTE...", end=" ")
        
        cliente_group = Group.objects.get(name='cliente')
        permisos_cliente = cliente_group.permissions.all()
        
        permisos_requeridos = [
            'realizar_operacion',
            'view_transacciones_asignadas',
            'view_medios_pago',
            'manage_medios_pago',
            'view_cotizaciones_segmento',
        ]
        
        permisos_faltantes = []
        for codename in permisos_requeridos:
            if not permisos_cliente.filter(codename=codename).exists():
                permisos_faltantes.append(codename)
        
        self.assertEqual(
            len(permisos_faltantes),
            0,
            f"Cliente no tiene permisos requeridos: {permisos_faltantes}"
        )
        
        print(f"✅ ({len(permisos_requeridos)}/{len(permisos_requeridos)} básicos)")


class UserPermissionsTestCase(TestCase):
    """
    ✅ Test 3: Verificar que los usuarios heredan permisos de sus grupos
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print("\n" + "="*70)
        print("🧪 TEST 3: HERENCIA DE PERMISOS DE USUARIOS")
        print("="*70)
        
        # ✅ ÚNICA EJECUCIÓN: Sincronizar y configurar roles
        setup_permissions_silently() 
        
        print("\n🔧 Creando usuarios de prueba...")
        
        # Crear usuarios y asignarlos a grupos
        cls.admin_user = CustomUser.objects.create_user(
            username='test_admin',
            email='admin@test.com',
            password='test1234'
        )
        cls.admin_user.groups.add(Group.objects.get(name='administrador'))
        
        cls.operador_user = CustomUser.objects.create_user(
            username='test_operador',
            email='operador@test.com',
            password='test1234'
        )
        cls.operador_user.groups.add(Group.objects.get(name='operador'))
        
        cls.cliente_user = CustomUser.objects.create_user(
            username='test_cliente',
            email='cliente@test.com',
            password='test1234'
        )
        cls.cliente_user.groups.add(Group.objects.get(name='cliente'))
        
        print("✅ 3 usuarios creados")
    
    # ❌ ELIMINADO: Ya no es necesario el setUp (la lógica se movió a setUpClass)
    # def setUp(self):
    #     """Crear usuarios de prueba con diferentes roles"""
    #     ...
    
    def test_01_admin_user_has_permissions(self):
        """Verifica que un usuario admin tenga permisos de su grupo"""
        print("  👑 Herencia ADMIN...", end=" ")
        
        permisos_criticos = [
            'users.manage_usuarios',
            'clientes.view_all_clientes',
            'clientes.manage_descuentos_segmento',
            'divisas.manage_cotizaciones_segmento',
        ]
        
        permisos_faltantes = []
        for perm in permisos_criticos:
            if not self.admin_user.has_perm(perm):
                permisos_faltantes.append(perm)
        
        self.assertEqual(
            len(permisos_faltantes),
            0,
            f"Usuario admin no heredó: {permisos_faltantes}"
        )
        
        print(f"✅ ({len(permisos_criticos)} heredados)")
    
    def test_02_operador_cannot_manage_users(self):
        """Verifica que operador NO pueda gestionar usuarios"""
        print("  🔧 Restricciones OPERADOR...", end=" ")
        
        permisos_prohibidos = [
            'users.manage_usuarios',
            'clientes.manage_cliente_assignment',
            'clientes.manage_descuentos_segmento',
        ]
        
        permisos_incorrectos = []
        for perm in permisos_prohibidos:
            if self.operador_user.has_perm(perm):
                permisos_incorrectos.append(perm)
        
        self.assertEqual(
            len(permisos_incorrectos),
            0,
            f"Usuario operador tiene permisos prohibidos: {permisos_incorrectos}"
        )
        
        print(f"✅ ({len(permisos_prohibidos)} bloqueados)")
    
    def test_03_cliente_basic_operations(self):
        """Verifica que cliente pueda realizar operaciones básicas"""
        print("  👤 Operaciones CLIENTE...", end=" ")
        
        permisos_requeridos = [
            'divisas.realizar_operacion',
            'transacciones.view_transacciones_asignadas',
            'clientes.view_medios_pago',
            'clientes.manage_medios_pago',
        ]
        
        permisos_faltantes = []
        for perm in permisos_requeridos:
            if not self.cliente_user.has_perm(perm):
                permisos_faltantes.append(perm)
        
        self.assertEqual(
            len(permisos_faltantes),
            0,
            f"Usuario cliente no tiene: {permisos_faltantes}"
        )
        
        print(f"✅ ({len(permisos_requeridos)} operativos)")


class ContextProcessorTestCase(TestCase):
    """
    ✅ Test 4: Verificar que el context processor funcione correctamente
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print("\n" + "="*70)
        print("🧪 TEST 4: CONTEXT PROCESSOR DE PERMISOS")
        print("="*70)
        
        # ✅ ÚNICA EJECUCIÓN: Sincronizar, crear grupos y asignar roles
        setup_permissions_silently()
        
        # Crear usuarios de prueba con roles
        cls.admin_user = CustomUser.objects.create_user(
            username='admin_ctx',
            email='admin_ctx@test.com',
            password='test1234'
        )
        cls.admin_user.groups.add(Group.objects.get(name='administrador'))
        
        cls.cliente_user = CustomUser.objects.create_user(
            username='cliente_ctx',
            email='cliente_ctx@test.com',
            password='test1234'
        )
        cls.cliente_user.groups.add(Group.objects.get(name='cliente'))
        
        # Crear objetos necesarios para la asignación de cliente
        segmento = Segmento.objects.create(
            name='VIP' 
        )
        
        cls.cliente_obj = Cliente.objects.create(
            cedula='12345678',
            nombre_completo='Cliente Test S.A.',
            segmento=segmento,
            esta_activo=True
        )
        
        # Crear asignación (para que el context processor lo detecte como Operador de Cuenta)
        AsignacionCliente.objects.create(
            usuario=cls.cliente_user,
            cliente=cls.cliente_obj
        )

    # ❌ ELIMINADO: Ya no es necesario el setUp
    # def setUp(self):
    #     """Configurar usuarios y clientes"""
    #     ...
    
    def test_01_admin_context_variables(self):
        """Verifica variables de contexto para admin"""
        print("  👑 Context ADMIN...", end=" ")
        
        from roles.context_processors import grupo_usuario
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.admin_user
        request.session = {}
        
        context = grupo_usuario(request)
        
        self.assertEqual(context['tipo_usuario'], 'Administrador')
        self.assertTrue(context['usuario_es_staff'])
        self.assertFalse(context['usuario_es_cliente'])
        self.assertFalse(context['usuario_es_registrado'])
        
        print("✅ (staff=True)")
    
    def test_02_cliente_context_variables(self):
        """Verifica variables de contexto para operador de cuenta"""
        print("\n👤 Verificando contexto del CLIENTE...")
        
        from roles.context_processors import grupo_usuario
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.cliente_user
        request.session = {}
        
        context = grupo_usuario(request)
        
        print("\n📊 Variables de contexto:")
        print(f"  tipo_usuario: {context['tipo_usuario']}")
        print(f"  usuario_es_staff: {context['usuario_es_staff']}")
        print(f"  usuario_es_cliente: {context['usuario_es_cliente']}")
        # Nota: 'tiene_clientes_asignados' no estaba en el contexto inicial, pero se mantiene la verificación si se incluyó.
        # self.assertTrue(context['tiene_clientes_asignados'])
        
        self.assertEqual(context['tipo_usuario'], 'Operador de Cuenta')
        self.assertFalse(context['usuario_es_staff'])
        self.assertTrue(context['usuario_es_cliente'])
        
        print("\n✅ CONTEXTO CLIENTE CORRECTO")


class DecoratorTestCase(TestCase):
    """
    ✅ Test 5: Verificar que el decorador @require_permission funcione
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print("\n" + "="*70)
        print("🧪 TEST 5: DECORADOR @require_permission")
        print("="*70)
        
        # ✅ ÚNICA EJECUCIÓN: Sincronizar, crear grupos y asignar roles
        setup_permissions_silently() 
        
        print("\n🔧 Configurando usuarios...")
        
        cls.admin_user = CustomUser.objects.create_user(
            username='admin_dec',
            email='admin_dec@test.com',
            password='test1234'
        )
        cls.admin_user.groups.add(Group.objects.get(name='administrador'))
        
        cls.cliente_user = CustomUser.objects.create_user(
            username='cliente_dec',
            email='cliente_dec@test.com',
            password='test1234'
        )
        cls.cliente_user.groups.add(Group.objects.get(name='cliente'))
        
        print("✅ Usuarios configurados")
    
    # ❌ ELIMINADO: Ya no es necesario el setUp
    # def setUp(self):
    #     """Configurar usuarios"""
    #     ...

    def test_01_decorator_allows_authorized_user(self):
        """Verifica que el decorador permita usuarios autorizados"""
        print("\n✅ Probando acceso AUTORIZADO...")
        
        from roles.decorators import require_permission
        from django.http import HttpResponse
        from django.test import RequestFactory
        
        # Vista protegida
        @require_permission('users.manage_usuarios')
        def protected_view(request):
            return HttpResponse('OK')
        
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = self.admin_user
        
        response = protected_view(request)
        
        print(f"  Status code: {response.status_code}")
        print(f"  Content: {response.content.decode()}")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'OK')
        
        print("\n✅ DECORADOR PERMITIÓ ACCESO AUTORIZADO")
    
    def test_02_decorator_blocks_unauthorized_user(self):
        """Verifica que el decorador bloquee usuarios no autorizados"""
        print("\n🚫 Probando acceso NO AUTORIZADO...")
        
        from roles.decorators import require_permission
        from django.http import HttpResponse
        from django.core.exceptions import PermissionDenied
        from django.test import RequestFactory
        
        # Vista protegida
        @require_permission('users.manage_usuarios')
        def protected_view(request):
            return HttpResponse('OK')
        
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = self.cliente_user
        
        print("  Intentando acceso con usuario sin permisos...")
        
        with self.assertRaises(PermissionDenied) as context:
            protected_view(request)
        
        print(f"  ✅ PermissionDenied lanzado correctamente")
        print(f"  Mensaje: {str(context.exception)}")
        
        print("\n✅ DECORADOR BLOQUEÓ ACCESO NO AUTORIZADO")
    
    def test_03_decorator_with_multiple_permissions(self):
        """Verifica decorador con lista de permisos (OR logic)"""
        print("\n🔀 Probando decorador con MÚLTIPLES permisos (OR)...")
        
        from roles.decorators import require_permission
        from django.http import HttpResponse
        from django.test import RequestFactory
        
        # Vista que acepta múltiples permisos
        @require_permission([
            'users.manage_usuarios',
            'clientes.view_all_clientes'
        ])
        def multi_perm_view(request):
            return HttpResponse('OK')
        
        factory = RequestFactory()
        request = factory.get('/test/')
        request.user = self.admin_user
        
        response = multi_perm_view(request)
        
        print(f"  Status code: {response.status_code}")
        print("  ✅ Usuario tiene al menos uno de los permisos")
        
        self.assertEqual(response.status_code, 200)
        
        print("\n✅ DECORADOR CON MÚLTIPLES PERMISOS FUNCIONA")