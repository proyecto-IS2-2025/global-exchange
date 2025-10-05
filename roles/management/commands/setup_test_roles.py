"""
Comando para asignar permisos a los roles existentes del sistema.
Versión actualizada con permisos de TRANSACCIONES.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.contrib.contenttypes.models import ContentType


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
            # === USUARIOS ===
            'manage_usuarios',
            'view_all_usuarios',
            'manage_usuario_roles',
            'activate_deactivate_usuarios',
            'reset_usuario_password',
            
            # === CLIENTES ===
            'view_all_clientes',
            'manage_cliente_assignment',
            'manage_limites_operacion',
            'view_limites_operacion',
            'view_descuentos_segmento',
            'view_assigned_clientes',
            'view_cliente',
            'add_cliente',
            'change_cliente',
            'delete_cliente',
            'view_medios_pago',
            'view_clientemediodepago',
            'add_clientemediodepago',
            'change_clientemediodepago',
            'delete_clientemediodepago',
            
            # === TRANSACCIONES ===
            'view_transacciones_globales',
            'view_transacciones_asignadas',
            'manage_estados_transacciones',
            'manage_reversiones_transacciones',
            'cancel_propias_transacciones',
            'view_historial_transacciones',
            'export_transacciones',
            'view_transaccion',
            'add_transaccion',
            'change_transaccion',
            'delete_transaccion',
            'view_historialtransaccion',
            
            # === DIVISAS ===
            'realizar_operacion',
            'manage_cotizaciones_segmento',
            'approve_operaciones_divisas',
            'view_cotizaciones_segmento',
            'view_divisa',
            'add_divisa',
            'change_divisa',
            'delete_divisa',
            'view_tasacambio',
            'add_tasacambio',
            'change_tasacambio',
            'delete_tasacambio',
            
            # === MEDIOS DE PAGO ===
            'manage_catalogo_medios_pago',
            'view_catalogo_medios_pago',
            'view_mediodepago',
            'add_mediodepago',
            'change_mediodepago',
            'delete_mediodepago',
            
            # === LÍMITES ===
            'view_limitediario',
            'add_limitediario',
            'change_limitediario',
            'delete_limitediario',
            'view_limitemensual',
            'add_limitemensual',
            'change_limitemensual',
            'delete_limitemensual',
            
            # === ASIGNACIONES ===
            'view_asignacioncliente',
            'add_asignacioncliente',
            'change_asignacioncliente',
            'delete_asignacioncliente',
        ]
        
        self._assign_permissions('admin', codenames, verbose)

    def _configure_operador(self, verbose):
        """Configurar permisos para OPERADOR"""
        codenames = [
            # === CLIENTES (SOLO ASIGNADOS) ===
            'view_assigned_clientes',
            'view_cliente',
            'view_medios_pago',
            'view_clientemediodepago',
            'view_descuentos_segmento',
            
            # === TRANSACCIONES ===
            'view_transacciones_asignadas',
            'manage_estados_transacciones',
            'view_historial_transacciones',
            'view_transaccion',
            'add_transaccion',
            
            # === DIVISAS ===
            'realizar_operacion',
            'view_cotizaciones_segmento',
            'view_divisa',
            'view_tasacambio',
            
            # === MEDIOS DE PAGO ===
            'view_catalogo_medios_pago',
            'view_mediodepago',
        ]
        
        self._assign_permissions('operador', codenames, verbose)

    def _configure_cliente(self, verbose):
        """Configurar permisos para CLIENTE"""
        codenames = [
            # === OPERACIONES ===
            'realizar_operacion',
            
            # === TRANSACCIONES (SOLO LAS PROPIAS) ===
            'view_transacciones_asignadas',
            'cancel_propias_transacciones',
            'view_transaccion',
            
            # === MEDIOS DE PAGO ===
            'view_medios_pago',
            'view_clientemediodepago',
            
            # === COTIZACIONES ===
            'view_cotizaciones_segmento',
            'view_divisa',
            'view_tasacambio',
        ]
        
        self._assign_permissions('cliente', codenames, verbose)

    def _configure_usuario_registrado(self, verbose):
        """Configurar permisos para USUARIO REGISTRADO"""
        codenames = [
            # === COTIZACIONES PÚBLICAS ===
            'view_cotizaciones_segmento',
            'view_divisa',
            'view_tasacambio',
        ]
        
        self._assign_permissions('usuario_registrado', codenames, verbose)

    def _configure_observador(self, verbose):
        """Configurar permisos para OBSERVADOR (solo lectura)"""
        codenames = [
            # === CLIENTES (SOLO LECTURA) ===
            'view_all_clientes',
            'view_cliente',
            'view_clientemediodepago',
            'view_asignacioncliente',
            
            # === DIVISAS (SOLO LECTURA) ===
            'view_cotizaciones_segmento',
            'view_divisa',
            'view_tasacambio',
            
            # === TRANSACCIONES (SOLO LECTURA) ===
            'view_transacciones_globales',
            'view_transaccion',
            'view_historial_transacciones',
            'view_historialtransaccion',
            'export_transacciones',
            
            # === MEDIOS DE PAGO (SOLO LECTURA) ===
            'view_catalogo_medios_pago',
            'view_mediodepago',
            
            # === LÍMITES (SOLO LECTURA) ===
            'view_limites_operacion',
            'view_limitediario',
            'view_limitemensual',
        ]
        
        self._assign_permissions('observador', codenames, verbose)