"""
Script de prueba para verificar la funcionalidad de pago con tarjeta de débito/crédito.

Uso:
    python manage.py shell < scripts/test_pago_tarjeta.py
    
O desde el shell de Django:
    python manage.py shell
    >>> exec(open('scripts/test_pago_tarjeta.py').read())
"""

from decimal import Decimal
from django.db import transaction as db_transaction
from transacciones.views import realizar_pago_tarjeta
from banco.models import TarjetaDebito, TarjetaCredito, PagoTarjeta, Cuenta, EntidadBancaria
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
        
        # Verificar tarjetas de débito
        tarjetas_debito = TarjetaDebito.objects.all()
        if not tarjetas_debito.exists():
            print("⚠️  ADVERTENCIA: No hay tarjetas de débito registradas")
        else:
            print(f"✓ Tarjetas de débito encontradas: {tarjetas_debito.count()}")
            for td in tarjetas_debito[:3]:
                print(f"  - {td}")
        
        # Verificar tarjetas de crédito
        tarjetas_credito = TarjetaCredito.objects.all()
        if not tarjetas_credito.exists():
            print("⚠️  ADVERTENCIA: No hay tarjetas de crédito registradas")
        else:
            print(f"✓ Tarjetas de crédito encontradas: {tarjetas_credito.count()}")
            for tc in tarjetas_credito[:3]:
                print(f"  - {tc} (Disponible: ₲{tc.disponible():,.0f})")
        
        if not tarjetas_debito.exists() and not tarjetas_credito.exists():
            print("\n❌ ERROR: No hay tarjetas registradas para probar")
            print("   Carga fixtures con: python manage.py loaddata banco/fixtures/banco_data.json")
            return False
        
        print("\n✅ Configuración básica correcta")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_pago_tarjeta_debito_exitoso():
    """Probar un pago exitoso con tarjeta de débito"""
    print("🔍 TEST 2: Probando pago exitoso con tarjeta de débito...")
    
    try:
        # Buscar una tarjeta de débito con saldo
        tarjeta = None
        for td in TarjetaDebito.objects.all():
            if td.cuenta and td.cuenta.saldo > Decimal('100000'):
                tarjeta = td
                break
        
        if not tarjeta:
            print("⚠️  No hay tarjetas de débito con saldo suficiente")
            return False
        
        print(f"Tarjeta seleccionada: {tarjeta}")
        print(f"Saldo cuenta: ₲{tarjeta.cuenta.saldo:,.0f}")
        
        # Obtener saldos iniciales
        saldo_cuenta_inicial = tarjeta.cuenta.saldo
        cuenta_empresa = Cuenta.objects.get(numero_cuenta='000111222')
        saldo_empresa_inicial = cuenta_empresa.saldo
        
        print(f"\nSaldo cuenta antes: ₲{saldo_cuenta_inicial:,.0f}")
        print(f"Saldo empresa antes: ₲{saldo_empresa_inicial:,.0f}")
        
        # Preparar datos del medio
        medio_datos = {
            'tipo': 'Tarjeta de Débito',
            'datos_campos': {
                'Número de tarjeta': tarjeta.numero,
                'Mes de vencimiento': str(tarjeta.mes_vencimiento),
                'Año de vencimiento': str(tarjeta.anho_vencimiento),
                'Código de seguridad': tarjeta.cvv,
                'Entidad': tarjeta.entidad.nombre
            }
        }
        
        # Monto a pagar
        monto = Decimal('50000.00')  # ₲50,000
        
        print(f"\n💳 Procesando pago de ₲{monto:,.0f}...")
        
        # Ejecutar pago
        resultado = realizar_pago_tarjeta(
            medio_datos=medio_datos,
            monto=monto,
            referencia='TEST-DEBITO-001'
        )
        
        # Verificar resultado
        print(f"\nResultado del pago:")
        print(f"  OK: {resultado.get('ok')}")
        print(f"  Código: {resultado.get('code')}")
        print(f"  Mensaje: {resultado.get('message')}")
        
        if resultado.get('ok'):
            print(f"  Comprobante: {resultado.get('comprobante')}")
            print(f"  Tipo: {resultado.get('tipo_tarjeta')}")
            
            # Refrescar datos
            tarjeta.cuenta.refresh_from_db()
            cuenta_empresa.refresh_from_db()
            
            print(f"\nSaldo cuenta después: ₲{tarjeta.cuenta.saldo:,.0f}")
            print(f"Saldo empresa después: ₲{cuenta_empresa.saldo:,.0f}")
            
            # Verificar cambios
            diferencia_cuenta = saldo_cuenta_inicial - tarjeta.cuenta.saldo
            diferencia_empresa = cuenta_empresa.saldo - saldo_empresa_inicial
            
            print(f"\nCambios:")
            print(f"  Cuenta cliente: -₲{diferencia_cuenta:,.0f}")
            print(f"  Cuenta empresa: +₲{diferencia_empresa:,.0f}")
            
            if diferencia_cuenta == monto and diferencia_empresa == monto:
                print("\n✅ Pago con tarjeta de débito procesado correctamente")
                
                # Verificar registro en PagoTarjeta
                pago = PagoTarjeta.objects.filter(
                    comprobante=resultado.get('comprobante')
                ).first()
                if pago:
                    print(f"✓ Registro de pago encontrado (ID: {pago.id})")
                    print(f"  Monto: ₲{pago.monto:,.0f}")
                    print(f"  Tarjeta: {pago.tarjeta_debito}")
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

def test_pago_tarjeta_credito_exitoso():
    """Probar un pago exitoso con tarjeta de crédito"""
    print("🔍 TEST 3: Probando pago exitoso con tarjeta de crédito...")
    
    try:
        # Buscar una tarjeta de crédito con crédito disponible
        tarjeta = None
        for tc in TarjetaCredito.objects.all():
            if tc.disponible() > Decimal('100000'):
                tarjeta = tc
                break
        
        if not tarjeta:
            print("⚠️  No hay tarjetas de crédito con crédito suficiente")
            return False
        
        print(f"Tarjeta seleccionada: {tarjeta}")
        print(f"Crédito disponible: ₲{tarjeta.disponible():,.0f}")
        
        # Obtener valores iniciales
        saldo_usado_inicial = tarjeta.saldo_usado
        cuenta_empresa = Cuenta.objects.get(numero_cuenta='000111222')
        saldo_empresa_inicial = cuenta_empresa.saldo
        
        print(f"\nCrédito usado antes: ₲{saldo_usado_inicial:,.0f}")
        print(f"Saldo empresa antes: ₲{saldo_empresa_inicial:,.0f}")
        
        # Preparar datos del medio
        medio_datos = {
            'tipo': 'Tarjeta de Crédito',
            'datos_campos': {
                'card_number': tarjeta.numero,
                'exp_month': str(tarjeta.mes_vencimiento),
                'exp_year': str(tarjeta.anho_vencimiento),
                'cvc': tarjeta.cvv,
                'Entidad': tarjeta.entidad.nombre
            }
        }
        
        # Monto a pagar
        monto = Decimal('75000.00')  # ₲75,000
        
        print(f"\n💳 Procesando pago de ₲{monto:,.0f}...")
        
        # Ejecutar pago
        resultado = realizar_pago_tarjeta(
            medio_datos=medio_datos,
            monto=monto,
            referencia='TEST-CREDITO-001'
        )
        
        # Verificar resultado
        print(f"\nResultado del pago:")
        print(f"  OK: {resultado.get('ok')}")
        print(f"  Código: {resultado.get('code')}")
        print(f"  Mensaje: {resultado.get('message')}")
        
        if resultado.get('ok'):
            print(f"  Comprobante: {resultado.get('comprobante')}")
            print(f"  Tipo: {resultado.get('tipo_tarjeta')}")
            
            # Refrescar datos
            tarjeta.refresh_from_db()
            cuenta_empresa.refresh_from_db()
            
            print(f"\nCrédito usado después: ₲{tarjeta.saldo_usado:,.0f}")
            print(f"Crédito disponible: ₲{tarjeta.disponible():,.0f}")
            print(f"Saldo empresa después: ₲{cuenta_empresa.saldo:,.0f}")
            
            # Verificar cambios
            diferencia_credito = tarjeta.saldo_usado - saldo_usado_inicial
            diferencia_empresa = cuenta_empresa.saldo - saldo_empresa_inicial
            
            print(f"\nCambios:")
            print(f"  Crédito consumido: +₲{diferencia_credito:,.0f}")
            print(f"  Cuenta empresa: +₲{diferencia_empresa:,.0f}")
            
            if diferencia_credito == monto and diferencia_empresa == monto:
                print("\n✅ Pago con tarjeta de crédito procesado correctamente")
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

def test_tarjeta_no_encontrada():
    """Probar pago con tarjeta que no existe"""
    print("🔍 TEST 4: Probando pago con tarjeta inexistente...")
    
    try:
        medio_datos = {
            'tipo': 'Tarjeta de Débito',
            'datos_campos': {
                'card_number': '9999999999999999',  # No existe
                'exp_month': '12',
                'exp_year': '2030',
                'cvc': '999'
            }
        }
        
        resultado = realizar_pago_tarjeta(
            medio_datos=medio_datos,
            monto=Decimal('50000.00'),
            referencia='TEST-NO-EXISTE'
        )
        
        print(f"\nResultado:")
        print(f"  OK: {resultado.get('ok')}")
        print(f"  Código: {resultado.get('code')}")
        print(f"  Mensaje: {resultado.get('message')}")
        
        if not resultado.get('ok') and resultado.get('code') == '14':
            print("\n✅ Error de tarjeta no encontrada detectado correctamente")
            return True
        else:
            print("\n❌ ERROR: Debería haber detectado tarjeta inexistente")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_datos_incompletos():
    """Probar pago con datos incompletos"""
    print("🔍 TEST 5: Probando pago con datos incompletos...")
    
    try:
        # Datos sin CVV
        medio_datos = {
            'tipo': 'Tarjeta de Débito',
            'datos_campos': {
                'card_number': '4111111111111111',
                'exp_month': '12',
                'exp_year': '2027'
                # Falta CVV
            }
        }
        
        resultado = realizar_pago_tarjeta(
            medio_datos=medio_datos,
            monto=Decimal('50000.00'),
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
    print("\n" + "🚀 INICIANDO TESTS DE PAGO CON TARJETA " + "\n")
    
    resultados = []
    
    # Test 1: Configuración básica
    print_separator()
    resultados.append(('Configuración básica', test_configuracion_basica()))
    
    # Test 2: Pago con débito exitoso
    print_separator()
    resultados.append(('Pago con débito', test_pago_tarjeta_debito_exitoso()))
    
    # Test 3: Pago con crédito exitoso
    print_separator()
    resultados.append(('Pago con crédito', test_pago_tarjeta_credito_exitoso()))
    
    # Test 4: Tarjeta no encontrada
    print_separator()
    resultados.append(('Tarjeta inexistente', test_tarjeta_no_encontrada()))
    
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
