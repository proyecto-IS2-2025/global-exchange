"""
Comando para asignar permisos a grupos según la matriz de permisos del sistema.
Este comando debe ejecutarse después de sync_permissions.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db import transaction

# Definición de permisos por grupo
PERMISOS_POR_GRUPO = {
    'administrador': [
        # CLIENTES - Administrador tiene acceso completo
        'clientes.add_cliente',
        'clientes.change_cliente',
        'clientes.delete_cliente',
        'clientes.view_cliente',
        'clientes.view_medios_pago',
        'clientes.view_all_clientes',
        'clientes.manage_medios_pago',
        'clientes.manage_cliente_assignment',
        'clientes.admin_manage_limites',
        'clientes.manage_limites_operacion',
        'clientes.view_limites_operacion',
        'clientes.manage_descuentos_segmento',
        'clientes.view_descuentos_segmento',
        'clientes.view_historial_descuentos',
        'clientes.export_clientes',
        
        # DIVISAS
        'divisas.add_divisa',
        'divisas.change_divisa',
        'divisas.delete_divisa',
        'divisas.view_divisa',
        'divisas.manage_divisas',
        'divisas.manage_cotizaciones_segmento',
        'divisas.view_cotizaciones_segmento',
        'divisas.manage_denominaciones',
        'divisas.view_denominaciones',
        'divisas.manage_tasas_cambio',
        'divisas.view_tasas_cambio',
        'divisas.realizar_operacion',
        
        # TRANSACCIONES
        'transacciones.add_transaccion',
        'transacciones.change_transaccion',
        'transacciones.delete_transaccion',
        'transacciones.view_transaccion',
        'transacciones.view_transacciones_asignadas',
        'transacciones.view_transacciones_globales',
        'transacciones.manage_estados_transacciones',
        'transacciones.manage_reversiones_transacciones',
        'transacciones.view_historial_transacciones',
        'transacciones.export_transacciones',
        
        # MEDIOS DE PAGO
        'medios_pago.add_mediodepago',
        'medios_pago.change_mediodepago',
        'medios_pago.delete_mediodepago',
        'medios_pago.view_mediodepago',
        'medios_pago.manage_catalogo_medios_pago',
        'medios_pago.view_catalogo_medios_pago',
        
        # USUARIOS
        'users.add_customuser',
        'users.change_customuser',
        'users.delete_customuser',
        'users.view_customuser',
        'users.manage_usuarios',
        'users.view_all_usuarios',
        'users.manage_usuario_roles',
        'users.activate_deactivate_usuarios',
        'users.reset_usuario_password',
        
        # ROLES
        'roles.manage_roles',
        'roles.view_roles_list',
        'roles.view_role_details',
        'roles.manage_group_permissions',
        'roles.view_group_permissions',
        'roles.manage_group_users',
        'roles.view_group_users',
        'roles.view_permission_matrix',
        'roles.manage_role_status',
        
        # MFA
        'mfa.manage_mfa_config',
        'mfa.view_mfa_config',
    ],
    
    'operador': [
        # CLIENTES - Operador puede ver y gestionar clientes
        'clientes.add_cliente',
        'clientes.change_cliente',
        'clientes.view_cliente',
        'clientes.view_medios_pago',
        'clientes.view_assigned_clientes',
        'clientes.manage_medios_pago',
        'clientes.view_limites_operacion',
        'clientes.view_descuentos_segmento',
        
        # DIVISAS - Puede ver y actualizar cotizaciones
        'divisas.view_divisa',
        'divisas.view_cotizaciones_segmento',
        'divisas.manage_cotizaciones_segmento',
        'divisas.view_denominaciones',
        'divisas.view_tasas_cambio',
        'divisas.realizar_operacion',
        
        # TRANSACCIONES - Puede gestionar transacciones
        'transacciones.add_transaccion',
        'transacciones.change_transaccion',
        'transacciones.view_transaccion',
        'transacciones.view_transacciones_asignadas',
        'transacciones.manage_estados_transacciones',
        'transacciones.view_historial_transacciones',
        
        # MEDIOS DE PAGO
        'medios_pago.view_mediodepago',
        'medios_pago.view_catalogo_medios_pago',
        
        # USUARIOS
        'users.view_customuser',
    ],
    
    'observador': [
        # CLIENTES - Solo lectura
        'clientes.view_cliente',
        'clientes.view_medios_pago',
        'clientes.view_all_clientes',
        'clientes.view_limites_operacion',
        'clientes.view_descuentos_segmento',
        'clientes.view_historial_descuentos',
        
        # DIVISAS - Solo lectura
        'divisas.view_divisa',
        'divisas.view_cotizaciones_segmento',
        'divisas.view_denominaciones',
        'divisas.view_tasas_cambio',
        
        # TRANSACCIONES - Solo lectura
        'transacciones.view_transaccion',
        'transacciones.view_transacciones_globales',
        'transacciones.view_historial_transacciones',
        
        # MEDIOS DE PAGO
        'medios_pago.view_mediodepago',
        'medios_pago.view_catalogo_medios_pago',
        
        # USUARIOS
        'users.view_customuser',
    ],
    
    'cliente': [
        # CLIENTES - El cliente puede ver sus propios datos
        'clientes.view_cliente',
        'clientes.change_cliente',  # Solo sus propios datos
        'clientes.view_medios_pago',
        'clientes.manage_medios_pago',  # Solo sus propios medios
        
        # DIVISAS - Solo ver cotizaciones de su segmento y realizar operaciones
        'divisas.view_divisa',
        'divisas.view_cotizaciones_segmento',
        'divisas.view_denominaciones',
        'divisas.realizar_operacion',  # ⭐ Permite realizar operaciones de compra/venta
        
        # TRANSACCIONES - Gestionar sus propias transacciones
        'transacciones.add_transaccion',
        'transacciones.view_transaccion',
        'transacciones.view_transacciones_asignadas',  # ⭐ Ver sus propias transacciones
        'transacciones.view_historial_transacciones',  # ⭐ Ver historial de cambios
        'transacciones.cancel_propias_transacciones',
        
        # MEDIOS DE PAGO
        'medios_pago.view_mediodepago',
        'medios_pago.view_catalogo_medios_pago',
        
        # FACTURACIÓN ELECTRÓNICA - Ver y descargar sus propias facturas
        'facturacion_electronica.view_facturas_propias',  # ⭐ Ver sus propias facturas
        'facturacion_electronica.download_kude_pdf',  # ⭐ Descargar facturas en PDF
        'facturacion_electronica.download_kude_xml',  # ⭐ Descargar facturas en XML
    ],
    
    'usuario_registrado': [
        # CLIENTES - Usuario registrado tiene acceso limitado
        'clientes.view_cliente',
        'clientes.change_cliente',  # Solo sus propios datos
        'clientes.view_medios_pago',
        
        # DIVISAS - Solo ver cotizaciones
        'divisas.view_divisa',
        'divisas.view_cotizaciones_segmento',
        
        # TRANSACCIONES - Solo ver
        'transacciones.view_transaccion',
        
        # MEDIOS DE PAGO
        'medios_pago.view_mediodepago',
        'medios_pago.view_catalogo_medios_pago',
    ],
    
    'usuario_no_registrado': [
        # Solo puede ver cotizaciones públicas
        'divisas.view_divisa',
        'divisas.view_cotizaciones_segmento',
        'medios_pago.view_catalogo_medios_pago',
    ],
    
    'dev': [
        # El grupo dev no necesita permisos porque sus usuarios son superusuarios
        # Pero podemos asignarle todos los permisos por consistencia
    ],
}


class Command(BaseCommand):
    help = 'Asigna permisos a grupos según la matriz de permisos del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Elimina todos los permisos existentes antes de asignar los nuevos',
        )

    def handle(self, *args, **options):
        verbosity = options.get('verbosity', 1)
        force = options.get('force', False)
        
        if verbosity >= 1:
            self.stdout.write(self.style.WARNING('\n🔐 Iniciando asignación de permisos a grupos...\n'))
        
        grupos_actualizados = 0
        permisos_asignados = 0
        permisos_no_encontrados = []
        
        with transaction.atomic():
            for grupo_nombre, codenames in PERMISOS_POR_GRUPO.items():
                try:
                    grupo = Group.objects.get(name=grupo_nombre)
                    
                    if force:
                        # Eliminar todos los permisos existentes
                        grupo.permissions.clear()
                        if verbosity >= 2:
                            self.stdout.write(f'  🗑️  Permisos eliminados del grupo: {grupo_nombre}')
                    
                    # Contador de permisos para este grupo
                    permisos_grupo = 0
                    
                    for codename_completo in codenames:
                        # Separar app_label.codename
                        try:
                            app_label, codename = codename_completo.split('.')
                            
                            # Buscar el permiso
                            permiso = Permission.objects.filter(
                                codename=codename,
                                content_type__app_label=app_label
                            ).first()
                            
                            if permiso:
                                grupo.permissions.add(permiso)
                                permisos_grupo += 1
                                permisos_asignados += 1
                                
                                if verbosity >= 2:
                                    self.stdout.write(
                                        f'    ✓ {grupo_nombre}: {codename_completo}'
                                    )
                            else:
                                permisos_no_encontrados.append(f'{grupo_nombre}: {codename_completo}')
                                if verbosity >= 1:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'    ⚠️  Permiso no encontrado: {codename_completo} para {grupo_nombre}'
                                        )
                                    )
                        except ValueError:
                            if verbosity >= 1:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f'    ❌ Formato inválido: {codename_completo}'
                                    )
                                )
                    
                    grupos_actualizados += 1
                    if verbosity >= 1:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✅ Grupo "{grupo_nombre}": {permisos_grupo} permisos asignados'
                            )
                        )
                    
                except Group.DoesNotExist:
                    if verbosity >= 1:
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ❌ Grupo no encontrado: {grupo_nombre}'
                            )
                        )
        
        # Resumen
        if verbosity >= 1:
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('✅ ASIGNACIÓN COMPLETADA'))
            self.stdout.write('='*60)
            self.stdout.write(f'  📊 Grupos actualizados: {grupos_actualizados}')
            self.stdout.write(f'  🔑 Permisos asignados: {permisos_asignados}')
            
            if permisos_no_encontrados:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠️  Permisos no encontrados: {len(permisos_no_encontrados)}'
                    )
                )
                if verbosity >= 2:
                    self.stdout.write('\n  Permisos no encontrados:')
                    for perm in permisos_no_encontrados:
                        self.stdout.write(f'    - {perm}')
            
            self.stdout.write('='*60 + '\n')
