"""
Script para asignar permisos de facturación electrónica a roles existentes
Ejecutar con: poetry run python facturacion_electronica/asignar_permisos_facturacion.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

def asignar_permisos():
    """Asigna permisos de facturación según el rol"""
    
    print("\n" + "="*70)
    print("🔐 ASIGNACIÓN DE PERMISOS DE FACTURACIÓN ELECTRÓNICA")
    print("="*70 + "\n")
    
    # Obtener content type de FacturaElectronica
    try:
        from facturacion_electronica.models import FacturaElectronica
        ct = ContentType.objects.get_for_model(FacturaElectronica)
    except Exception as e:
        print(f"❌ Error al obtener ContentType: {e}")
        return
    
    # =========================================================================
    # CLIENTE - Permisos básicos para ver sus propias facturas
    # =========================================================================
    try:
        role_cliente = Group.objects.get(name='cliente')
        permisos_cliente = [
            'view_facturas_propias',
            'download_kude_pdf',
        ]
        
        print(f"📋 Asignando permisos a rol: CLIENTE")
        for codename in permisos_cliente:
            try:
                perm = Permission.objects.get(content_type=ct, codename=codename)
                role_cliente.permissions.add(perm)
                print(f"   ✅ {codename}")
            except Permission.DoesNotExist:
                print(f"   ⚠️  {codename} - NO EXISTE")
        print()
    except Group.DoesNotExist:
        print("⚠️  Rol 'cliente' no existe\n")
    
    # =========================================================================
    # OPERADOR - Permisos para generar facturas y ver de clientes asignados
    # =========================================================================
    try:
        role_operador = Group.objects.get(name='operador')
        permisos_operador = [
            'view_facturas_asignadas',
            'generar_factura',
            'download_kude_pdf',
            'download_kude_xml',
        ]
        
        print(f"📋 Asignando permisos a rol: OPERADOR")
        for codename in permisos_operador:
            try:
                perm = Permission.objects.get(content_type=ct, codename=codename)
                role_operador.permissions.add(perm)
                print(f"   ✅ {codename}")
            except Permission.DoesNotExist:
                print(f"   ⚠️  {codename} - NO EXISTE")
        print()
    except Group.DoesNotExist:
        print("⚠️  Rol 'operador' no existe\n")
    
    # =========================================================================
    # OBSERVADOR - Permisos de solo lectura (todas las facturas)
    # =========================================================================
    try:
        role_observador = Group.objects.get(name='observador')
        permisos_observador = [
            'view_todas_facturas',
            'view_reporte_facturacion',
            'download_kude_pdf',
            'download_kude_xml',
        ]
        
        print(f"📋 Asignando permisos a rol: OBSERVADOR")
        for codename in permisos_observador:
            try:
                perm = Permission.objects.get(content_type=ct, codename=codename)
                role_observador.permissions.add(perm)
                print(f"   ✅ {codename}")
            except Permission.DoesNotExist:
                print(f"   ⚠️  {codename} - NO EXISTE")
        print()
    except Group.DoesNotExist:
        print("⚠️  Rol 'observador' no existe\n")
    
    # =========================================================================
    # ADMINISTRADOR - Todos los permisos
    # =========================================================================
    try:
        role_admin = Group.objects.get(name='administrador')
        permisos_admin = [
            'view_facturas_propias',
            'view_facturas_asignadas',
            'view_todas_facturas',
            'generar_factura',
            'generar_factura_manual',
            'cancelar_factura',
            'inutilizar_numero',
            'download_kude_pdf',
            'download_kude_xml',
            'view_reporte_facturacion',
            'export_reporte_facturacion',
            'manage_config_facturacion',
            'sync_sifen',
        ]
        
        print(f"📋 Asignando permisos a rol: ADMINISTRADOR")
        for codename in permisos_admin:
            try:
                perm = Permission.objects.get(content_type=ct, codename=codename)
                role_admin.permissions.add(perm)
                print(f"   ✅ {codename}")
            except Permission.DoesNotExist:
                print(f"   ⚠️  {codename} - NO EXISTE")
        print()
    except Group.DoesNotExist:
        print("⚠️  Rol 'administrador' no existe\n")
    
    # =========================================================================
    # DEV - Todos los permisos (igual que admin)
    # =========================================================================
    try:
        role_dev = Group.objects.get(name='dev')
        permisos_dev = permisos_admin  # Mismo que admin
        
        print(f"📋 Asignando permisos a rol: DEV")
        for codename in permisos_dev:
            try:
                perm = Permission.objects.get(content_type=ct, codename=codename)
                role_dev.permissions.add(perm)
                print(f"   ✅ {codename}")
            except Permission.DoesNotExist:
                print(f"   ⚠️  {codename} - NO EXISTE")
        print()
    except Group.DoesNotExist:
        print("⚠️  Rol 'dev' no existe\n")
    
    print("="*70)
    print("✅ Asignación de permisos completada")
    print("="*70 + "\n")


if __name__ == '__main__':
    asignar_permisos()
