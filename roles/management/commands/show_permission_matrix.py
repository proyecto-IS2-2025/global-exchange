"""
Comando para mostrar una matriz de permisos por rol/grupo.
Versión mejorada con opción de exportar a archivo UTF-8.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
import sys


class Command(BaseCommand):
    help = 'Muestra una matriz de permisos asignados a cada rol/grupo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Filtrar permisos por app_label específica (ej: clientes, divisas)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Guardar salida en archivo (ej: matriz.txt)',
        )
        parser.add_argument(
            '--unicode',
            action='store_true',
            help='Usar caracteres Unicode (puede fallar en Windows CMD)',
        )

    def handle(self, *args, **options):
        app_filter = options.get('app')
        output_file = options.get('output')
        use_unicode = options.get('unicode', False)
        
        # Detectar si estamos en Windows
        is_windows = sys.platform.startswith('win')
        
        # Si estamos en Windows y no se especificó --unicode, usar ASCII
        if is_windows and not use_unicode:
            self.CHECK = 'SI'
            self.CROSS = 'NO'
        else:
            self.CHECK = '✓'
            self.CROSS = '✗'
        
        # Si hay archivo de salida, redirigir stdout
        if output_file:
            output_handle = open(output_file, 'w', encoding='utf-8')
            self.stdout._out = output_handle
        
        try:
            # Encabezado
            self.stdout.write('=' * 80)
            self.stdout.write('  MATRIZ DE PERMISOS POR ROL')
            self.stdout.write('=' * 80)
            self.stdout.write('')
            
            # Obtener todos los grupos
            groups = Group.objects.all().order_by('name')
            
            if not groups.exists():
                self.stdout.write(self.style.WARNING('No hay grupos/roles configurados en el sistema.'))
                return
            
            # Obtener todos los permisos
            if app_filter:
                permissions = Permission.objects.filter(
                    content_type__app_label=app_filter
                ).select_related('content_type').order_by('content_type__app_label', 'codename')
            else:
                permissions = Permission.objects.all().select_related('content_type').order_by(
                    'content_type__app_label', 'codename'
                )
            
            # Construir matriz
            permission_matrix = {}
            for perm in permissions:
                app_label = perm.content_type.app_label
                if app_label not in permission_matrix:
                    permission_matrix[app_label] = []
                
                perm_data = {
                    'codename': perm.codename,
                    'name': perm.name,
                    'groups': {}
                }
                
                # Verificar qué grupos tienen este permiso
                for group in groups:
                    perm_data['groups'][group.name] = group.permissions.filter(id=perm.id).exists()
                
                permission_matrix[app_label].append(perm_data)
            
            # Mostrar matriz
            self._display_matrix(permission_matrix, groups)
            
            self.stdout.write('')
            self.stdout.write('=' * 80)
            
            if output_file:
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS(f'Matriz exportada a: {output_file}'))
        
        finally:
            if output_file:
                output_handle.close()

    def _display_matrix(self, permission_matrix, groups):
        """
        Muestra la matriz de permisos en formato tabla.
        """
        # Encabezado de columnas
        header_parts = ['PERMISO'.ljust(45)]
        for group in groups:
            header_parts.append(group.name.upper().ljust(15))
        
        header = '  '.join(header_parts)
        self.stdout.write(header)
        self.stdout.write('-' * 80)
        
        # Filas de permisos por app
        for app_label in sorted(permission_matrix.keys()):
            # Título de la app
            self.stdout.write('')
            self.stdout.write(f"{app_label.upper()}:")
            
            perms = permission_matrix[app_label]
            for perm_data in perms:
                row_parts = [f"  {perm_data['codename']}".ljust(45)]
                
                for group in groups:
                    has_perm = perm_data['groups'].get(group.name, False)
                    symbol = self.CHECK if has_perm else self.CROSS
                    row_parts.append(symbol.ljust(15))
                
                row = '  '.join(row_parts)
                self.stdout.write(row)