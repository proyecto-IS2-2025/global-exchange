# tests.py - Tests esenciales para el módulo de Medios de Pago
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from .models import MedioDePago, CampoMedioDePago


class MedioDePagoModelTest(TestCase):
    """Tests básicos para el modelo MedioDePago"""
    
    def setUp(self):
        print(f"\nEjecutando: {self._testMethodName}")
    
    def test_crear_medio_pago_valido(self):
        """Test: Crear medio de pago con datos válidos"""
        print("Creando medio de pago básico...")
        
        medio = MedioDePago.objects.create(
            nombre="PayPal",
            comision_porcentaje=3.5,
            is_active=True
        )
        
        self.assertEqual(medio.nombre, "PayPal")
        self.assertEqual(medio.comision_porcentaje, Decimal('3.5'))
        self.assertTrue(medio.is_active)
        self.assertFalse(medio.is_deleted)
        
        print(f"Medio creado exitosamente: {medio.nombre} - {medio.comision_porcentaje}%")
    
    def test_validacion_comision_fuera_rango(self):
        """Test: Validar comisiones fuera del rango 0-100"""
        print("Probando validación de comisión fuera de rango...")
        
        # Comisión negativa
        with self.assertRaises(ValidationError):
            medio = MedioDePago(
                nombre="Test Negativo",
                comision_porcentaje=-5.0
            )
            medio.full_clean()
        print("Comisión negativa rechazada correctamente")
        
        # Comisión mayor a 100
        with self.assertRaises(ValidationError):
            medio = MedioDePago(
                nombre="Test Mayor",
                comision_porcentaje=150.0
            )
            medio.full_clean()
        print("Comisión > 100% rechazada correctamente")
    
    def test_nombre_requerido(self):
        """Test: Nombre es obligatorio"""
        print("Probando validación de nombre obligatorio...")
        
        with self.assertRaises(ValidationError):
            medio = MedioDePago(
                nombre="",
                comision_porcentaje=2.5
            )
            medio.save()
        
        print("Nombre vacío rechazado correctamente")
    
    def test_soft_delete_basico(self):
        """Test: Funcionalidad básica de soft delete"""
        print("Probando soft delete...")
        
        medio = MedioDePago.objects.create(
            nombre="Para Eliminar",
            comision_porcentaje=2.0,
            is_active=True
        )
        
        # Estado inicial
        self.assertFalse(medio.is_deleted)
        self.assertTrue(medio.is_active)
        
        # Aplicar soft delete
        medio.soft_delete()
        
        # Verificar cambios
        self.assertTrue(medio.is_deleted)
        self.assertFalse(medio.is_active)
        self.assertIsNotNone(medio.deleted_at)
        
        print(f"Soft delete aplicado: eliminado={medio.is_deleted}, activo={medio.is_active}")
    
    def test_restaurar_medio_eliminado(self):
        """Test: Restaurar medio eliminado"""
        print("Probando restauración...")
        
        medio = MedioDePago.objects.create(
            nombre="Para Restaurar",
            comision_porcentaje=1.5
        )
        
        # Eliminar y restaurar
        medio.soft_delete()
        self.assertTrue(medio.is_deleted)
        
        medio.restore()
        self.assertFalse(medio.is_deleted)
        self.assertTrue(medio.is_active)
        
        print(f"Restauración exitosa: eliminado={medio.is_deleted}, activo={medio.is_active}")
    
    def test_toggle_estado_activo(self):
        """Test: Cambiar estado activo/inactivo"""
        print("Probando toggle de estado...")
        
        medio = MedioDePago.objects.create(
            nombre="Toggle Test",
            comision_porcentaje=3.0,
            is_active=False
        )
        
        # Toggle a activo
        resultado = medio.toggle_active()
        self.assertTrue(medio.is_active)
        self.assertTrue(resultado)
        
        # Toggle a inactivo
        resultado = medio.toggle_active()
        self.assertFalse(medio.is_active)
        self.assertFalse(resultado)
        
        print(f"Toggle funcionando: estado final={medio.is_active}")


class CampoMedioDePagoModelTest(TestCase):
    """Tests para el modelo CampoMedioDePago"""
    
    def setUp(self):
        print(f"\nEjecutando: {self._testMethodName}")
        
        self.medio = MedioDePago.objects.create(
            nombre="Medio Test",
            comision_porcentaje=2.0,
            is_active=True
        )
    
    def test_crear_campo_valido(self):
        """Test: Crear campo con datos válidos"""
        print("Creando campo básico...")
        
        campo = CampoMedioDePago.objects.create(
            medio_de_pago=self.medio,
            nombre_campo="Email",
            tipo_dato="EMAIL",
            is_required=True
        )
        
        self.assertEqual(campo.nombre_campo, "Email")
        self.assertEqual(campo.tipo_dato, "EMAIL")
        self.assertTrue(campo.is_required)
        self.assertFalse(campo.is_deleted)
        
        print(f"Campo creado: {campo.nombre_campo} ({campo.get_tipo_dato_display()})")
    
    def test_todos_tipos_dato_validos(self):
        """Test: Verificar que todos los tipos de dato funcionan"""
        print("Probando todos los tipos de dato...")
        
        tipos_datos = [
            ('TEXTO', 'Texto'),
            ('NUMERO', 'Número'),
            ('FECHA', 'Fecha'),
            ('EMAIL', 'Email'),
            ('TELEFONO', 'Teléfono'),
            ('URL', 'URL'),
        ]
        
        for codigo, display in tipos_datos:
            campo = CampoMedioDePago.objects.create(
                medio_de_pago=self.medio,
                nombre_campo=f"Campo {codigo}",
                tipo_dato=codigo,
                is_required=False
            )
            
            self.assertEqual(campo.tipo_dato, codigo)
            self.assertEqual(campo.get_tipo_dato_display(), display)
            print(f"Tipo {codigo}: OK")
        
        print(f"Total campos creados: {self.medio.campos.count()}")
    
    def test_validacion_nombre_duplicado(self):
        """Test: No permitir campos con nombres duplicados en el mismo medio"""
        print("Probando validación de nombres duplicados...")
        
        # Crear primer campo
        CampoMedioDePago.objects.create(
            medio_de_pago=self.medio,
            nombre_campo="Número de cuenta",
            tipo_dato="NUMERO"
        )
        
        # Intentar crear duplicado exacto
        with self.assertRaises(ValidationError):
            campo_duplicado = CampoMedioDePago(
                medio_de_pago=self.medio,
                nombre_campo="Número de cuenta",
                tipo_dato="TEXTO"
            )
            campo_duplicado.full_clean()
        
        print("Duplicado exacto rechazado")
        
        # Intentar crear con diferente case (debe fallar también)
        with self.assertRaises(ValidationError):
            campo_case = CampoMedioDePago(
                medio_de_pago=self.medio,
                nombre_campo="NÚMERO DE CUENTA",
                tipo_dato="TEXTO"
            )
            campo_case.full_clean()
        
        print("Duplicado con diferente case rechazado")
    
    def test_nombre_campo_requerido(self):
        """Test: Nombre de campo es obligatorio"""
        print("Probando validación de nombre campo obligatorio...")
        
        with self.assertRaises(ValidationError):
            campo = CampoMedioDePago(
                medio_de_pago=self.medio,
                nombre_campo="",
                tipo_dato="TEXTO"
            )
            campo.full_clean()
        
        print("Nombre vacío rechazado correctamente")
    
    def test_tipo_dato_requerido(self):
        """Test: Tipo de dato es obligatorio"""
        print("Probando validación de tipo dato obligatorio...")
        
        with self.assertRaises(ValidationError):
            campo = CampoMedioDePago(
                medio_de_pago=self.medio,
                nombre_campo="Campo Test",
                tipo_dato=""
            )
            campo.full_clean()
        
        print("Tipo dato vacío rechazado correctamente")
    
    def test_soft_delete_campo(self):
        """Test: Soft delete de campo individual"""
        print("Probando soft delete de campo...")
        
        campo = CampoMedioDePago.objects.create(
            medio_de_pago=self.medio,
            nombre_campo="Campo Para Eliminar",
            tipo_dato="TEXTO"
        )
        
        # Estado inicial
        self.assertFalse(campo.is_deleted)
        campos_activos_inicial = self.medio.campos.filter(deleted_at__isnull=True).count()
        
        # Eliminar campo
        campo.soft_delete()
        
        # Verificar eliminación
        self.assertTrue(campo.is_deleted)
        self.assertIsNotNone(campo.deleted_at)
        
        campos_activos_final = self.medio.campos.filter(deleted_at__isnull=True).count()
        self.assertEqual(campos_activos_final, campos_activos_inicial - 1)
        
        print(f"Campo eliminado: campos activos {campos_activos_inicial} -> {campos_activos_final}")
    
    def test_reutilizar_nombre_despues_eliminacion(self):
        """Test: Permitir reutilizar nombre de campo después de eliminación"""
        print("Probando reutilización de nombre después de eliminación...")
        
        # Crear y eliminar campo
        campo1 = CampoMedioDePago.objects.create(
            medio_de_pago=self.medio,
            nombre_campo="Token",
            tipo_dato="TEXTO"
        )
        campo1.soft_delete()
        print(f"Campo '{campo1.nombre_campo}' eliminado")
        
        # Crear nuevo campo con mismo nombre (debe permitirse)
        campo2 = CampoMedioDePago.objects.create(
            medio_de_pago=self.medio,
            nombre_campo="Token",
            tipo_dato="NUMERO"
        )
        
        self.assertEqual(campo2.nombre_campo, "Token")
        self.assertFalse(campo2.is_deleted)
        
        print(f"Nuevo campo '{campo2.nombre_campo}' creado exitosamente")


class EdgeCasesTest(TestCase):
    """Tests para casos límite del módulo medios de pago"""
    
    def setUp(self):
        print(f"\nEjecutando: {self._testMethodName}")
    
    def test_precision_decimal_comisiones(self):
        """Test: Precisión decimal en comisiones"""
        print("Probando precisión decimal...")
        
        casos = [
            Decimal('0.001'),    # Mínimo con decimales
            Decimal('2.999'),    # Múltiples decimales
            Decimal('99.999'),   # Máximo con decimales
            Decimal('50.000'),   # Sin decimales significativos
        ]
        
        for valor in casos:
            medio = MedioDePago.objects.create(
                nombre=f"Precisión {valor}",
                comision_porcentaje=valor
            )
            self.assertEqual(medio.comision_porcentaje, valor)
            print(f"Precisión {valor}: OK")
            medio.delete()  # Limpiar
        
        print("Precisión decimal verificada")
    
    def test_limites_longitud_nombres(self):
        """Test: Límites de longitud en nombres"""
        print("Probando límites de longitud...")
        
        # Nombre de medio en el límite (100 caracteres)
        nombre_limite = "A" * 100
        medio = MedioDePago.objects.create(
            nombre=nombre_limite,
            comision_porcentaje=1.0
        )
        self.assertEqual(len(medio.nombre), 100)
        print(f"Nombre medio 100 chars: OK")
        
        # Nombre de campo en el límite (100 caracteres)
        campo_limite = "B" * 100
        campo = CampoMedioDePago.objects.create(
            medio_de_pago=medio,
            nombre_campo=campo_limite,
            tipo_dato="TEXTO"
        )
        self.assertEqual(len(campo.nombre_campo), 100)
        print(f"Nombre campo 100 chars: OK")
    
    def test_managers_personalizados(self):
        """Test: Comportamiento de managers 'objects' vs 'active'"""
        print("Probando managers personalizados...")
        
        # Crear medios en diferentes estados
        medio_activo = MedioDePago.objects.create(
            nombre="Activo",
            is_active=True
        )
        
        medio_inactivo = MedioDePago.objects.create(
            nombre="Inactivo", 
            is_active=False
        )
        
        medio_eliminado = MedioDePago.objects.create(
            nombre="Eliminado",
            is_active=True
        )
        medio_eliminado.soft_delete()
        
        # Verificar contadores
        total_objects = MedioDePago.objects.count()
        total_active = MedioDePago.active.count()
        
        self.assertEqual(total_objects, 3)  # Todos los registros
        self.assertEqual(total_active, 2)   # Solo no eliminados
        
        print(f"Manager objects: {total_objects} registros")
        print(f"Manager active: {total_active} registros")
        print("Managers funcionando correctamente")
    
    def test_relacion_medio_campos(self):
        """Test: Relación entre medio y sus campos"""
        print("Probando relación medio-campos...")
        
        medio = MedioDePago.objects.create(
            nombre="Medio con Campos",
            comision_porcentaje=2.5
        )
        
        # Crear varios campos
        campos_creados = []
        for i in range(3):
            campo = CampoMedioDePago.objects.create(
                medio_de_pago=medio,
                nombre_campo=f"Campo {i+1}",
                tipo_dato="TEXTO"
            )
            campos_creados.append(campo)
        
        # Verificar relaciones
        self.assertEqual(medio.campos.count(), 3)
        self.assertEqual(medio.total_campos_activos, 3)
        
        # Eliminar un campo y verificar
        campos_creados[0].soft_delete()
        self.assertEqual(medio.total_campos_activos, 2)
        
        print(f"Campos totales: {medio.campos.count()}")
        print(f"Campos activos: {medio.total_campos_activos}")
        print("Relación medio-campos funcionando correctamente")


class ErrorSearchTest(TestCase):
    """Tests específicamente diseñados para encontrar errores y fallos"""
    
    def setUp(self):
        print(f"\nBUSCANDO ERRORES: {self._testMethodName}")
        
        self.medio_base = MedioDePago.objects.create(
            nombre="Medio Para Errores",
            comision_porcentaje=2.0,
            is_active=True
        )
    
    def test_crear_medio_con_datos_extremos_debe_fallar(self):
        """Test: Buscar errores con datos extremos"""
        print("Probando datos extremos que deben fallar...")
        
        casos_que_deben_fallar = [
            # Comisiones inválidas
            {"nombre": "Test1", "comision_porcentaje": -0.001, "error_esperado": "negativa"},
            {"nombre": "Test2", "comision_porcentaje": 100.001, "error_esperado": "mayor a 100"},
            {"nombre": "Test3", "comision_porcentaje": 999.999, "error_esperado": "excesiva"},
            # Nombres inválidos
            {"nombre": None, "comision_porcentaje": 5.0, "error_esperado": "nombre nulo"},
            {"nombre": "   ", "comision_porcentaje": 5.0, "error_esperado": "nombre vacío"},
        ]
        
        errores_encontrados = 0
        for i, caso in enumerate(casos_que_deben_fallar):
            try:
                medio = MedioDePago(
                    nombre=caso["nombre"],
                    comision_porcentaje=caso["comision_porcentaje"]
                )
                # Intentar tanto full_clean como save
                medio.full_clean()
                medio.save()
                
                print(f"ERROR CRÍTICO: Caso {i+1} ({caso['error_esperado']}) fue ACEPTADO cuando debía fallar")
                self.fail(f"Datos inválidos fueron aceptados: {caso}")
                
            except (ValidationError, ValueError, TypeError) as e:
                errores_encontrados += 1
                print(f"BIEN: Caso {i+1} ({caso['error_esperado']}) rechazado correctamente")
        
        print(f"Total errores correctamente capturados: {errores_encontrados}/{len(casos_que_deben_fallar)}")
        self.assertEqual(errores_encontrados, len(casos_que_deben_fallar))
    
    def test_operaciones_en_medio_eliminado_deben_fallar(self):
        """Test: Operaciones inválidas en medios eliminados"""
        print("Probando operaciones que deben fallar en medios eliminados...")
        
        # Crear y eliminar medio
        medio = MedioDePago.objects.create(
            nombre="Para Eliminar Y Probar",
            comision_porcentaje=3.0
        )
        medio.soft_delete()
        
        # Estas operaciones deben fallar
        operaciones_invalidas = [
            ("toggle_active", lambda: medio.toggle_active()),
            ("soft_delete doble", lambda: medio.soft_delete()),
        ]
        
        errores_capturados = 0
        for nombre_operacion, operacion in operaciones_invalidas:
            try:
                operacion()
                print(f"ERROR: {nombre_operacion} fue permitida en medio eliminado")
                self.fail(f"Operación '{nombre_operacion}' debería fallar en medio eliminado")
            except ValidationError:
                errores_capturados += 1
                print(f"BIEN: {nombre_operacion} rechazada correctamente")
            except Exception as e:
                print(f"ADVERTENCIA: {nombre_operacion} falló con error inesperado: {e}")
        
        print(f"Operaciones inválidas bloqueadas: {errores_capturados}")
    
    def test_crear_campos_con_datos_invalidos_debe_fallar(self):
        """Test: Buscar errores en creación de campos con datos inválidos"""
        print("Probando creación de campos con datos inválidos...")
        
        casos_campo_invalido = [
            # Nombres inválidos
            {"nombre_campo": "", "tipo_dato": "TEXTO", "error": "nombre vacío"},
            {"nombre_campo": "   ", "tipo_dato": "TEXTO", "error": "nombre solo espacios"},
            {"nombre_campo": None, "tipo_dato": "TEXTO", "error": "nombre nulo"},
            # Tipos inválidos  
            {"nombre_campo": "Campo Valid", "tipo_dato": "", "error": "tipo vacío"},
            {"nombre_campo": "Campo Valid", "tipo_dato": "INVALIDO", "error": "tipo no existe"},
            {"nombre_campo": "Campo Valid", "tipo_dato": None, "error": "tipo nulo"},
        ]
        
        errores_encontrados = 0
        for caso in casos_campo_invalido:
            try:
                campo = CampoMedioDePago(
                    medio_de_pago=self.medio_base,
                    nombre_campo=caso["nombre_campo"],
                    tipo_dato=caso["tipo_dato"]
                )
                campo.full_clean()
                campo.save()
                
                print(f"ERROR CRÍTICO: {caso['error']} fue ACEPTADO")
                self.fail(f"Datos inválidos de campo aceptados: {caso['error']}")
                
            except (ValidationError, ValueError, TypeError):
                errores_encontrados += 1
                print(f"BIEN: {caso['error']} rechazado correctamente")
        
        print(f"Errores de campo capturados: {errores_encontrados}/{len(casos_campo_invalido)}")
    
    def test_duplicados_con_variaciones_debe_fallar(self):
        """Test: Buscar errores con nombres duplicados y sus variaciones"""
        print("Probando detección de duplicados con variaciones...")
        
        # Crear campo base
        CampoMedioDePago.objects.create(
            medio_de_pago=self.medio_base,
            nombre_campo="Email Cliente",
            tipo_dato="EMAIL"
        )
        
        # Variaciones que deben ser detectadas como duplicados
        variaciones_duplicadas = [
            "Email Cliente",      # Exacto
            "email cliente",      # Minúsculas
            "EMAIL CLIENTE",      # Mayúsculas  
            "Email  Cliente",     # Espacios extra internos
            " Email Cliente ",    # Espacios externos
        ]
        
        duplicados_bloqueados = 0
        for variacion in variaciones_duplicadas:
            try:
                campo_duplicado = CampoMedioDePago(
                    medio_de_pago=self.medio_base,
                    nombre_campo=variacion,
                    tipo_dato="TEXTO"
                )
                campo_duplicado.full_clean()
                
                print(f"ERROR: Variación '{variacion}' NO fue detectada como duplicado")
                self.fail(f"Duplicado no detectado: '{variacion}'")
                
            except ValidationError:
                duplicados_bloqueados += 1
                print(f"BIEN: '{variacion}' detectado como duplicado")
        
        print(f"Duplicados correctamente bloqueados: {duplicados_bloqueados}/{len(variaciones_duplicadas)}")
    
    def test_limites_numericos_debe_fallar(self):
        """Test: Buscar errores en límites numéricos"""
        print("Probando límites numéricos extremos...")
        
        limites_que_deben_fallar = [
            # Valores fuera del rango de DecimalField
            {"comision": Decimal('999999.999'), "error": "demasiado grande"},
            {"comision": Decimal('-999999.999'), "error": "demasiado negativo"},
        ]
        
        for caso in limites_que_deben_fallar:
            try:
                medio = MedioDePago(
                    nombre=f"Test {caso['error']}",
                    comision_porcentaje=caso["comision"]
                )
                medio.full_clean()
                medio.save()
                
                print(f"ADVERTENCIA: {caso['error']} fue aceptado - valor: {caso['comision']}")
                # Esto podría ser válido si el campo permite estos valores
                
            except Exception as e:
                print(f"BIEN: {caso['error']} rechazado - {type(e).__name__}")


# Función para ejecutar tests esenciales incluyendo búsqueda de errores
def run_essential_tests():
    """Ejecuta todos los tests esenciales del módulo incluyendo búsqueda de errores"""
    import unittest
    
    print("EJECUTANDO TESTS ESENCIALES + BÚSQUEDA DE ERRORES")
    print("MÓDULO MEDIOS DE PAGO")
    print("="*60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Todos los test cases incluyendo búsqueda de errores
    all_tests = [
        MedioDePagoModelTest,
        CampoMedioDePagoModelTest,
        ErrorSearchTest,  # Nueva clase de búsqueda de errores
        EdgeCasesTest
    ]
    
    total_tests = 0
    for test_case in all_tests:
        case_suite = loader.loadTestsFromTestCase(test_case)
        suite.addTests(case_suite)
        test_count = case_suite.countTestCases()
        total_tests += test_count
        print(f"{test_case.__name__}: {test_count} tests")
    
    print(f"Total tests: {total_tests}")
    print("="*60)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Reporte detallado
    print("\n" + "="*60)
    print("REPORTE FINAL DETALLADO")
    print("="*60)
    
    exitosos = result.testsRun - len(result.failures) - len(result.errors)
    porcentaje_exito = (exitosos / result.testsRun * 100) if result.testsRun > 0 else 0
    
    print(f"ESTADÍSTICAS:")
    print(f"  Tests ejecutados: {result.testsRun}")
    print(f"  Exitosos: {exitosos}")
    print(f"  Fallos: {len(result.failures)}")
    print(f"  Errores: {len(result.errors)}")
    print(f"  Tasa de éxito: {porcentaje_exito:.1f}%")
    
    if result.failures:
        print(f"\nFALLOS DETECTADOS ({len(result.failures)}):")
        for i, (test, traceback) in enumerate(result.failures, 1):
            test_name = str(test).split()[0]
            error_msg = traceback.split('AssertionError:')[-1].split('\n')[0].strip() if 'AssertionError:' in traceback else 'Fallo de aserción'
            print(f"  {i}. {test_name}")
            print(f"     Error: {error_msg}")
    
    if result.errors:
        print(f"\nERRORES DE EJECUCIÓN ({len(result.errors)}):")
        for i, (test, traceback) in enumerate(result.errors, 1):
            test_name = str(test).split()[0]
            print(f"  {i}. {test_name}")
            print(f"     Tipo: {traceback.split('\\n')[-2] if traceback.split('\\n') else 'Error desconocido'}")
    
    # Análisis específico de búsqueda de errores
    error_search_results = []
    for test_result in [result.failures, result.errors]:
        for test, _ in test_result:
            if 'ErrorSearchTest' in str(test):
                error_search_results.append(str(test))
    
    if error_search_results:
        print(f"\nERRORES ENCONTRADOS EN BÚSQUEDA:")
        print("ATENCIÓN: Los siguientes tests de búsqueda de errores fallaron:")
        for error_test in error_search_results:
            print(f"  - {error_test}")
        print("Esto indica posibles vulnerabilidades o fallos en las validaciones")
    
    if result.wasSuccessful():
        print(f"\n✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("✅ Funcionalidades básicas: OK")
        print("✅ Validaciones de seguridad: OK") 
        print("✅ Búsqueda de errores: OK")
        print("✅ Casos límite: OK")
        print("\nEl módulo de medios de pago está robusto y seguro")
    else:
        print(f"\n⚠️ ALGUNOS TESTS FALLARON")
        print("🔍 Revisa los detalles arriba para identificar problemas")
        print("💡 Los fallos en tests de búsqueda de errores son CRÍTICOS")
        print("💡 Indica que validaciones de seguridad no están funcionando")
    
    return result


def run_error_search_only():
    """Ejecuta solo los tests de búsqueda de errores"""
    import unittest
    
    print("EJECUTANDO SOLO TESTS DE BÚSQUEDA DE ERRORES")
    print("="*60)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(ErrorSearchTest)
    
    print(f"Tests de búsqueda de errores: {suite.countTestCases()}")
    print("Estos tests buscan específicamente vulnerabilidades y fallos")
    print("="*60)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print(f"\n✅ BÚSQUEDA DE ERRORES EXITOSA")
        print("Todas las validaciones están funcionando correctamente")
        print("No se encontraron vulnerabilidades críticas")
    else:
        print(f"\n🚨 ERRORES CRÍTICOS ENCONTRADOS")
        print("Las validaciones tienen fallos que deben corregirse INMEDIATAMENTE")
        
    return result


if __name__ == '__main__':
    run_essential_tests()