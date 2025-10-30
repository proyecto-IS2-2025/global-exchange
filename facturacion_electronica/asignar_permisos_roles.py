"""
Script para asignar permisos de facturación a los roles existentes
Ejecutar con: poetry run python facturacion_electronica/asignar_permisos_roles.py
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def asignar_permisos():
    """
    Asigna permisos de facturación electrónica a los roles del sistema
    """
    
    print("=" * 70)
    print("ASIGNACIÓN DE PERMISOS DE FACTURACIÓN ELECTRÓNICA")
    print("=" * 70)
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ROL: CLIENTE (no staff)
    # ═══════════════════════════════════════════════════════════════════
    
    print("📋 Configurando permisos para CLIENTES...")
    
    # Los clientes NO están en un grupo, solo tienen is_staff=False
    # Los permisos se manejan directamente en las vistas
    # (verificando factura.transaccion.usuario == request.user)
    
    print("   ✓ Clientes acceden mediante validación en vistas")
    print("   ✓ Pueden ver solo sus propias facturas")
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ROL: OPERADOR
    # ═══════════════════════════════════════════════════════════════════
    
    try:
        operador = Group.objects.get(name='operador')
        print(f"📋 Configurando permisos para {operador.name}...")
        
        permisos_operador = [
            'facturacion_electronica.view_facturas_asignadas',
            'facturacion_electronica.generar_factura',
            'facturacion_electronica.download_kude_pdf',
        ]
        
        asignados = 0
        for perm_code in permisos_operador:
            try:
                app, codename = perm_code.split('.')
                permiso = Permission.objects.get(
                    content_type__app_label=app,
                    codename=codename
                )
                operador.permissions.add(permiso)
                asignados += 1
            except Permission.DoesNotExist:
                print(f"   ⚠️  Permiso {perm_code} no encontrado")
        
        print(f"   ✓ {asignados}/{len(permisos_operador)} permisos asignados")
        print()
    except Group.DoesNotExist:
        print("   ⚠️  Rol 'operador' no existe")
        print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ROL: OBSERVADOR (puede ver todo pero no modificar)
    # ═══════════════════════════════════════════════════════════════════
    
    try:
        observador = Group.objects.get(name='observador')
        print(f"📋 Configurando permisos para {observador.name}...")
        
        permisos_observador = [
            'facturacion_electronica.view_todas_facturas',
            'facturacion_electronica.download_kude_pdf',
            'facturacion_electronica.download_kude_xml',
            'facturacion_electronica.view_reporte_facturacion',
            'facturacion_electronica.export_reporte_facturacion',
        ]
        
        asignados = 0
        for perm_code in permisos_observador:
            try:
                app, codename = perm_code.split('.')
                permiso = Permission.objects.get(
                    content_type__app_label=app,
                    codename=codename
                )
                observador.permissions.add(permiso)
                asignados += 1
            except Permission.DoesNotExist:
                print(f"   ⚠️  Permiso {perm_code} no encontrado")
        
        print(f"   ✓ {asignados}/{len(permisos_observador)} permisos asignados")
        print()
    except Group.DoesNotExist:
        print("   ⚠️  Rol 'observador' no existe")
        print()
    
    # ═══════════════════════════════════════════════════════════════════
    # ROL: ADMINISTRADOR
    # ═══════════════════════════════════════════════════════════════════
    
    try:
        admin = Group.objects.get(name='administrador')
        print(f"📋 Configurando permisos para {admin.name}...")
        
        # Administrador tiene TODOS los permisos de facturación
        permisos_admin = Permission.objects.filter(
            content_type__app_label='facturacion_electronica'
        )
        
        asignados = 0
        for permiso in permisos_admin:
            admin.permissions.add(permiso)
            asignados += 1
        
        print(f"   ✓ {asignados} permisos asignados (TODOS)")
        print()
    except Group.DoesNotExist:
        print("   ⚠️  Rol 'administrador' no existe")
        print()
    
    # ═══════════════════════════════════════════════════════════════════
    # RESUMEN
    # ═══════════════════════════════════════════════════════════════════
    
    print("=" * 70)
    print("✅ ASIGNACIÓN COMPLETADA")
    print("=" * 70)
    print()
    print("Ahora los roles tienen los siguientes permisos:")
    print()
    print("👤 CLIENTES:")
    print("   - Ver sus propias facturas (validado en vista)")
    print("   - Descargar PDFs de sus facturas")
    print()
    print("👨‍💼 OPERADOR:")
    print("   - Ver facturas de clientes asignados")
    print("   - Generar facturas para transacciones")
    print("   - Descargar PDFs")
    print()
    print("�️ OBSERVADOR:")
    print("   - Ver TODAS las facturas")
    print("   - Ver reportes")
    print("   - Descargar PDFs y XMLs")
    print("   - NO puede generar ni cancelar")
    print()
    print("👨‍💻 ADMINISTRADOR:")
    print("   - TODOS los permisos de facturación")
    print("   - Configurar sistema")
    print("   - Inutilizar números")
    print("   - Facturas manuales")
    print("   - Cancelar facturas")
    print()
    print("=" * 70)


if __name__ == "__main__":
    asignar_permisos()
