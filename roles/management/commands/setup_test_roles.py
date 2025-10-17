"""
Comando para asignar permisos a los roles existentes del sistema.
✅ VERSIÓN LIMPIA - Solo permisos personalizados custom.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from roles.models import RoleStatus


class Command(BaseCommand):
    help = 'Asigna permisos custom a los roles del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada de permisos asignados',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('  CONFIGURACIÓN DE PERMISOS POR ROL'))
        self.stdout.write(self.style.HTTP_INFO('  ✅ SOLO PERMISOS CUSTOM'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write('')
        
        # ✅ CREAR ROLESTATUS PARA TODOS LOS GRUPOS
        self._ensure_role_status()
        
        with transaction.atomic():
            self._configure_dev(verbose)
            self._configure_administrador(verbose)
            self._configure_operador(verbose)
            self._configure_cliente(verbose)
            self._configure_usuario_registrado(verbose)
            self._configure_observador(verbose)
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('✅ Configuración completada exitosamente'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

    def _ensure_role_status(self):
        """✅ Asegura que todos los grupos tengan RoleStatus"""
        self.stdout.write(self.style.HTTP_INFO('\n📄 Verificando RoleStatus...'))
        
        groups = Group.objects.all()
        created_count = 0
        
        for group in groups:
            status, created = RoleStatus.objects.get_or_create(
                group=group,
                defaults={'is_active': True}
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Creado RoleStatus para: {group.name}")
                )
        
        if created_count == 0:
            self.stdout.write(
                self.style.WARNING("  ○ Todos los grupos ya tienen RoleStatus")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"  ✅ {created_count} RoleStatus creados")
            )
        
        self.stdout.write('')

    def _get_permissions(self, codenames, verbose=False):
        """Obtiene objetos Permission desde una lista de codenames custom."""
        permissions = Permission.objects.filter(codename__in=codenames)
        
        if verbose:
            found = set(permissions.values_list('codename', flat=True))
            missing = set(codenames) - found
            
            for perm in permissions:
                self.stdout.write(
                    f"  ✓ {perm.content_type.app_label}.{perm.codename}"
                )
            
            if missing:
                for codename in missing:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠️  Permiso no encontrado: {codename}")
                    )
        
        return permissions

    def _assign_permissions(self, group_name, codenames, verbose):
        """Helper para asignar permisos a un grupo"""
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Grupo '{group_name}' no existe")
            )
            return
        
        self.stdout.write(self.style.HTTP_INFO(f"\n{'─' * 60}"))
        self.stdout.write(self.style.HTTP_INFO(f"📋 Configurando permisos para: {group_name.upper()}"))
        self.stdout.write(self.style.HTTP_INFO(f"{'─' * 60}"))
        
        permissions = self._get_permissions(codenames, verbose)
        group.permissions.set(permissions)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ {group_name}: {permissions.count()} permisos asignados"
            )
        )

    def _configure_dev(self, verbose):
        """
        ✅ DESARROLLADOR - Acceso total a permisos custom
        """
        codenames = [
            # ═══════════════════════════════════════════════════════════════
            # USUARIOS (5 custom)
            # ═══════════════════════════════════════════════════════════════
            'manage_usuarios',
            'view_all_usuarios',
            'manage_usuario_roles',
            'activate_deactivate_usuarios',
            'reset_usuario_password',
            
            # ═══════════════════════════════════════════════════════════════
            # MFA (2 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_mfa_config',
            'manage_mfa_config',
            
            # ═══════════════════════════════════════════════════════════════
            # CLIENTES (13 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_all_clientes',
            'view_assigned_clientes',
            'manage_cliente_assignment',
            'manage_limites_operacion',
            'view_limites_operacion',
            'admin_manage_limites',
            'manage_medios_pago',
            'view_medios_pago',
            'export_clientes',
            'view_descuentos_segmento',
            'manage_descuentos_segmento',
            'view_historial_descuentos',
            
            # ═══════════════════════════════════════════════════════════════
            # TRANSACCIONES (7 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_transacciones_globales',
            'view_transacciones_asignadas',
            'manage_estados_transacciones',
            'manage_reversiones_transacciones',
            'cancel_propias_transacciones',
            'view_historial_transacciones',
            'export_transacciones',
            
            # ═══════════════════════════════════════════════════════════════
            # DIVISAS (7 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_cotizaciones_segmento',
            'manage_cotizaciones_segmento',
            'realizar_operacion',
            'manage_divisas',
            'view_divisas',
            'manage_tasas_cambio',
            'view_tasas_cambio',
            
            # ═══════════════════════════════════════════════════════════════
            # MEDIOS DE PAGO (2 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_catalogo_medios_pago',
            'manage_catalogo_medios_pago',
        ]
        # Total: 35 permisos custom
        
        self._assign_permissions('dev', codenames, verbose)

    def _configure_administrador(self, verbose):
        """
        ✅ ADMINISTRADOR - Casi todos los permisos custom (excepto algunos críticos)
        """
        codenames = [
            # ═══════════════════════════════════════════════════════════════
            # USUARIOS (5 custom)
            # ═══════════════════════════════════════════════════════════════
            'manage_usuarios',
            'view_all_usuarios',
            'manage_usuario_roles',
            'activate_deactivate_usuarios',
            'reset_usuario_password',
            
            # ═══════════════════════════════════════════════════════════════
            # MFA (2 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_mfa_config',
            'manage_mfa_config',
            
            # ═══════════════════════════════════════════════════════════════
            # CLIENTES (13 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_all_clientes',
            'view_assigned_clientes',
            'manage_cliente_assignment',
            'manage_limites_operacion',
            'view_limites_operacion',
            'admin_manage_limites',
            'manage_medios_pago',
            'view_medios_pago',
            'export_clientes',
            'view_descuentos_segmento',
            'manage_descuentos_segmento',
            'view_historial_descuentos',
            
            # ═══════════════════════════════════════════════════════════════
            # TRANSACCIONES (6 custom - sin reversiones)
            # ═══════════════════════════════════════════════════════════════
            'view_transacciones_globales',
            'view_transacciones_asignadas',
            'manage_estados_transacciones',
            # 'manage_reversiones_transacciones',  # Solo dev
            'view_historial_transacciones',
            'export_transacciones',
            
            # ═══════════════════════════════════════════════════════════════
            # DIVISAS (7 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_cotizaciones_segmento',
            'manage_cotizaciones_segmento',
            'realizar_operacion',
            'manage_divisas',
            'view_divisas',
            'manage_tasas_cambio',
            'view_tasas_cambio',
            
            # ═══════════════════════════════════════════════════════════════
            # MEDIOS DE PAGO (2 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_catalogo_medios_pago',
            'manage_catalogo_medios_pago',
        ]
        # Total: ~34 permisos custom
        
        self._assign_permissions('administrador', codenames, verbose)

    def _configure_operador(self, verbose):
        """
        ✅ OPERADOR - Permisos operativos (sin gestión administrativa)
        """
        codenames = [
            # ═══════════════════════════════════════════════════════════════
            # CLIENTES (5 custom - solo lectura)
            # ═══════════════════════════════════════════════════════════════
            'view_assigned_clientes',
            'view_limites_operacion',
            'view_medios_pago',
            'view_descuentos_segmento',
            
            # ═══════════════════════════════════════════════════════════════
            # TRANSACCIONES (4 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_transacciones_asignadas',
            'view_transacciones_globales',
            'manage_estados_transacciones',
            'view_historial_transacciones',
            
            # ═══════════════════════════════════════════════════════════════
            # DIVISAS (4 custom)
            # ═══════════════════════════════════════════════════════════════
            'realizar_operacion',
            'view_cotizaciones_segmento',
            'view_divisas',
            'manage_tasas_cambio',
            'view_tasas_cambio',
            
            # ═══════════════════════════════════════════════════════════════
            # MEDIOS DE PAGO (1 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_catalogo_medios_pago',
        ]
        # Total: ~14 permisos custom
        
        self._assign_permissions('operador', codenames, verbose)

    def _configure_cliente(self, verbose):
        """
        ✅ CLIENTE (Operador de Cuenta) - Operaciones propias
        """
        codenames = [
            # ═══════════════════════════════════════════════════════════════
            # OPERACIONES (1 custom)
            # ═══════════════════════════════════════════════════════════════
            'realizar_operacion',
            
            # ═══════════════════════════════════════════════════════════════
            # TRANSACCIONES (2 custom - solo propias)
            # ═══════════════════════════════════════════════════════════════
            'view_transacciones_asignadas',
            'cancel_propias_transacciones',
            
            # ═══════════════════════════════════════════════════════════════
            # MEDIOS DE PAGO (2 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_medios_pago',
            'manage_medios_pago',
            
            # ═══════════════════════════════════════════════════════════════
            # DIVISAS (1 custom - consulta)
            # ═══════════════════════════════════════════════════════════════
            'view_cotizaciones_segmento',
            
            # ═══════════════════════════════════════════════════════════════
            # DESCUENTOS (1 custom - consulta)
            # ═══════════════════════════════════════════════════════════════
            'view_descuentos_segmento',
            
            # ═══════════════════════════════════════════════════════════════
            # CLIENTES (1 custom - consulta)
            # ═══════════════════════════════════════════════════════════════
            'view_assigned_clientes',
        ]
        # Total: ~8 permisos custom
        
        self._assign_permissions('cliente', codenames, verbose)

    def _configure_usuario_registrado(self, verbose):
        """
        ✅ USUARIO REGISTRADO - Solo consulta pública
        """
        codenames = [
            # ═══════════════════════════════════════════════════════════════
            # COTIZACIONES PÚBLICAS (1 custom)
            # ═══════════════════════════════════════════════════════════════
            'view_cotizaciones_segmento',
        ]
        # Total: 1 permiso custom
        
        self._assign_permissions('usuario_registrado', codenames, verbose)

    def _configure_observador(self, verbose):
        """
        ✅ OBSERVADOR - Solo lectura (auditoría)
        """
        codenames = [
            # ═══════════════════════════════════════════════════════════════
            # CLIENTES (4 custom - lectura)
            # ═══════════════════════════════════════════════════════════════
            'view_all_clientes',
            'view_limites_operacion',
            'view_descuentos_segmento',
            'view_historial_descuentos',
            
            # ═══════════════════════════════════════════════════════════════
            # TRANSACCIONES (3 custom - lectura)
            # ═══════════════════════════════════════════════════════════════
            'view_transacciones_globales',
            'view_historial_transacciones',
            'export_transacciones',
            
            # ═══════════════════════════════════════════════════════════════
            # DIVISAS (3 custom - lectura)
            # ═══════════════════════════════════════════════════════════════
            'view_cotizaciones_segmento',
            'view_divisas',
            'view_tasas_cambio',
            
            # ═══════════════════════════════════════════════════════════════
            # MEDIOS DE PAGO (1 custom - lectura)
            # ═══════════════════════════════════════════════════════════════
            'view_catalogo_medios_pago',
            
            # ═══════════════════════════════════════════════════════════════
            # USUARIOS (1 custom - lectura)
            # ═══════════════════════════════════════════════════════════════
            'view_all_usuarios',
        ]
        # Total: ~12 permisos custom
        
        self._assign_permissions('observador', codenames, verbose)