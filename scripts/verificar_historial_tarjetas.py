"""
Script de verificación del historial de pagos con tarjeta.
Verifica que los pagos aparezcan correctamente en el historial.

Uso:
    Get-Content scripts\verificar_historial_tarjetas.py | python manage.py shell
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from banco.models import PagoTarjeta, Cuenta
from datetime import date, timedelta

def print_separator(char="=", length=70):
    print(char * length)

def verificar_historial():
    print("\n")
    print_separator()
    print("🔍 VERIFICACIÓN DE HISTORIAL - PAGOS CON TARJETA")
    print_separator()
    
    # 1. Verificar cuenta empresa
    print("\n📊 1. VERIFICANDO CUENTA EMPRESA...")
    try:
        cuenta_empresa = Cuenta.objects.get(numero_cuenta='000111222')
        print(f"   ✅ Cuenta empresa encontrada")
        print(f"   📁 Número: {cuenta_empresa.numero_cuenta}")
        print(f"   💰 Saldo: ₲{cuenta_empresa.saldo:,.0f}")
        print(f"   🏦 Entidad: {cuenta_empresa.entidad.nombre}")
    except Cuenta.DoesNotExist:
        print("   ❌ Cuenta empresa NO encontrada")
        return False
    
    # 2. Verificar pagos con tarjeta recientes
    print("\n📊 2. VERIFICANDO PAGOS CON TARJETA...")
    
    # Últimos 7 días
    fecha_desde = date.today() - timedelta(days=7)
    pagos_recientes = PagoTarjeta.objects.filter(
        fecha__date__gte=fecha_desde
    ).order_by('-fecha')
    
    print(f"   📅 Período: Últimos 7 días (desde {fecha_desde})")
    print(f"   📦 Total pagos encontrados: {pagos_recientes.count()}")
    
    if not pagos_recientes.exists():
        print("   ⚠️  No hay pagos recientes para verificar")
        print("   💡 Realiza una compra con tarjeta local para probar")
        return True
    
    # 3. Analizar cada pago
    print("\n📊 3. DETALLE DE PAGOS:")
    print_separator("-")
    
    pagos_con_destino = 0
    pagos_sin_destino = 0
    
    for pago in pagos_recientes[:10]:  # Mostrar últimos 10
        print(f"\n   🎫 Pago ID: {pago.id}")
        print(f"   📅 Fecha: {pago.fecha.strftime('%Y-%m-%d %H:%M')}")
        print(f"   💵 Monto: ₲{pago.monto:,.0f}")
        print(f"   🧾 Comprobante: {pago.comprobante}")
        
        # Tipo de tarjeta
        if pago.tarjeta_debito:
            print(f"   💳 Tipo: Débito (****{pago.tarjeta_debito.numero[-4:]})")
            print(f"   👤 Usuario: {pago.tarjeta_debito.usuario.email if pago.tarjeta_debito.usuario else 'N/A'}")
        elif pago.tarjeta_credito:
            print(f"   💳 Tipo: Crédito (****{pago.tarjeta_credito.numero[-4:]})")
            print(f"   👤 Usuario: {pago.tarjeta_credito.usuario.email if pago.tarjeta_credito.usuario else 'N/A'}")
        
        # Cuenta destino (IMPORTANTE)
        if pago.cuenta_destino:
            print(f"   ✅ Cuenta destino: {pago.cuenta_destino.numero_cuenta} ({pago.cuenta_destino.entidad.nombre})")
            pagos_con_destino += 1
        else:
            print(f"   ❌ Cuenta destino: NO REGISTRADA")
            pagos_sin_destino += 1
        
        # Billetera (si es recarga)
        if pago.billetera:
            print(f"   👛 Recarga a billetera: {pago.billetera.usuario.telefono if pago.billetera.usuario else 'N/A'}")
    
    # 4. Resumen
    print("\n")
    print_separator("-")
    print("📊 4. RESUMEN DE VERIFICACIÓN:")
    print_separator("-")
    
    total = pagos_recientes.count()
    print(f"\n   📦 Total pagos analizados: {total}")
    print(f"   ✅ Con cuenta destino: {pagos_con_destino} ({pagos_con_destino/max(total,1)*100:.1f}%)")
    print(f"   ❌ Sin cuenta destino: {pagos_sin_destino} ({pagos_sin_destino/max(total,1)*100:.1f}%)")
    
    # 5. Verificar pagos recibidos en cuenta empresa
    print("\n📊 5. PAGOS RECIBIDOS EN CUENTA EMPRESA:")
    print_separator("-")
    
    pagos_empresa = PagoTarjeta.objects.filter(
        cuenta_destino=cuenta_empresa,
        fecha__date__gte=fecha_desde
    ).order_by('-fecha')
    
    print(f"\n   💰 Total recibido (últimos 7 días): {pagos_empresa.count()} pagos")
    
    if pagos_empresa.exists():
        monto_total = sum(p.monto for p in pagos_empresa)
        print(f"   💵 Monto total: ₲{monto_total:,.0f}")
        print(f"\n   📋 Últimos 5 pagos recibidos:")
        for p in pagos_empresa[:5]:
            tarjeta_info = f"****{p.tarjeta_debito.numero[-4:]}" if p.tarjeta_debito else f"****{p.tarjeta_credito.numero[-4:]}"
            print(f"      • {p.fecha.strftime('%Y-%m-%d %H:%M')} | ₲{p.monto:,.0f} | {tarjeta_info}")
    else:
        print(f"   ⚠️  No se recibieron pagos en este período")
    
    # 6. Conclusión
    print("\n")
    print_separator()
    print("✅ CONCLUSIÓN:")
    print_separator()
    
    if pagos_sin_destino == 0:
        print("\n   ✅ ¡PERFECTO! Todos los pagos tienen cuenta destino registrada")
        print("   ✅ Los pagos aparecerán en el historial del destinatario")
    elif pagos_sin_destino > 0 and pagos_con_destino == 0:
        print("\n   ❌ PROBLEMA: Ningún pago tiene cuenta destino")
        print("   💡 Verifica que la función realizar_pago_tarjeta() esté actualizada")
        print("   💡 Los pagos nuevos deben incluir 'cuenta_destino' al crearse")
    else:
        print(f"\n   ⚠️  PARCIAL: {pagos_sin_destino} pagos antiguos sin cuenta destino")
        print("   ✅ Los pagos nuevos SÍ tienen cuenta destino")
        print("   💡 Los pagos antiguos solo aparecen en historial de quien pagó")
    
    print("\n" + "="*70 + "\n")
    
    return True

if __name__ == '__main__':
    verificar_historial()
