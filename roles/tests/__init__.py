"""
Suite de tests para el módulo de roles y permisos.
"""
# Importar solo las clases de test que EXISTEN
from .test_permissions import (
    PermissionAssignmentTestCase,
    URLAccessControlTestCase,
    UserPermissionsTestCase,
    PermissionMatrixTestCase,
    EdgeCasesSecurityTestCase,
    ManagementCommandsTestCase,
    PermissionEnforcementTestCase,
)

__all__ = [
    'PermissionAssignmentTestCase',
    'URLAccessControlTestCase',
    'UserPermissionsTestCase',
    'PermissionMatrixTestCase',
    'EdgeCasesSecurityTestCase',
    'ManagementCommandsTestCase',
    'PermissionEnforcementTestCase',
]