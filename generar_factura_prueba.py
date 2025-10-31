#!/usr/bin/env python3
"""
Script para generar una factura de prueba completa para un usuario
Crea: Usuario → Transacción → Factura Electrónica
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from django.contrib.auth import get_user_model
from transacciones.models import Transaccion
from divisas.models import Divisa
from facturacion_electronica.utils import generar_factura_desde_transaccion
from facturacion_electronica.models import FacturaElectronica

User = get_user_model()

print("=" * 70)
print("GENERAR FACTURA DE PRUEBA PARA USUARIO")
print("=" * 70)
print()

# ═══════════════════════════════════════════════════════════════════
# 1. BUSCAR O CREAR USUARIO DE PRUEBA
# ═══════════════════════════════════════════════════════════════════

print("1️⃣  Buscando usuario de prueba...")

# Primero intentar obtener un usuario existente
usuarios_list = list(User.objects.filter(is_staff=False, is_superuser=False)[:5])

if usuarios_list:
    print(f"\n   Usuarios disponibles:")
    for idx, u in enumerate(usuarios_list, 1):
        print(f"   {idx}. {u.username} - {u.get_full_name() or 'Sin nombre'} ({u.email})")
    
    usuario = usuarios_list[0]
    print(f"\n   ✅ Usando usuario: {usuario.username}")
else:
    # Crear usuario de prueba
    print("   No hay usuarios cliente, creando uno de prueba...")
    usuario = User.objects.create_user(
        username='cliente_prueba',
        email='cliente@test.com',
        password='test1234',
        first_name='Cliente',
        last_name='De Prueba'
    )
    print(f"   ✅ Usuario creado: {usuario.username}")

print()

# ═══════════════════════════════════════════════════════════════════
# 2. VERIFICAR DIVISAS
# ═══════════════════════════════════════════════════════════════════

print("2️⃣  Verificando divisas...")

try:
    divisa_compra = Divisa.objects.get(code='USD')
    print(f"   ✅ Divisa encontrada: {divisa_compra.nombre} ({divisa_compra.code})")
except Divisa.DoesNotExist:
    print("   ⚠️  No existe divisa USD, creando...")
    divisa_compra = Divisa.objects.create(
        code='USD',
        nombre='Dólar Estadounidense',
        simbolo='$',
        es_moneda_base=False,
        is_active=True
    )
    print(f"   ✅ Divisa creada: {divisa_compra.nombre}")

print()

# ═══════════════════════════════════════════════════════════════════
# 3. CREAR TRANSACCIÓN COMPLETADA
# ═══════════════════════════════════════════════════════════════════

print("3️⃣  Creando transacción completada...")

# Verificar si ya existe una transacción para este usuario
transaccion_existente = Transaccion.objects.filter(
    usuario=usuario,
    estado='completada'
).first()

if transaccion_existente and hasattr(transaccion_existente, 'factura'):
    print(f"   ℹ️  Ya existe transacción con factura: {transaccion_existente.numero_transaccion}")
    print(f"   Factura: {transaccion_existente.factura.numero_factura}")
    transaccion = transaccion_existente
else:
    # Crear nueva transacción
    transaccion = Transaccion.objects.create(
        usuario=usuario,
        tipo_operacion='compra',
        divisa_compra=divisa_compra,
        monto_compra=Decimal('500.00'),
        monto_venta=Decimal('3750000.00'),  # Asumiendo tasa de 7500 PYG/USD
        tasa_aplicada=Decimal('7500.00'),
        estado='completada',
        fecha_creacion=datetime.now() - timedelta(hours=2),
        fecha_completado=datetime.now() - timedelta(hours=1),
        numero_transaccion=f'TXN-{datetime.now().strftime("%Y%m%d%H%M%S")}'
    )
    print(f"   ✅ Transacción creada: {transaccion.numero_transaccion}")
    print(f"      - Tipo: {transaccion.get_tipo_operacion_display()}")
    print(f"      - Monto: ${transaccion.monto_compra} USD")
    print(f"      - Total: ₲{transaccion.monto_venta:,.0f} PYG")
    print(f"      - Estado: {transaccion.estado}")

print()

# ═══════════════════════════════════════════════════════════════════
# 4. GENERAR FACTURA ELECTRÓNICA
# ═══════════════════════════════════════════════════════════════════

print("4️⃣  Generando factura electrónica...")

try:
    # Verificar si ya tiene factura
    if hasattr(transaccion, 'factura'):
        factura = transaccion.factura
        print(f"   ℹ️  Transacción ya tiene factura: {factura.numero_factura}")
    else:
        # Generar nueva factura
        factura = generar_factura_desde_transaccion(transaccion)
        print(f"   ✅ Factura generada exitosamente!")
        print(f"      - Número: {factura.numero_factura}")
        print(f"      - Estado: {factura.estado}")
        print(f"      - CDC: {factura.cdc or 'Pendiente de procesamiento'}")
        print(f"      - Fecha: {factura.fecha_emision}")
    
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # 5. RESUMEN FINAL
    # ═══════════════════════════════════════════════════════════════════
    
    print("=" * 70)
    print("✅ FACTURA DE PRUEBA GENERADA EXITOSAMENTE")
    print("=" * 70)
    print()
    print("📋 DATOS DE ACCESO:")
    print("-" * 70)
    print(f"Usuario:     {usuario.username}")
    print(f"Contraseña:  test1234")
    print(f"Email:       {usuario.email}")
    print()
    print("🧾 DATOS DE LA FACTURA:")
    print("-" * 70)
    print(f"Número Factura:  {factura.numero_factura}")
    print(f"Transacción:     {transaccion.numero_transaccion}")
    print(f"Estado:          {factura.estado}")
    print(f"Monto:           ${transaccion.monto_compra} USD = ₲{transaccion.monto_venta:,.0f} PYG")
    print()
    print("🌐 URLs PARA ACCEDER:")
    print("-" * 70)
    print(f"Login:           http://localhost:8000/login/")
    print(f"Mis Facturas:    http://localhost:8000/facturacion/mis-facturas/")
    print(f"Ver Factura:     http://localhost:8000/facturacion/{factura.id}/")
    print()
    print("=" * 70)
    print()
    print("💡 PRÓXIMOS PASOS:")
    print("   1. Inicia sesión con las credenciales del usuario")
    print("   2. Ve a 'Mis Facturas Electrónicas' en el menú")
    print("   3. Verás la factura que acabamos de generar")
    print("   4. Podrás descargar el PDF desde el detalle")
    print()
    print("=" * 70)
    
except Exception as e:
    print(f"   ❌ Error al generar factura: {str(e)}")
    import traceback
    traceback.print_exc()
