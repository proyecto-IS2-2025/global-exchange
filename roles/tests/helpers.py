"""
Helpers para tests de permisos.
"""
from io import StringIO
import sys
from django.core.management import call_command
from django.contrib.auth.models import Group


def setup_permissions_silently():
    """
    ✅ Configura permisos y roles SIN output en terminal.
    """
    # Silenciar output
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    
    try:
        # Sincronizar permisos
        call_command('sync_permissions', verbosity=0)
        
        # Crear TODOS los grupos
        grupos = ['dev', 'administrador', 'operador', 'cliente', 'usuario_registrado', 'observador']
        for grupo_nombre in grupos:
            Group.objects.get_or_create(name=grupo_nombre)
        
        # Asignar permisos a roles
        call_command('setup_test_roles', verbosity=0)
        
    finally:
        # Restaurar stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr