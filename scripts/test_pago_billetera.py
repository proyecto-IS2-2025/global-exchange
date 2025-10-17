"""
Script de prueba para verificar la funcionalidad de pago con billetera digital.

Uso:
    python manage.py shell < scripts/test_pago_billetera.py
    
O desde el shell de Django:
    python manage.py shell
    >>> exec(open('scripts/test_pago_billetera.py').read())
"""

from decimal import Decimal
from django.db import transaction as db_transaction
from transacciones.views import realizar_pago_billetera
from billetera.models import UsuarioBilletera, Billetera, PagoBilletera
from banco.models import Cuenta, EntidadBancaria
from clientes.models import Cliente, ClienteMedioDePago
from medios_pago.models import MedioDePago

def print_separator():
    print("\n" + "="*60 + "\n")

def test_configuracion_basica():
    """Verificar que la configuración básica existe"""
    print("🔍 TEST 1: Verificando configuración básica...")
    
    try:
        # Verificar entidad bancaria
        entidad = EntidadBancaria.objects.filter(codigo='BPY').first()
        if not entidad:
            print("❌ ERROR: No existe EntidadBancaria con código 'BPY'")
            return False
        print(f"✓ Entidad encontrada: {entidad.nombre}")
        
        # Verificar cuenta empresa
        cuenta_empresa = Cuenta.objects.filter(
            entidad=entidad,
            numero_cuenta='000111222'
        ).first()
        if not cuenta_empresa:
            print("❌ ERROR: No existe cuenta empresa '000111222'")
            return False
        print(f"✓ Cuenta empresa encontrada: {cuenta_empresa.numero_cuenta}")
        print(f"  Saldo actual: ₲{cuenta_empresa.saldo:,.0f}")
        
        # Verificar usuario de billetera
        usuario_billetera = UsuarioBilletera.objects.filter(
            numero_celular='0981111111'
        ).first()
        if not usuario_billetera:
            print("❌ ERROR: No existe UsuarioBilletera con teléfono '0981111111'")
            return False
        print(f"✓ Usuario billetera encontrado: {usuario_billetera.nombre} {usuario_billetera.apellido}")
        
        # Verificar billetera
        billetera = Billetera.objects.filter(
            usuario=usuario_billetera,
            activa=True
        ).first()
        if not billetera:
            print("❌ ERROR: No existe Billetera activa para el usuario")
            return False
        print(f"✓ Billetera encontrada (ID: {billetera.id})")
        print(f"  Saldo actual: ₲{billetera.saldo:,.0f}")
        print(f"  Entidad: {billetera.entidad.nombre}")
        
        # Verificar medio de pago
        medio = MedioDePago.objects.filter(
            tipo_medio='billetera_electronica',
            is_active=True
        ).first()
        if not medio:
            print("⚠️  ADVERTENCIA: No existe MedioDePago tipo 'billetera_electronica'")
            print("   Esto no es crítico para el test de la función")
        else:
            print(f"✓ Medio de pago encontrado: {medio.nombre}")
        
        print("\n✅ Configuración básica correcta")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_pago_exitoso():
    """Probar un pago exitoso desde billetera"""
    print("🔍 TEST 2: Probando pago exitoso desde billetera...")
    
    try:
        # Obtener saldos iniciales
        billetera = Billetera.objects.get(
            usuario__numero_celular='0981111111',
            activa=True
        )
        cuenta_empresa = Cuenta.objects.get(
            entidad__codigo='BPY',
            numero_cuenta='000111222'
        )
        
        saldo_billetera_inicial = billetera.saldo
        saldo_empresa_inicial = cuenta_empresa.saldo
        
        print(f"Saldo billetera antes: ₲{saldo_billetera_inicial:,.0f}")
        print(f"Saldo empresa antes: ₲{saldo_empresa_inicial:,.0f}")
        
        # Preparar datos del medio
        medio_datos = {
            'tipo': 'Billetera Electrónica',
            'datos_campos': {
                'Teléfono de billetera': '0981111111',
                'Entidad': 'Banco Py'
            }
        }
        
        # Monto a transferir
        monto = Decimal('100000.00')  # ₲100,000
        
        print(f"\n💰 Procesando pago de ₲{monto:,.0f}...")
        
        # Ejecutar pago
        resultado = realizar_pago_billetera(
            medio_datos=medio_datos,
            monto=monto,
            referencia='TEST-PAGO-001'
        )
        
        # Verificar resultado
        print(f"\nResultado del pago:")
        print(f"  OK: {resultado.get('ok')}")
        print(f"  Código: {resultado.get('code')}")
        print(f"  Mensaje: {resultado.get('message')}")
        
        if resultado.get('ok'):
            print(f"  Comprobante: {resultado.get('comprobante')}")
            
            # Refrescar datos
            billetera.refresh_from_db()
            cuenta_empresa.refresh_from_db()
            
            print(f"\nSaldo billetera después: ₲{billetera.saldo:,.0f}")
            print(f"Saldo empresa después: ₲{cuenta_empresa.saldo:,.0f}")
            
            # Verificar cambios
            diferencia_billetera = saldo_billetera_inicial - billetera.saldo
            diferencia_empresa = cuenta_empresa.saldo - saldo_empresa_inicial
            
            print(f"\nCambios:")
            print(f"  Billetera: -₲{diferencia_billetera:,.0f}")
            print(f"  Empresa: +₲{diferencia_empresa:,.0f}")
            
            if diferencia_billetera == monto and diferencia_empresa == monto:
                print("\n✅ Pago procesado correctamente")
                
                # Verificar registro en PagoBilletera
                pago = PagoBilletera.objects.filter(
                    comprobante=resultado.get('comprobante')
                ).first()
                if pago:
                    print(f"✓ Registro de pago encontrado (ID: {pago.id})")
                    print(f"  Exitoso: {pago.exitoso}")
                    print(f"  Fecha: {pago.fecha}")
                else:
                    print("⚠️  Registro de pago no encontrado")
                
                return True
            else:
                print("❌ ERROR: Los montos no coinciden")
                return False
        else:
            print(f"\n❌ ERROR en el pago: {resultado.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_saldo_insuficiente():
    """Probar pago con saldo insuficiente"""
    print("🔍 TEST 3: Probando pago con saldo insuficiente...")
    
    try:
        # Obtener saldo actual
        billetera = Billetera.objects.get(
            usuario__numero_celular='0981111111',
            activa=True
        )
        
        # Intentar pagar más de lo que tiene
        monto_excesivo = billetera.saldo + Decimal('1000000.00')
        
        print(f"Saldo disponible: ₲{billetera.saldo:,.0f}")
        print(f"Intentando pagar: ₲{monto_excesivo:,.0f}")
        
        medio_datos = {
            'tipo': 'Billetera Electrónica',
            'datos_campos': {
                'Teléfono de billetera': '0981111111',
                'Entidad': 'Banco Py'
            }
        }
        
        resultado = realizar_pago_billetera(
            medio_datos=medio_datos,
            monto=monto_excesivo,
            referencia='TEST-SALDO-INSUFICIENTE'
        )
        
        print(f"\nResultado:")
        print(f"  OK: {resultado.get('ok')}")
        print(f"  Código: {resultado.get('code')}")
        print(f"  Mensaje: {resultado.get('message')}")
        
        if not resultado.get('ok') and resultado.get('code') == '51':
            print("\n✅ Error de saldo insuficiente detectado correctamente")
            return True
        else:
            print("\n❌ ERROR: Debería haber detectado saldo insuficiente")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_billetera_inexistente():
    """Probar pago con billetera que no existe"""
    print("🔍 TEST 4: Probando pago con billetera inexistente...")
    
    try:
        medio_datos = {
            'tipo': 'Billetera Electrónica',
            'datos_campos': {
                'Teléfono de billetera': '0999999999',  # No existe
                'Entidad': 'Banco Py'
            }
        }
        
        resultado = realizar_pago_billetera(
            medio_datos=medio_datos,
            monto=Decimal('100000.00'),
            referencia='TEST-NO-EXISTE'
        )
        
        print(f"\nResultado:")
        print(f"  OK: {resultado.get('ok')}")
        print(f"  Código: {resultado.get('code')}")
        print(f"  Mensaje: {resultado.get('message')}")
        
        if not resultado.get('ok') and resultado.get('code') == '14':
            print("\n✅ Error de billetera no encontrada detectado correctamente")
            return True
        else:
            print("\n❌ ERROR: Debería haber detectado billetera inexistente")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_datos_incompletos():
    """Probar pago con datos incompletos"""
    print("🔍 TEST 5: Probando pago con datos incompletos...")
    
    try:
        # Datos sin número de teléfono
        medio_datos = {
            'tipo': 'Billetera Electrónica',
            'datos_campos': {
                'Entidad': 'Banco Py'
                # Falta teléfono
            }
        }
        
        resultado = realizar_pago_billetera(
            medio_datos=medio_datos,
            monto=Decimal('100000.00'),
            referencia='TEST-DATOS-INCOMPLETOS'
        )
        
        print(f"\nResultado:")
        print(f"  OK: {resultado.get('ok')}")
        print(f"  Código: {resultado.get('code')}")
        print(f"  Mensaje: {resultado.get('message')}")
        
        if not resultado.get('ok') and resultado.get('code') == '12':
            print("\n✅ Error de datos incompletos detectado correctamente")
            return True
        else:
            print("\n❌ ERROR: Debería haber detectado datos incompletos")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n" + "🚀 INICIANDO TESTS DE PAGO CON BILLETERA DIGITAL " + "\n")
    
    resultados = []
    
    # Test 1: Configuración básica
    print_separator()
    resultados.append(('Configuración básica', test_configuracion_basica()))
    
    # Test 2: Pago exitoso
    print_separator()
    resultados.append(('Pago exitoso', test_pago_exitoso()))
    
    # Test 3: Saldo insuficiente
    print_separator()
    resultados.append(('Saldo insuficiente', test_saldo_insuficiente()))
    
    # Test 4: Billetera inexistente
    print_separator()
    resultados.append(('Billetera inexistente', test_billetera_inexistente()))
    
    # Test 5: Datos incompletos
    print_separator()
    resultados.append(('Datos incompletos', test_datos_incompletos()))
    
    # Resumen
    print_separator()
    print("📊 RESUMEN DE TESTS")
    print_separator()
    
    total = len(resultados)
    exitosos = sum(1 for _, resultado in resultados if resultado)
    
    for nombre, resultado in resultados:
        icono = "✅" if resultado else "❌"
        print(f"{icono} {nombre}")
    
    print(f"\nTotal: {exitosos}/{total} tests exitosos")
    
    if exitosos == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
    else:
        print(f"\n⚠️  {total - exitosos} test(s) fallaron")
    
    return exitosos == total

# Ejecutar tests
if __name__ == '__main__':
    run_all_tests()
