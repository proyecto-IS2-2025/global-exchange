"""
Test específico con tarjeta ID 3 (cuenta 000555666)
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from decimal import Decimal
from banco.models import TarjetaDebito, Cuenta
from transacciones.views import realizar_pago_tarjeta

# Obtener tarjeta y cuentas
tarjeta = TarjetaDebito.objects.get(id=3)  # ****1111, cuenta 000555666
cuenta_cliente = tarjeta.cuenta
cuenta_empresa = Cuenta.objects.get(numero_cuenta='000111222')

print(f"\n{'='*70}")
print(f"  TEST DE PAGO CON TARJETA LOCAL")
print(f"{'='*70}\n")

print(f"💳 Tarjeta seleccionada:")
print(f"   ID: {tarjeta.id}")
print(f"   Número: ****{tarjeta.numero[-4:]}")
print(f"   Cuenta: {cuenta_cliente.numero_cuenta}")
print(f"   Usuario: {tarjeta.usuario.email}\n")

print(f"📊 ANTES DEL PAGO:")
print(f"   Cliente (cuenta {cuenta_cliente.numero_cuenta}): ₲{cuenta_cliente.saldo:,.0f}")
print(f"   Empresa (cuenta {cuenta_empresa.numero_cuenta}): ₲{cuenta_empresa.saldo:,.0f}\n")

# Guardar saldos iniciales
saldo_cliente_antes = cuenta_cliente.saldo
saldo_empresa_antes = cuenta_empresa.saldo

# Preparar datos
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

monto = Decimal('100000.00')  # ₲100,000

print(f"💰 Procesando pago de ₲{monto:,.0f}...\n")

# Ejecutar pago
resultado = realizar_pago_tarjeta(
    medio_datos=medio_datos,
    monto=monto,
    referencia='TEST-VERIFICACION-FINAL'
)

print(f"📋 RESULTADO:")
print(f"   Estado: {'✅ EXITOSO' if resultado.get('ok') else '❌ FALLIDO'}")
print(f"   Mensaje: {resultado.get('message')}")
if resultado.get('ok'):
    print(f"   Comprobante: {resultado.get('comprobante')}\n")
else:
    print(f"   Código error: {resultado.get('code')}\n")
    exit(1)

# Refrescar saldos
cuenta_cliente.refresh_from_db()
cuenta_empresa.refresh_from_db()

print(f"📊 DESPUÉS DEL PAGO:")
print(f"   Cliente (cuenta {cuenta_cliente.numero_cuenta}): ₲{cuenta_cliente.saldo:,.0f}")
print(f"   Empresa (cuenta {cuenta_empresa.numero_cuenta}): ₲{cuenta_empresa.saldo:,.0f}\n")

# Calcular diferencias
debito_cliente = saldo_cliente_antes - cuenta_cliente.saldo
credito_empresa = cuenta_empresa.saldo - saldo_empresa_antes

print(f"📊 MOVIMIENTOS:")
print(f"   Débito cliente: ₲{debito_cliente:,.0f}")
print(f"   Crédito empresa: ₲{credito_empresa:,.0f}\n")

# Verificar
print(f"{'='*70}")
print(f"  VERIFICACIÓN")
print(f"{'='*70}\n")

debito_ok = debito_cliente == monto
credito_ok = credito_empresa == monto

print(f"{'✅' if debito_ok else '❌'} Débito correcto: ₲{debito_cliente:,.0f} == ₲{monto:,.0f}")
print(f"{'✅' if credito_ok else '❌'} Crédito correcto: ₲{credito_empresa:,.0f} == ₲{monto:,.0f}\n")

if debito_ok and credito_ok:
    print(f"✅ ¡PERFECTO! El pago funcionó correctamente:")
    print(f"   ✅ Se debitó ₲{monto:,.0f} de cuenta cliente")
    print(f"   ✅ Se acreditó ₲{monto:,.0f} a cuenta empresa")
    print(f"\n{'='*70}\n")
else:
    print(f"❌ HAY PROBLEMAS EN EL PAGO\n")
    print(f"{'='*70}\n")
    exit(1)
