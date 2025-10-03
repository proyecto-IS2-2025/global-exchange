# roles/management/commands/sync_permissions.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from roles.models import PermissionMetadata
from .permissions_defs import TODOS_LOS_PERMISOS


class Command(BaseCommand):
    help = 'Sincroniza permisos personalizados y crea su metadata'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando sincronización de permisos...'))
        
        creados = 0
        actualizados = 0
        errores = 0
        
        for permiso_def in TODOS_LOS_PERMISOS:
            try:
                # Obtener ContentType
                content_type = ContentType.objects.get(
                    app_label=permiso_def['app_label'],
                    model=permiso_def['model']
                )
                
                # Crear o actualizar Permission
                permission, perm_created = Permission.objects.get_or_create(
                    codename=permiso_def['codename'],
                    content_type=content_type,
                    defaults={'name': permiso_def['name']}
                )
                
                # Si el permiso ya existía pero el nombre cambió, actualizarlo
                if not perm_created and permission.name != permiso_def['name']:
                    permission.name = permiso_def['name']
                    permission.save()
                
                # Crear o actualizar PermissionMetadata
                metadata, meta_created = PermissionMetadata.objects.update_or_create(
                    permission=permission,
                    defaults={
                        'modulo': permiso_def['modulo'],
                        'descripcion_detallada': permiso_def['descripcion'],
                        'ejemplo_uso': permiso_def.get('ejemplo', ''),
                        'nivel_riesgo': permiso_def.get('nivel_riesgo', 'medio'),
                        'orden': permiso_def.get('orden', 0),
                    }
                )
                
                if perm_created or meta_created:
                    creados += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Creado: {permission.name}')
                    )
                else:
                    actualizados += 1
                    self.stdout.write(f'  Actualizado: {permission.name}')
                    
            except ContentType.DoesNotExist:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error: Modelo {permiso_def["app_label"]}.{permiso_def["model"]} no existe'
                    )
                )
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error procesando {permiso_def.get("codename", "desconocido")}: {str(e)}')
                )
        
        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Sincronización completa: {creados} creados, {actualizados} actualizados'
            )
        )
        if errores > 0:
            self.stdout.write(self.style.ERROR(f'✗ {errores} errores'))