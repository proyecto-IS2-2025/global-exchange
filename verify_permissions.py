"""
Script rápido para verificar que los permisos estén correctamente asignados.
Uso: python verify_permissions.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from django.contrib.auth.models import Group
from users.models import CustomUser

def verificar_permisos():
    print("="*70)
    print("VERIFICACIÓN DE PERMISOS DEL SISTEMA".center(70))
    print("="*70)
    
    # Verificar grupos
    print("\n📊 RESUMEN DE GRUPOS Y PERMISOS:")
    print("-" * 70)
    
    grupos = Group.objects.all()
    total_permisos = 0
    
    for grupo in grupos:
        count = grupo.permissions.count()
        total_permisos += count
        emoji = "🔴" if count > 50 else "🟡" if count > 20 else "🟢" if count > 10 else "🔵" if count > 5 else "⚪"
        print(f"{emoji} {grupo.name:25} {count:3} permisos")
    
    print("-" * 70)
    print(f"TOTAL: {total_permisos} permisos asignados")
    
    # Verificar usuarios clave
    print("\n👥 VERIFICACIÓN DE USUARIOS CLAVE:")
    print("-" * 70)
    
    usuarios_verificar = [
        ('dev@test.com', 'dev', True),
        ('admin@gmail.com', 'administrador', False),
        ('operador@test.com', 'operador', False),
        ('cliente@test.com', 'cliente', False),
    ]
    
    for email, grupo_esperado, es_superuser in usuarios_verificar:
        try:
            user = CustomUser.objects.get(email=email)
            grupos = [g.name for g in user.groups.all()]
            perms_count = user.get_all_permissions() if not user.is_superuser else "∞"
            
            # Verificaciones
            ok_grupo = grupo_esperado in grupos
            ok_super = user.is_superuser == es_superuser
            ok_activo = user.is_active
            
            if ok_grupo and ok_super and ok_activo:
                print(f"✅ {email:25} Grupo: {grupo_esperado:15} Permisos: {perms_count}")
            else:
                print(f"❌ {email:25} ERROR en configuración")
                if not ok_grupo:
                    print(f"   ⚠️  Grupo esperado: {grupo_esperado}, actual: {grupos}")
                if not ok_super:
                    print(f"   ⚠️  Superuser esperado: {es_superuser}, actual: {user.is_superuser}")
                if not ok_activo:
                    print(f"   ⚠️  Usuario inactivo")
        except CustomUser.DoesNotExist:
            print(f"❌ {email:25} NO ENCONTRADO")
    
    # Verificar permisos específicos críticos
    print("\n🔍 VERIFICACIÓN DE PERMISOS CRÍTICOS:")
    print("-" * 70)
    
    permisos_criticos = [
        ('cliente', 'clientes.view_medios_pago'),
        ('cliente', 'transacciones.cancel_propias_transacciones'),
        ('operador', 'transacciones.manage_estados_transacciones'),
        ('administrador', 'users.manage_usuarios'),
    ]
    
    for grupo_nombre, permiso in permisos_criticos:
        try:
            grupo = Group.objects.get(name=grupo_nombre)
            app_label, codename = permiso.split('.')
            tiene_permiso = grupo.permissions.filter(
                codename=codename,
                content_type__app_label=app_label
            ).exists()
            
            if tiene_permiso:
                print(f"✅ {grupo_nombre:20} tiene {permiso}")
            else:
                print(f"❌ {grupo_nombre:20} NO tiene {permiso}")
        except Group.DoesNotExist:
            print(f"❌ Grupo {grupo_nombre} no encontrado")
    
    print("\n" + "="*70)
    print("✅ VERIFICACIÓN COMPLETADA".center(70))
    print("="*70)

if __name__ == '__main__':
    try:
        verificar_permisos()
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()
