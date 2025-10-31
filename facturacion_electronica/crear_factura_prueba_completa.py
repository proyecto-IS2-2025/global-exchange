#!/usr/bin/env python
"""
Script para crear una factura electrónica de prueba completa.
Crea: Cliente → Transacción → Factura (Django + SQL Proxy)
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime

# Configurar Django
sys.path.append('/home/jose/proyecto_is2/global-exchange')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from users.models import CustomUser
from clientes.models import Cliente
from divisas.models import Divisa
from transacciones.models import Transaccion
from facturacion_electronica.models import FacturaElectronica
from facturacion_electronica.services import SQLProxyService

def main():
    print("=" * 60)
    print("GENERADOR DE FACTURA DE PRUEBA COMPLETA")
    print("=" * 60)
    
    # 1. Seleccionar usuario
    print("\n1. Usuarios disponibles:")
    usuarios = CustomUser.objects.filter(is_active=True)[:5]
    for i, u in enumerate(usuarios, 1):
        print(f"   {i}. {u.username} ({u.email})")
    
    seleccion = input("\nSelecciona un usuario (número): ").strip()
    try:
        usuario = usuarios[int(seleccion) - 1]
        print(f"✓ Usuario seleccionado: {usuario.username}")
    except:
        print("❌ Selección inválida")
        return
    
    # 2. Obtener o crear cliente
    clientes = Cliente.objects.filter(usuarios=usuario)
    if clientes.exists():
        cliente = clientes.first()
        print(f"✓ Cliente encontrado: {cliente.nombre_completo}")
    else:
        print(f"❌ El usuario {usuario.username} no tiene clientes asociados")
        # Crear cliente de prueba
        crear = input("¿Crear cliente de prueba? (s/n): ").strip().lower()
        if crear != 's':
            return
        
        cliente = Cliente.objects.create(
            cedula=f"TEST{usuario.id}",
            nombre_completo=f"Cliente de {usuario.username}",
            email=usuario.email,
            telefono="0981234567",
            tipo_cliente="minorista",
            esta_activo=True
        )
        cliente.usuarios.add(usuario)
        print(f"✓ Cliente creado: {cliente.nombre_completo}")
    
    # 3. Verificar divisas
    try:
        usd = Divisa.objects.get(code='USD')
        pyg = Divisa.objects.get(code='PYG')
        print(f"✓ Divisas encontradas: USD, PYG")
    except Divisa.DoesNotExist:
        print("❌ No se encontraron las divisas necesarias (USD, PYG)")
        return
    
    # 4. Crear transacción completada
    print("\n2. Creando transacción de prueba...")
    # COMPRA: Cliente compra USD pagando con PYG
    monto_pyg = Decimal("730000.00")  # 730,000 guaraníes
    tasa = Decimal("7300.00")
    monto_usd = monto_pyg / tasa  # 100 USD
    
    transaccion = Transaccion.objects.create(
        cliente=cliente,
        tipo_operacion='compra',
        divisa_origen=pyg,  # Cliente paga en PYG
        divisa_destino=usd,  # Cliente recibe USD
        monto_origen=monto_pyg,
        monto_destino=monto_usd,
        tasa_de_cambio_aplicada=tasa,
        estado='completado',
        metodo_pago='efectivo',
        observaciones='Transacción de prueba para facturación electrónica'
    )
    print(f"✓ Transacción creada: ID {transaccion.id}")
    print(f"  - Tipo: Compra de {monto_usd} USD pagando {monto_pyg} PYG")
    print(f"  - Estado: {transaccion.estado}")
    
    # 5. Generar factura electrónica
    print("\n3. Generando factura electrónica...")
    try:
        # Crear servicio SQL Proxy
        servicio = SQLProxyService()
        servicio.conectar()  # ¡Conectar primero!
        
        # Preparar datos de la factura
        datos_factura = {
            'cliente': {
                'nombre': cliente.nombre_completo,
                'ruc': cliente.cedula,
                'direccion': cliente.direccion or 'Asunción',
                'email': cliente.email or usuario.email,
            },
            'items': [
                {
                    'codigo': '001',
                    'descripcion': f'Compra de divisas: {transaccion.monto_origen} {transaccion.divisa_origen.code}',
                    'cantidad': 1,
                    'precio_unitario': float(transaccion.monto_destino),
                    'descuento': 0,
                }
            ],
            'condicion_operacion': 1,  # Contado
            'forma_pago': 1,  # Efectivo
        }
        
        # Generar factura en SQL Proxy
        resultado = servicio.crear_factura(datos_factura)
        
        # Crear registro en Django
        factura = FacturaElectronica.objects.create(
            transaccion=transaccion,
            numero_factura=resultado['numero_factura'],
            cdc=resultado.get('cdc'),
            estado='aprobado' if resultado.get('cdc') else 'pendiente',
            estado_sifen=resultado.get('estado_sifen', 'Pendiente'),
            url_kude_pdf=resultado.get('url_kude_pdf'),
            url_kude_xml=resultado.get('url_kude_xml')
        )
        
        print(f"✓ Factura generada exitosamente!")
        print(f"  - Número: {factura.numero_factura}")
        print(f"  - Estado: {factura.estado}")
        print(f"  - CDC: {factura.cdc or 'Pendiente'}")
        
        if factura.url_kude_pdf:
            print(f"  - PDF: {factura.url_kude_pdf}")
        if factura.url_kude_xml:
            print(f"  - XML: {factura.url_kude_xml}")
        
        print("\n" + "=" * 60)
        print("✓ FACTURA CREADA EXITOSAMENTE")
        print("=" * 60)
        print(f"\nEl usuario '{usuario.username}' ahora puede ver esta factura")
        print(f"en: http://127.0.0.1:8000/facturacion/mis-facturas/")
        print(f"\nFactura: {factura.numero_factura}")
        print(f"Cliente: {cliente.nombre_completo}")
        print(f"Monto: {monto_pyg} PYG")
        
    except Exception as e:
        print(f"❌ Error al generar factura: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == '__main__':
    main()
