from collections import defaultdict
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission

from roles.models import PermissionMetadata


class Command(BaseCommand):
    help = "Muestra una matriz de permisos con su metadata organizada por módulo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--module",
            dest="module",
            help="Filtra la salida a un módulo específico (usar el valor interno, p. ej. 'clientes').",
        )
        parser.add_argument(
            "--app",
            dest="app",
            help="Filtra por etiqueta de aplicación (app_label) del permiso.",
        )
        parser.add_argument(
            "--csv",
            action="store_true",
            dest="csv",
            help="Exporta la matriz en formato CSV.",
        )

    def handle(self, *args, **options):
        qs = (
            Permission.objects.select_related("metadata", "content_type")
            .filter(metadata__isnull=False)
            .order_by("metadata__modulo", "metadata__orden", "codename")
        )

        module_filter = options.get("module")
        if module_filter:
            qs = qs.filter(metadata__modulo=module_filter)

        app_filter = options.get("app")
        if app_filter:
            qs = qs.filter(content_type__app_label=app_filter)

        if not qs.exists():
            self.stdout.write(self.style.WARNING("No se encontraron permisos con metadata."))
            return

        rows = []
        for perm in qs:
            metadata: PermissionMetadata = perm.metadata
            rows.append(
                {
                    "modulo": metadata.modulo,
                    "modulo_display": metadata.get_modulo_display(),
                    "app": perm.content_type.app_label,
                    "modelo": perm.content_type.model,
                    "codename": perm.codename,
                    "nombre": perm.name,
                    "riesgo": metadata.get_nivel_riesgo_display() if metadata.nivel_riesgo else "",
                    "orden": metadata.orden or "",
                }
            )

        if options.get("csv"):
            self._print_csv(rows)
        else:
            self._print_table(rows)

        summary = defaultdict(int)
        for row in rows:
            summary[row["modulo_display"]] += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Resumen por módulo:"))
        for modulo, count in summary.items():
            self.stdout.write(f"  • {modulo}: {count} permisos")
        self.stdout.write(f"\nTotal de permisos listados: {len(rows)}")

    def _print_csv(self, rows):
        header = [
            "modulo",
            "modulo_display",
            "app",
            "modelo",
            "codename",
            "nombre",
            "riesgo",
            "orden",
        ]
        self.stdout.write(",".join(header))
        for row in rows:
            values = [str(row[field]).replace(",", r"\,") for field in header]
            self.stdout.write(",".join(values))

    def _print_table(self, rows):
        header = ["Módulo", "App", "Modelo", "Codename", "Nombre", "Riesgo", "Orden"]
        data = [
            [
                row["modulo_display"],
                row["app"],
                row["modelo"],
                row["codename"],
                row["nombre"],
                row["riesgo"],
                row["orden"],
            ]
            for row in rows
        ]

        widths = [len(col) for col in header]
        for record in data:
            for idx, value in enumerate(record):
                widths[idx] = max(widths[idx], len(str(value)))

        line = "+".join("-" * (w + 2) for w in widths)
        fmt = " | ".join("{:<" + str(w) + "}" for w in widths)

        self.stdout.write(line.replace("-", "+"))
        self.stdout.write(fmt.format(*header))
        self.stdout.write(line.replace("-", "+"))
        for record in data:
            self.stdout.write(fmt.format(*record))
        self.stdout.write(line.replace("-", "+"))