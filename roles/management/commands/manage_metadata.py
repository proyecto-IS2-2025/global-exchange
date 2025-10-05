"""
Comando para gestionar metadata de permisos desde la terminal.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from roles.models import PermissionMetadata
from tabulate import tabulate


class Command(BaseCommand):
    help = 'Gestiona metadata de permisos'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['list', 'show', 'create', 'update', 'delete', 'sync'],
            help='Acción a realizar'
        )
        parser.add_argument(
            '--permission-id',
            type=int,
            help='ID del permiso'
        )
        parser.add_argument(
            '--codename',
            type=str,
            help='Codename del permiso'
        )
        parser.add_argument(
            '--modulo',
            type=str,
            help='Filtrar por módulo'
        )
        parser.add_argument(
            '--with-metadata',
            action='store_true',
            help='Solo mostrar permisos CON metadata'
        )
        parser.add_argument(
            '--without-metadata',
            action='store_true',
            help='Solo mostrar permisos SIN metadata'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'list':
            self.list_metadata(options)
        elif action == 'show':
            self.show_metadata(options)
        elif action == 'sync':
            self.sync_all_metadata()
        elif action == 'create':
            self.create_metadata(options)
        elif action == 'update':
            self.update_metadata(options)
        elif action == 'delete':
            self.delete_metadata(options)

    def list_metadata(self, options):
        """Lista todos los permisos y su metadata"""
        modulo = options.get('modulo')
        with_metadata = options.get('with_metadata')
        without_metadata = options.get('without_metadata')
        
        permissions = Permission.objects.select_related(
            'content_type'
        ).prefetch_related('metadata').all()
        
        # Filtrar por app relevante
        permissions = permissions.filter(
            content_type__app_label__in=[
                'clientes', 'divisas', 'transacciones', 
                'medios_pago', 'users', 'auth'
            ]
        )
        
        # Aplicar filtros
        if modulo:
            permissions = permissions.filter(
                content_type__app_label=modulo
            )
        
        data = []
        for perm in permissions:
            has_metadata = hasattr(perm, 'metadata')
            
            # Aplicar filtros de metadata
            if with_metadata and not has_metadata:
                continue
            if without_metadata and has_metadata:
                continue
            
            if has_metadata:
                meta = perm.metadata
                data.append([
                    perm.id,
                    perm.codename,
                    perm.name,
                    meta.modulo,
                    meta.get_nivel_riesgo_display(),  # ✅ CORREGIDO
                    '✓' if meta.es_personalizado else '✗',
                    '✓'
                ])
            else:
                data.append([
                    perm.id,
                    perm.codename,
                    perm.name,
                    perm.content_type.app_label,
                    '-',
                    '✗',
                    '✗'
                ])
        
        headers = [
            'ID', 'Codename', 'Nombre', 'Módulo', 
            'Riesgo', 'Personalizado', 'Metadata'
        ]
        
        self.stdout.write("\n" + "="*100)
        self.stdout.write(
            self.style.SUCCESS(
                f"\n📋 LISTADO DE PERMISOS (Total: {len(data)})\n"
            )
        )
        self.stdout.write(tabulate(data, headers=headers, tablefmt='grid'))
        self.stdout.write("="*100 + "\n")

    def show_metadata(self, options):
        """Muestra detalles de metadata de un permiso"""
        perm_id = options.get('permission_id')
        codename = options.get('codename')
        
        if not perm_id and not codename:
            self.stdout.write(
                self.style.ERROR(
                    "❌ Debes especificar --permission-id o --codename"
                )
            )
            return
        
        try:
            if perm_id:
                permission = Permission.objects.get(id=perm_id)
            else:
                permission = Permission.objects.get(codename=codename)
        except Permission.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("❌ Permiso no encontrado")
            )
            return
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🔍 DETALLE DEL PERMISO\n"
            )
        )
        self.stdout.write(f"ID: {permission.id}")
        self.stdout.write(f"Codename: {permission.codename}")
        self.stdout.write(f"Nombre: {permission.name}")
        self.stdout.write(f"App: {permission.content_type.app_label}")
        self.stdout.write(f"Modelo: {permission.content_type.model}")
        
        if hasattr(permission, 'metadata'):
            meta = permission.metadata
            self.stdout.write("\n" + self.style.SUCCESS("✓ TIENE METADATA:"))
            self.stdout.write(f"\nMódulo: {meta.modulo}")
            self.stdout.write(f"Categoría: {meta.get_categoria_display()}")  # ✅ CORREGIDO
            self.stdout.write(f"Nivel de Riesgo: {meta.get_nivel_riesgo_display()}")  # ✅ CORREGIDO
            self.stdout.write(f"Es Personalizado: {'Sí' if meta.es_personalizado else 'No'}")
            self.stdout.write(f"Visible en UI: {'Sí' if meta.visible_en_ui else 'No'}")
            self.stdout.write(f"\nDescripción:")
            self.stdout.write(f"  {meta.descripcion_detallada or '(sin descripción)'}")
            self.stdout.write(f"\nEjemplo de Uso:")
            self.stdout.write(f"  {meta.ejemplo_uso or '(sin ejemplo)'}")
        else:
            self.stdout.write(
                self.style.WARNING("\n✗ NO TIENE METADATA")
            )
        
        self.stdout.write("="*80 + "\n")

    def sync_all_metadata(self):
        """Sincroniza metadata para TODOS los permisos relevantes"""
        from roles.utils import get_permission_metadata
        
        self.stdout.write("\n🔄 Sincronizando metadata para todos los permisos...\n")
        
        permissions = Permission.objects.filter(
            content_type__app_label__in=[
                'clientes', 'divisas', 'transacciones',
                'medios_pago', 'users', 'auth'
            ]
        ).select_related('content_type')
        
        creados = 0
        actualizados = 0
        sin_cambios = 0
        
        for perm in permissions:
            # Obtener metadata (del helper o inferida)
            meta_info = get_permission_metadata(perm)
            
            if not meta_info:
                continue
            
            # Crear o actualizar metadata
            metadata, created = PermissionMetadata.objects.update_or_create(
                permission=perm,
                defaults={
                    'descripcion_detallada': meta_info['descripcion_detallada'],
                    'ejemplo_uso': meta_info['ejemplo_uso'],
                    'modulo': meta_info['modulo'],
                    'categoria': meta_info['categoria'],
                    'nivel_riesgo': meta_info['nivel_riesgo'],
                    'es_personalizado': meta_info['es_personalizado'],
                    'visible_en_ui': True,
                }
            )
            
            if created:
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Creado: {perm.codename}")
                )
            else:
                actualizados += 1
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Sincronización completa:\n"
                f"  Metadata creada: {creados}\n"
                f"  Metadata actualizada: {actualizados}\n"
                f"  Total procesados: {permissions.count()}"
            )
        )
        self.stdout.write("="*50 + "\n")

    def create_metadata(self, options):
        """Crea metadata manualmente para un permiso"""
        self.stdout.write(
            self.style.WARNING(
                "\n⚠️  Para crear metadata, es mejor usar 'sync' que "
                "automáticamente crea metadata inferida.\n"
            )
        )

    def update_metadata(self, options):
        """Actualiza metadata de un permiso"""
        self.stdout.write(
            self.style.WARNING(
                "\n⚠️  Para actualizar metadata, usa el comando 'sync_permissions --force-metadata'\n"
            )
        )

    def delete_metadata(self, options):
        """Elimina metadata de un permiso"""
        perm_id = options.get('permission_id')
        
        if not perm_id:
            self.stdout.write(
                self.style.ERROR(
                    "❌ Debes especificar --permission-id"
                )
            )
            return
        
        try:
            permission = Permission.objects.get(id=perm_id)
            if hasattr(permission, 'metadata'):
                permission.metadata.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Metadata eliminada para: {permission.name}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  El permiso no tiene metadata: {permission.name}"
                    )
                )
        except Permission.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("❌ Permiso no encontrado")
            )