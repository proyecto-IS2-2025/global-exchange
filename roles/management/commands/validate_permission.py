"""
Script de validación del estado actual del sistema de permisos.
Ubicación: roles/management/commands/validate_permissions.py

Ejecutar:
    python manage.py validate_permissions
    python manage.py validate_permissions --check-users
    python manage.py validate_permissions --detailed
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from roles.management.commands.permissions_defs import TODOS_LOS_PERMISOS

User = get_user_model()


class Command(BaseCommand):
    help = 'Valida el estado actual del sistema de permisos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-users',
            action='store_true',
            help='Verifica también los permisos de usuarios individuales',
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Muestra información detallada de cada permiso',
        )

    def handle(self, *args, **options):
        check_users = options.get('check_users', False)
        detailed = options.get('detailed', False)
        
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*70))
        self.stdout.write(self.style.HTTP_INFO('🔍 VALIDACIÓN DEL SISTEMA DE PERMISOS'))
        self.stdout.write(self.style.HTTP_INFO('='*70 + '\n'))
        
        # 1. Verificar permisos definidos
        self._check_permissions_exist()
        
        # 2. Verificar grupos
        self._check_groups_exist()
        
        # 3. Verificar asignación a grupos
        self._check_group_permissions(detailed)
        
        # 4. Verificar usuarios (opcional)
        if check_users:
            self._check_user_permissions()
        
        # 5. Resumen final
        self._print_summary()

    def _check_permissions_exist(self):
        """Verifica que todos los permisos definidos existan en BD"""
        self.stdout.write(self.style.WARNING('\n📋 1. VERIFICANDO PERMISOS DEFINIDOS'))
        self.stdout.write('─'*70)
        
        total = len(TODOS_LOS_PERMISOS)
        encontrados = 0
        faltantes = []
        
        for perm_def in TODOS_LOS_PERMISOS:
            try:
                Permission.objects.get(
                    codename=perm_def['codename'],
                    content_type__app_label=perm_def['app_label']
                )
                encontrados += 1
            except Permission.DoesNotExist:
                faltantes.append(perm_def['codename'])
        
        if encontrados == total:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Todos los permisos existen ({encontrados}/{total})'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Faltan {len(faltantes)} permisos ({encontrados}/{total})'
                )
            )
            for codename in faltantes:
                self.stdout.write(f'   • {codename}')
            
            self.stdout.write(
                self.style.WARNING(
                    '\n💡 Ejecuta: python manage.py sync_permissions'
                )
            )

    def _check_groups_exist(self):
        """Verifica que los grupos necesarios existan"""
        self.stdout.write(self.style.WARNING('\n📋 2. VERIFICANDO GRUPOS/ROLES'))
        self.stdout.write('─'*70)
        
        grupos_requeridos = [
            'dev',
            'administrador',
            'operador',
            'cliente',
            'usuario_registrado',
            'observador',
        ]
        
        for grupo_nombre in grupos_requeridos:
            try:
                grupo = Group.objects.get(name=grupo_nombre)
                permisos_count = grupo.permissions.count()
                usuarios_count = grupo.user_set.count()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {grupo_nombre.ljust(20)} | '
                        f'Permisos: {str(permisos_count).rjust(3)} | '
                        f'Usuarios: {usuarios_count}'
                    )
                )
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Grupo "{grupo_nombre}" no existe')
                )
        
        # Grupos adicionales no estándar
        otros_grupos = Group.objects.exclude(name__in=grupos_requeridos)
        if otros_grupos.exists():
            self.stdout.write(
                self.style.WARNING(f'\n⚠️  Grupos adicionales encontrados:')
            )
            for grupo in otros_grupos:
                self.stdout.write(f'   • {grupo.name}')

    def _check_group_permissions(self, detailed):
        """Verifica permisos asignados a cada grupo"""
        self.stdout.write(self.style.WARNING('\n📋 3. VERIFICANDO ASIGNACIÓN DE PERMISOS'))
        self.stdout.write('─'*70)
        
        grupos = Group.objects.all().order_by('name')
        
        for grupo in grupos:
            permisos = grupo.permissions.select_related('content_type').all()
            
            self.stdout.write(
                self.style.HTTP_INFO(f'\n🔹 {grupo.name.upper()}')
            )
            self.stdout.write(f'   Total de permisos: {permisos.count()}')
            
            if detailed and permisos.exists():
                # Agrupar por módulo
                por_modulo = {}
                for perm in permisos:
                    app = perm.content_type.app_label
                    if app not in por_modulo:
                        por_modulo[app] = []
                    por_modulo[app].append(perm.codename)
                
                for app, codenames in sorted(por_modulo.items()):
                    self.stdout.write(f'\n   📦 {app.upper()}:')
                    for codename in sorted(codenames):
                        self.stdout.write(f'      • {codename}')
            
            # Verificar permisos críticos
            if grupo.name == 'administrador':
                self._check_admin_permissions(grupo)
            elif grupo.name == 'cliente':
                self._check_cliente_permissions(grupo)

    def _check_admin_permissions(self, grupo):
        """Verifica permisos críticos del administrador"""
        criticos = [
            'manage_usuarios',
            'view_all_clientes',
            'manage_descuentos_segmento',
            'manage_cotizaciones_segmento',
        ]
        
        faltantes = []
        for codename in criticos:
            if not grupo.permissions.filter(codename=codename).exists():
                faltantes.append(codename)
        
        if faltantes:
            self.stdout.write(
                self.style.ERROR(
                    f'   ⚠️  Permisos críticos faltantes: {", ".join(faltantes)}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '   ✅ Todos los permisos críticos asignados'
                )
            )

    def _check_cliente_permissions(self, grupo):
        """Verifica permisos básicos del cliente"""
        basicos = [
            'realizar_operacion',
            'view_transacciones_asignadas',
            'view_medios_pago',
            'manage_medios_pago',
        ]
        
        faltantes = []
        for codename in basicos:
            if not grupo.permissions.filter(codename=codename).exists():
                faltantes.append(codename)
        
        if faltantes:
            self.stdout.write(
                self.style.ERROR(
                    f'   ⚠️  Permisos básicos faltantes: {", ".join(faltantes)}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '   ✅ Todos los permisos básicos asignados'
                )
            )

    def _check_user_permissions(self):
        """Verifica permisos de usuarios individuales"""
        self.stdout.write(self.style.WARNING('\n📋 4. VERIFICANDO PERMISOS DE USUARIOS'))
        self.stdout.write('─'*70)
        
        usuarios = User.objects.filter(is_active=True)[:10]  # Primeros 10
        
        if not usuarios.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  No hay usuarios activos en el sistema')
            )
            return
        
        for user in usuarios:
            grupos = list(user.groups.values_list('name', flat=True))
            permisos_totales = user.get_all_permissions()
            
            self.stdout.write(
                self.style.HTTP_INFO(f'\n👤 {user.username} ({user.email})')
            )
            self.stdout.write(f'   Grupos: {", ".join(grupos) if grupos else "Ninguno"}')
            self.stdout.write(f'   Permisos totales: {len(permisos_totales)}')
            
            # Verificar permiso básico
            if user.has_perm('divisas.realizar_operacion'):
                self.stdout.write(
                    self.style.SUCCESS('   ✅ Puede realizar operaciones')
                )
            elif grupos:
                self.stdout.write(
                    self.style.WARNING('   ⚠️  No puede realizar operaciones')
                )

    def _print_summary(self):
        """Imprime resumen final"""
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*70))
        self.stdout.write(self.style.HTTP_INFO('📊 RESUMEN DE VALIDACIÓN'))
        self.stdout.write(self.style.HTTP_INFO('='*70))
        
        # Estadísticas generales
        total_permisos = Permission.objects.count()
        total_grupos = Group.objects.count()
        total_usuarios = User.objects.filter(is_active=True).count()
        
        self.stdout.write(f'\n📈 Estadísticas Generales:')
        self.stdout.write(f'   • Total de permisos en BD:    {total_permisos}')
        self.stdout.write(f'   • Total de grupos/roles:      {total_grupos}')
        self.stdout.write(f'   • Total de usuarios activos:  {total_usuarios}')
        
        # Verificar integridad
        permisos_definidos = len(TODOS_LOS_PERMISOS)
        permisos_personalizados = Permission.objects.filter(
            codename__in=[p['codename'] for p in TODOS_LOS_PERMISOS]
        ).count()
        
        self.stdout.write(f'\n🎯 Permisos Personalizados:')
        self.stdout.write(f'   • Definidos en código:        {permisos_definidos}')
        self.stdout.write(f'   • Creados en BD:              {permisos_personalizados}')
        
        if permisos_personalizados == permisos_definidos:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✅ Sistema de permisos completamente sincronizado'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    '\n❌ Sistema de permisos requiere sincronización'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    '💡 Ejecuta: python manage.py sync_permissions'
                )
            )
        
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*70 + '\n'))