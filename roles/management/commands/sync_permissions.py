"""
Comando para sincronizar permisos personalizados en Django.
VERSIÓN SIMPLIFICADA - Sin dependencia de PermissionMetadata.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# ✅ IMPORTAR DESDE CADA MÓDULO
from .permissions_defs.clientes import PERMISOS_CLIENTES
from .permissions_defs.divisas import PERMISOS_DIVISAS
from .permissions_defs.transacciones import PERMISOS_TRANSACCIONES
from .permissions_defs.medios_pago import PERMISOS_MEDIOS_PAGO
from .permissions_defs.usuarios import PERMISOS_USUARIOS

# ✅ COMBINAR TODOS LOS PERMISOS
TODOS_LOS_PERMISOS = (
    PERMISOS_CLIENTES +
    PERMISOS_DIVISAS +
    PERMISOS_TRANSACCIONES +
    PERMISOS_MEDIOS_PAGO +
    PERMISOS_USUARIOS
)


class Command(BaseCommand):
    help = 'Sincroniza permisos personalizados definidos en permissions_defs/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada de cada permiso',
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        
        self.stdout.write(self.style.WARNING('\n🔄 Iniciando sincronización de permisos personalizados...\n'))
        
        creados = 0
        actualizados = 0
        errores = 0
        sin_cambios = 0
        
        for permiso_def in TODOS_LOS_PERMISOS:
            try:
                # Obtener o crear ContentType
                content_type, ct_created = ContentType.objects.get_or_create(
                    app_label=permiso_def['app_label'],
                    model=permiso_def['model']
                )
                
                if ct_created and verbose:
                    self.stdout.write(
                        self.style.NOTICE(f'  ℹ️ ContentType creado: {permiso_def["app_label"]}.{permiso_def["model"]}')
                    )
                
                # Crear o actualizar Permission
                permission, created = Permission.objects.get_or_create(
                    codename=permiso_def['codename'],
                    content_type=content_type,
                    defaults={'name': permiso_def['name']}
                )
                
                # Si el permiso existía, verificar si el nombre cambió
                if not created:
                    if permission.name != permiso_def['name']:
                        permission.name = permiso_def['name']
                        permission.save()
                        actualizados += 1
                        if verbose:
                            self.stdout.write(
                                self.style.WARNING(f'  🔄 Actualizado: {permission.codename} → "{permission.name}"')
                            )
                    else:
                        sin_cambios += 1
                        if verbose:
                            self.stdout.write(f'  ✓ Sin cambios: {permission.codename}')
                else:
                    creados += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Creado: {permission.codename} ({permiso_def["modulo"]})'
                        )
                    )
                    
            except ContentType.DoesNotExist:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ❌ Error: Modelo {permiso_def["app_label"]}.{permiso_def["model"]} no existe en la BD'
                    )
                )
            except KeyError as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ❌ Error: Falta clave {e} en definición de permiso'
                    )
                )
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ❌ Error procesando {permiso_def.get("codename", "desconocido")}: {str(e)}'
                    )
                )
        
        # Resumen final
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ Sincronización completada:'))
        self.stdout.write(f'   🆕 Permisos creados:      {creados}')
        self.stdout.write(f'   🔄 Permisos actualizados: {actualizados}')
        self.stdout.write(f'   ✓ Sin cambios:            {sin_cambios}')
        
        if errores > 0:
            self.stdout.write(self.style.ERROR(f'   ❌ Errores:               {errores}'))
        
        total_procesados = creados + actualizados + sin_cambios + errores
        self.stdout.write(f'   📊 Total procesados:      {total_procesados}')
        self.stdout.write('='*60 + '\n')
        
        # Sugerencia para siguiente paso
        if creados > 0 or actualizados > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n💡 Siguiente paso: Asignar permisos a roles con:'
                )
            )
            self.stdout.write('   python manage.py setup_test_roles\n')