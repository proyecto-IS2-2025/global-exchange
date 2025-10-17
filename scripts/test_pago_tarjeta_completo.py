"""
Script de verificación completa de pagos con tarjeta local.
Verifica débito de cuenta cliente y crédito a cuenta empresa.

Uso:
    python scripts/test_pago_tarjeta_completo.py
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from decimal import Decimal
from banco.models import TarjetaDebito, TarjetaCredito, Cuenta, EntidadBancaria, PagoTarjeta
from transacciones.views import realizar_pago_tarjeta

def print_separator(char="=", length=70):
    print("\n" + char * length)

def print_section(title):
    print_separator()
    print(f"  {title}")
    print_separator()

def verificar_pago_completo():
    """Verifica que los pagos con tarjeta funcionen correctamente"""
    
    print("\n")
    print_separator("=")
    print("  🔍 VERIFICACIÓN COMPLETA - PAGOS CON TARJETA LOCAL")
    print_separator("=")
    
    # 1. VERIFICAR CONFIGURACIÓN
    print_section("1️⃣  VERIFICANDO CONFIGURACIÓN INICIAL")
    
    # Verificar cuenta empresa
    try:
        entidad_empresa = EntidadBancaria.objects.get(codigo='BPY')
        cuenta_empresa = Cuenta.objects.get(
            entidad=entidad_empresa,
            numero_cuenta='000111222'
        )
        print(f"\n✅ Cuenta empresa encontrada:")
        print(f"   📁 Número: {cuenta_empresa.numero_cuenta}")
        print(f"   💰 Saldo inicial: ₲{cuenta_empresa.saldo:,.0f}")
        print(f"   🏦 Entidad: {cuenta_empresa.entidad.nombre}")
    except Exception as e:
        print(f"\n❌ ERROR: Cuenta empresa no encontrada - {e}")
        return False
    
    # Buscar tarjeta de débito con saldo
    print(f"\n🔍 Buscando tarjeta de débito con saldo...")
    tarjeta_debito = None
    for td in TarjetaDebito.objects.filter(cuenta__isnull=False):
        if td.cuenta.saldo >= Decimal('100000'):
            tarjeta_debito = td
            break
    
    if not tarjeta_debito:
        print("❌ No hay tarjetas de débito con saldo suficiente (mín ₲100,000)")
        return False
    
    print(f"\n✅ Tarjeta de débito seleccionada:")
    print(f"   💳 Número: ****{tarjeta_debito.numero[-4:]}")
    print(f"   👤 Usuario: {tarjeta_debito.usuario.email if tarjeta_debito.usuario else 'N/A'}")
    print(f"   🏦 Entidad: {tarjeta_debito.entidad.nombre}")
    print(f"   📅 Vence: {tarjeta_debito.mes_vencimiento:02d}/{tarjeta_debito.anho_vencimiento}")
    
    # Obtener cuenta asociada
    cuenta_cliente = tarjeta_debito.cuenta
    print(f"\n✅ Cuenta del cliente:")
    print(f"   📁 Número: {cuenta_cliente.numero_cuenta}")
    print(f"   💰 Saldo inicial: ₲{cuenta_cliente.saldo:,.0f}")
    
    # 2. PREPARAR DATOS
    print_section("2️⃣  PREPARANDO DATOS DE PAGO")
    
    medio_datos = {
        'tipo': 'Tarjeta de Débito',
        'datos_campos': {
            'Número de tarjeta': tarjeta_debito.numero,
            'Mes de vencimiento': str(tarjeta_debito.mes_vencimiento),
            'Año de vencimiento': str(tarjeta_debito.anho_vencimiento),
            'Código de seguridad': tarjeta_debito.cvv,
            'Entidad': tarjeta_debito.entidad.nombre
        }
    }
    
    monto_pago = Decimal('50000.00')  # ₲50,000
    
    print(f"\n💳 Datos del pago:")
    print(f"   Monto: ₲{monto_pago:,.0f}")
    print(f"   Tarjeta: ****{tarjeta_debito.numero[-4:]}")
    print(f"   Vencimiento: {medio_datos['datos_campos']['Mes de vencimiento']}/{medio_datos['datos_campos']['Año de vencimiento']}")
    print(f"   Entidad: {medio_datos['datos_campos']['Entidad']}")
    
    # 3. REGISTRAR SALDOS INICIALES
    print_section("3️⃣  SALDOS ANTES DEL PAGO")
    
    saldo_cliente_antes = cuenta_cliente.saldo
    saldo_empresa_antes = cuenta_empresa.saldo
    
    print(f"\n📊 Cuenta Cliente:")
    print(f"   Número: {cuenta_cliente.numero_cuenta}")
    print(f"   Saldo: ₲{saldo_cliente_antes:,.0f}")
    
    print(f"\n📊 Cuenta Empresa:")
    print(f"   Número: {cuenta_empresa.numero_cuenta}")
    print(f"   Saldo: ₲{saldo_empresa_antes:,.0f}")
    
    # 4. EJECUTAR PAGO
    print_section("4️⃣  EJECUTANDO PAGO")
    
    print(f"\n💳 Procesando pago de ₲{monto_pago:,.0f}...")
    
    try:
        resultado = realizar_pago_tarjeta(
            medio_datos=medio_datos,
            monto=monto_pago,
            referencia='TEST-VERIFICACION-001'
        )
        
        print(f"\n📋 Resultado del pago:")
        print(f"   Estado: {'✅ EXITOSO' if resultado.get('ok') else '❌ FALLIDO'}")
        print(f"   Código: {resultado.get('code')}")
        print(f"   Mensaje: {resultado.get('message')}")
        
        if resultado.get('ok'):
            print(f"   🧾 Comprobante: {resultado.get('comprobante')}")
            print(f"   💳 Tipo: {resultado.get('tipo_tarjeta')}")
        else:
            print(f"\n❌ El pago falló. No se puede continuar con la verificación.")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR al procesar pago: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. VERIFICAR SALDOS DESPUÉS
    print_section("5️⃣  SALDOS DESPUÉS DEL PAGO")
    
    # Refrescar datos de la base de datos
    cuenta_cliente.refresh_from_db()
    cuenta_empresa.refresh_from_db()
    
    saldo_cliente_despues = cuenta_cliente.saldo
    saldo_empresa_despues = cuenta_empresa.saldo
    
    print(f"\n📊 Cuenta Cliente:")
    print(f"   Número: {cuenta_cliente.numero_cuenta}")
    print(f"   Saldo antes: ₲{saldo_cliente_antes:,.0f}")
    print(f"   Saldo después: ₲{saldo_cliente_despues:,.0f}")
    print(f"   Diferencia: ₲{saldo_cliente_antes - saldo_cliente_despues:,.0f}")
    
    print(f"\n📊 Cuenta Empresa:")
    print(f"   Número: {cuenta_empresa.numero_cuenta}")
    print(f"   Saldo antes: ₲{saldo_empresa_antes:,.0f}")
    print(f"   Saldo después: ₲{saldo_empresa_despues:,.0f}")
    print(f"   Diferencia: ₲{saldo_empresa_despues - saldo_empresa_antes:,.0f}")
    
    # 6. VERIFICAR REGISTRO DE PAGO
    print_section("6️⃣  VERIFICANDO REGISTRO EN BASE DE DATOS")
    
    try:
        pago = PagoTarjeta.objects.filter(
            comprobante=resultado.get('comprobante')
        ).first()
        
        if pago:
            print(f"\n✅ Registro de pago encontrado:")
            print(f"   ID: {pago.id}")
            print(f"   Comprobante: {pago.comprobante}")
            print(f"   Monto: ₲{pago.monto:,.0f}")
            print(f"   Fecha: {pago.fecha.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Tarjeta débito: {pago.tarjeta_debito.numero[-4:] if pago.tarjeta_debito else 'N/A'}")
            print(f"   Tarjeta crédito: {pago.tarjeta_credito.numero[-4:] if pago.tarjeta_credito else 'N/A'}")
            print(f"   Cuenta destino: {pago.cuenta_destino.numero_cuenta if pago.cuenta_destino else '❌ NO REGISTRADA'}")
            
            if not pago.cuenta_destino:
                print(f"\n   ⚠️  ADVERTENCIA: La cuenta destino no está registrada")
                print(f"   ⚠️  El pago NO aparecerá en el historial del destinatario")
        else:
            print(f"\n❌ No se encontró el registro del pago en la base de datos")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR al buscar registro: {e}")
        return False
    
    # 7. ANÁLISIS DE RESULTADOS
    print_section("7️⃣  ANÁLISIS DE RESULTADOS")
    
    debito_correcto = (saldo_cliente_antes - saldo_cliente_despues) == monto_pago
    credito_correcto = (saldo_empresa_despues - saldo_empresa_antes) == monto_pago
    cuenta_destino_ok = pago.cuenta_destino is not None
    
    print(f"\n🔍 Verificaciones:")
    print(f"   {'✅' if debito_correcto else '❌'} Débito de cuenta cliente: {saldo_cliente_antes - saldo_cliente_despues:,.0f} == {monto_pago:,.0f}")
    print(f"   {'✅' if credito_correcto else '❌'} Crédito a cuenta empresa: {saldo_empresa_despues - saldo_empresa_antes:,.0f} == {monto_pago:,.0f}")
    print(f"   {'✅' if cuenta_destino_ok else '❌'} Cuenta destino registrada: {pago.cuenta_destino.numero_cuenta if pago.cuenta_destino else 'NO'}")
    
    # 8. CONCLUSIÓN
    print_section("8️⃣  CONCLUSIÓN")
    
    todo_ok = debito_correcto and credito_correcto and cuenta_destino_ok
    
    if todo_ok:
        print(f"\n✅ ¡PERFECTO! El pago con tarjeta local funciona correctamente:")
        print(f"   ✅ Se debitó ₲{monto_pago:,.0f} de la cuenta del cliente")
        print(f"   ✅ Se acreditó ₲{monto_pago:,.0f} a la cuenta de la empresa")
        print(f"   ✅ Se registró la cuenta destino")
        print(f"   ✅ El pago aparecerá en ambos historiales")
    else:
        print(f"\n❌ HAY PROBLEMAS:")
        if not debito_correcto:
            print(f"   ❌ El débito no es correcto")
            print(f"      Esperado: -₲{monto_pago:,.0f}")
            print(f"      Real: -₲{saldo_cliente_antes - saldo_cliente_despues:,.0f}")
        if not credito_correcto:
            print(f"   ❌ El crédito no es correcto")
            print(f"      Esperado: +₲{monto_pago:,.0f}")
            print(f"      Real: +₲{saldo_empresa_despues - saldo_empresa_antes:,.0f}")
        if not cuenta_destino_ok:
            print(f"   ❌ No se registró la cuenta destino")
            print(f"      El pago NO aparecerá en el historial de la empresa")
    
    print_separator("=")
    print()
    
    return todo_ok

if __name__ == '__main__':
    try:
        exito = verificar_pago_completo()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verificación cancelada por el usuario\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR FATAL: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
