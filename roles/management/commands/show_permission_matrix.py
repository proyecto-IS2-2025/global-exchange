"""
Comando para visualizar la matriz de permisos asignados a cada rol.
"""
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Muestra la matriz de permisos por rol'

    def add_arguments(self, parser):
        parser.add_argument(
            '--role',
            type=str,
            help='Mostrar permisos solo de un rol específico',
        )
        parser.add_argument(
            '--export',
            action='store_true',
            help='Exportar a archivo CSV',
        )

    def handle(self, *args, **options):
        role_filter = options.get('role')
        export = options.get('export')

        # Obtener grupos
        if role_filter:
            try:
                groups = [Group.objects.get(name=role_filter)]
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ Rol "{role_filter}" no encontrado')
                )
                return
        else:
            groups = Group.objects.all().order_by('name')

        if not groups:
            self.stdout.write(
                self.style.WARNING('⚠ No hay roles configurados')
            )
            return

        # Agrupar permisos por módulo
        permission_matrix = self._build_matrix(groups)

        # Mostrar en consola
        self._display_matrix(permission_matrix, groups)

        # Exportar si se solicita
        if export:
            self._export_to_csv(permission_matrix, groups)

    def _build_matrix(self, groups):
        """Construye la matriz de permisos"""
        matrix = defaultdict(lambda: defaultdict(dict))

        for group in groups:
            perms = group.permissions.select_related('content_type').order_by(
                'content_type__app_label', 'codename'
            )

            for perm in perms:
                app_label = perm.content_type.app_label
                codename = perm.codename
                matrix[app_label][codename][group.name] = True

        return matrix

    def _display_matrix(self, matrix, groups):
        """Muestra la matriz en consola"""
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('=' * 80))
        self.stdout.write(self.style.HTTP_INFO('  MATRIZ DE PERMISOS POR ROL'))
        self.stdout.write(self.style.HTTP_INFO('=' * 80))
        self.stdout.write('')

        # Encabezados
        header = f"{'PERMISO':<50}"
        for group in groups:
            header += f"{group.name.upper():<15}"
        self.stdout.write(self.style.MIGRATE_HEADING(header))
        self.stdout.write(self.style.MIGRATE_HEADING('-' * 80))

        # Filas por módulo
        for app_label in sorted(matrix.keys()):
            self.stdout.write(self.style.WARNING(f'\n{app_label.upper()}:'))

            for codename in sorted(matrix[app_label].keys()):
                row = f"  {codename:<48}"

                for group in groups:
                    has_perm = matrix[app_label][codename].get(group.name, False)
                    symbol = '✓' if has_perm else '✗'
                    color = self.style.SUCCESS if has_perm else self.style.ERROR
                    row += f"{color(symbol):<15}"

                self.stdout.write(row)

        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('=' * 80))
        self.stdout.write('')

    def _export_to_csv(self, matrix, groups):
        """Exporta la matriz a CSV"""
        import csv
        from datetime import datetime

        filename = f'permission_matrix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Encabezados
            headers = ['Módulo', 'Permiso'] + [g.name for g in groups]
            writer.writerow(headers)

            # Datos
            for app_label in sorted(matrix.keys()):
                for codename in sorted(matrix[app_label].keys()):
                    row = [app_label, codename]

                    for group in groups:
                        has_perm = matrix[app_label][codename].get(group.name, False)
                        row.append('✓' if has_perm else '✗')

                    writer.writerow(row)

        self.stdout.write(
            self.style.SUCCESS(f'✓ Matriz exportada a: {filename}')
        )