"""
Comando para crear RoleStatus faltantes.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from roles.models import RoleStatus


class Command(BaseCommand):
    help = 'Crea RoleStatus para grupos que no lo tienen'

    def handle(self, *args, **options):
        groups = Group.objects.all()
        
        created = 0
        for group in groups:
            status, was_created = RoleStatus.objects.get_or_create(
                group=group,
                defaults={'is_active': True}
            )
            
            if was_created:
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Creado RoleStatus para: {group.name}")
                )
            else:
                estado = "activo" if status.is_active else "inactivo"
                self.stdout.write(
                    self.style.WARNING(f"○ Ya existe ({estado}): {group.name}")
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Total creados: {created}\n"
                f"✅ Total existentes: {groups.count()}"
            )
        )