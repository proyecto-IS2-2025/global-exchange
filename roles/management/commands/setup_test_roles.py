"""
Comando para asignar permisos a los roles existentes del sistema.
Versión actualizada con TODOS los permisos personalizados.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from roles.models import RoleStatus  # ✅ IMPORTAR


class Command(BaseCommand):
    help = 'Asigna permisos a los roles existentes del sistema'

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
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write('')
        
        # ✅ CREAR ROLESTATUS PARA TODOS LOS GRUPOS
        self._ensure_role_status()
        
        with transaction.atomic():
            self._configure_admin(verbose)
            self._configure_operador(verbose)
            self._configure_cliente(verbose)
            self._configure_usuario_registrado(verbose)
            self._configure_observador(verbose)
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('✅ Configuración completada exitosamente'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

    def _ensure_role_status(self):
        """
        ✅ NUEVO: Asegura que todos los grupos tengan RoleStatus
        """
        self.stdout.write(self.style.HTTP_INFO('\n🔄 Verificando RoleStatus...'))
        
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
        """
        Obtiene objetos Permission desde una lista de codenames.
        """
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

    def _configure_admin(self, verbose):
        """Configurar permisos para ADMINISTRADOR"""
        codenames = [
            # ═══════════════════════════════════════════════════════
            # USUARIOS (5 permisos personalizados)
            # ═══════════════════════════════════════════════════════
            'manage_usuarios',
            'view_all_usuarios',
            'manage_usuario_roles',
            'activate_deactivate_usuarios',
            'reset_usuario_password',
            
            # Permisos nativos de usuarios
            'view_customuser',
            'add_customuser',
            'change_customuser',
            'delete_customuser',
            
            # ═══════════════════════════════════════════════════════
            # CLIENTES (12 permisos personalizados)
            # ═══════════════════════════════════════════════════════
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
            
            # Permisos nativos de clientes
            'view_cliente',
            'add_cliente',
            'change_cliente',
            'delete_cliente',
            'view_asignacioncliente',
            'add_asignacioncliente',
            'change_asignacioncliente',
            'delete_asignacioncliente',
            'view_clientemediodepago',
            'add_clientemediodepago',
            'change_clientemediodepago',
            'delete_clientemediodepago',
            'view_segmento',
            'add_segmento',
            'change_segmento',
            'delete_segmento',
            'view_descuento',
            'add_descuento',
            'change_descuento',
            'delete_descuento',
            'view_historialdescuentos',
            'view_historialclientemediodepago',
            'view_limitediario',
            'add_limitediario',
            'change_limitediario',
            'delete_limitediario',
            'view_limitemensual',
            'add_limitemensual',
            'change_limitemensual',
            'delete_limitemensual',
            
            # ═══════════════════════════════════════════════════════
            # TRANSACCIONES (7 permisos personalizados)
            # ═══════════════════════════════════════════════════════
            'view_transacciones_globales',
            'view_transacciones_asignadas',
            'manage_estados_transacciones',
            'manage_reversiones_transacciones',
            'cancel_propias_transacciones',
            'view_historial_transacciones',
            'export_transacciones',
            
            # Permisos nativos de transacciones
            'view_transaccion',
            'add_transaccion',
            'change_transaccion',
            'delete_transaccion',
            'view_historialtransaccion',
            
            # ═══════════════════════════════════════════════════════
            # DIVISAS (3 permisos personalizados)
            # ═══════════════════════════════════════════════════════
            'view_cotizaciones_segmento',
            'manage_cotizaciones_segmento',
            'realizar_operacion',
            
            # Permisos nativos de divisas
            'view_divisa',
            'add_divisa',
            'change_divisa',
            'delete_divisa',
            'view_tasacambio',
            'add_tasacambio',
            'change_tasacambio',
            'delete_tasacambio',
            'view_cotizacionsegmento',
            'add_cotizacionsegmento',
            'change_cotizacionsegmento',
            'delete_cotizacionsegmento',
            
            # ═══════════════════════════════════════════════════════
            # MEDIOS DE PAGO (2 permisos personalizados)
            # ═══════════════════════════════════════════════════════
            'view_catalogo_medios_pago',
            'manage_catalogo_medios_pago',
            
            # Permisos nativos de medios de pago
            'view_mediodepago',
            'add_mediodepago',
            'change_mediodepago',
            'delete_mediodepago',
            
            # ═══════════════════════════════════════════════════════
            # ROLES Y GRUPOS
            # ═══════════════════════════════════════════════════════
            'view_group',
            'add_group',
            'change_group',
            'delete_group',
            'view_permission',
        ]
        
        self._assign_permissions('admin', codenames, verbose)

    def _configure_operador(self, verbose):
        """Configurar permisos para OPERADOR"""
        codenames = [
            # ═══════════════════════════════════════════════════════
            # CLIENTES (SOLO ASIGNADOS)
            # ═══════════════════════════════════════════════════════
            'view_assigned_clientes',
            'view_limites_operacion',
            'view_medios_pago',
            'view_descuentos_segmento',
            
            # Permisos nativos necesarios
            'view_cliente',
            'view_clientemediodepago',
            'view_segmento',
            'view_descuento',
            'view_limitediario',
            'view_limitemensual',
            
            # ═══════════════════════════════════════════════════════
            # TRANSACCIONES
            # ═══════════════════════════════════════════════════════
            'view_transacciones_asignadas',
            'manage_estados_transacciones',
            'view_historial_transacciones',
            
            # Permisos nativos necesarios
            'view_transaccion',
            'add_transaccion',
            'change_transaccion',
            'view_historialtransaccion',
            
            # ═══════════════════════════════════════════════════════
            # DIVISAS
            # ═══════════════════════════════════════════════════════
            'realizar_operacion',
            'view_cotizaciones_segmento',
            
            # Permisos nativos necesarios
            'view_divisa',
            'view_tasacambio',
            'view_cotizacionsegmento',
            
            # ═══════════════════════════════════════════════════════
            # MEDIOS DE PAGO
            # ═══════════════════════════════════════════════════════
            'view_catalogo_medios_pago',
            
            # Permisos nativos necesarios
            'view_mediodepago',
        ]
        
        self._assign_permissions('operador', codenames, verbose)

    def _configure_cliente(self, verbose):
        """Configurar permisos para CLIENTE"""
        codenames = [
            # ═══════════════════════════════════════════════════════
            # OPERACIONES BÁSICAS
            # ═══════════════════════════════════════════════════════
            'realizar_operacion',
            
            # ═══════════════════════════════════════════════════════
            # TRANSACCIONES (SOLO LAS PROPIAS)
            # ═══════════════════════════════════════════════════════
            'view_transacciones_asignadas',
            'cancel_propias_transacciones',
            
            # Permisos nativos necesarios
            'view_transaccion',
            
            # ═══════════════════════════════════════════════════════
            # MEDIOS DE PAGO (SOLO LOS PROPIOS)
            # ═══════════════════════════════════════════════════════
            'view_medios_pago',
            
            # Permisos nativos necesarios
            'view_clientemediodepago',
            'view_mediodepago',
            
            # ═══════════════════════════════════════════════════════
            # COTIZACIONES
            # ═══════════════════════════════════════════════════════
            'view_cotizaciones_segmento',
            
            # Permisos nativos necesarios
            'view_divisa',
            'view_tasacambio',
            'view_cotizacionsegmento',
            
            # ═══════════════════════════════════════════════════════
            # DESCUENTOS (CONSULTA)
            # ═══════════════════════════════════════════════════════
            'view_descuentos_segmento',
            
            # Permisos nativos necesarios
            'view_segmento',
            'view_descuento',
        ]
        
        self._assign_permissions('cliente', codenames, verbose)

    def _configure_usuario_registrado(self, verbose):
        """Configurar permisos para USUARIO REGISTRADO (sin cliente asignado)"""
        codenames = [
            # ═══════════════════════════════════════════════════════
            # COTIZACIONES PÚBLICAS (SOLO LECTURA)
            # ═══════════════════════════════════════════════════════
            'view_cotizaciones_segmento',
            
            # Permisos nativos necesarios
            'view_divisa',
            'view_tasacambio',
            'view_cotizacionsegmento',
        ]
        
        self._assign_permissions('usuario_registrado', codenames, verbose)

    def _configure_observador(self, verbose):
        """Configurar permisos para OBSERVADOR (auditoría y reportes)"""
        codenames = [
            # ═══════════════════════════════════════════════════════
            # CLIENTES (SOLO LECTURA)
            # ═══════════════════════════════════════════════════════
            'view_all_clientes',
            'view_limites_operacion',
            'view_descuentos_segmento',
            'view_historial_descuentos',
            
            # Permisos nativos necesarios
            'view_cliente',
            'view_asignacioncliente',
            'view_clientemediodepago',
            'view_historialclientemediodepago',
            'view_segmento',
            'view_descuento',
            'view_historialdescuentos',
            'view_limitediario',
            'view_limitemensual',
            
            # ═══════════════════════════════════════════════════════
            # TRANSACCIONES (SOLO LECTURA)
            # ═══════════════════════════════════════════════════════
            'view_transacciones_globales',
            'view_historial_transacciones',
            'export_transacciones',
            
            # Permisos nativos necesarios
            'view_transaccion',
            'view_historialtransaccion',
            
            # ═══════════════════════════════════════════════════════
            # DIVISAS (SOLO LECTURA)
            # ═══════════════════════════════════════════════════════
            'view_cotizaciones_segmento',
            
            # Permisos nativos necesarios
            'view_divisa',
            'view_tasacambio',
            'view_cotizacionsegmento',
            
            # ═══════════════════════════════════════════════════════
            # MEDIOS DE PAGO (SOLO LECTURA)
            # ═══════════════════════════════════════════════════════
            'view_catalogo_medios_pago',
            
            # Permisos nativos necesarios
            'view_mediodepago',
            
            # ═══════════════════════════════════════════════════════
            # USUARIOS (SOLO LECTURA)
            # ═══════════════════════════════════════════════════════
            'view_all_usuarios',
            
            # Permisos nativos necesarios
            'view_customuser',
        ]
        
        self._assign_permissions('observador', codenames, verbose)