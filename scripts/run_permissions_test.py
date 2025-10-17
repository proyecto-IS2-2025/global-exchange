#!/usr/bin/env python
"""
Script para ejecutar los tests de permisos con output colorido.
Ubicación: scripts/run_permission_tests.py

Uso:
    python scripts/run_permission_tests.py
    python scripts/run_permission_tests.py --test=1  # Solo test 1
    python scripts/run_permission_tests.py --verbose  # Con más detalle
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from django.core.management import call_command
from django.test.utils import get_runner
from django.conf import settings
import argparse


class Colors:
    """Colores ANSI para output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_banner():
    """Imprime banner inicial"""
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}{'='*70}")
    print("🧪 SUITE DE TESTS - SISTEMA DE PERMISOS")
    print(f"{'='*70}{Colors.ENDC}\n")


def print_test_info(test_num, description):
    """Imprime información de cada test"""
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}▶️  Test {test_num}: {description}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'─'*70}{Colors.ENDC}")


def run_single_test(test_class, verbose=False):
    """Ejecuta un test específico"""
    test_label = f'roles.tests.test_permissions_basic.{test_class}'
    
    verbosity = 2 if verbose else 1
    call_command('test', test_label, verbosity=verbosity, keepdb=True)


def run_all_tests(verbose=False):
    """Ejecuta todos los tests"""
    print_banner()
    
    tests = [
        ('PermissionsCreationTestCase', 'Creación de Permisos'),
        ('RolePermissionsTestCase', 'Asignación a Roles'),
        ('UserPermissionsTestCase', 'Herencia de Usuarios'),
        ('ContextProcessorTestCase', 'Context Processor'),
        ('DecoratorTestCase', 'Decorador @require_permission'),
    ]
    
    print(f"{Colors.WARNING}📋 Tests a ejecutar:{Colors.ENDC}")
    for idx, (_, desc) in enumerate(tests, 1):
        print(f"   {idx}. {desc}")
    
    print(f"\n{Colors.OKGREEN}🚀 Iniciando ejecución...{Colors.ENDC}\n")
    
    for idx, (test_class, desc) in enumerate(tests, 1):
        print_test_info(idx, desc)
        run_single_test(test_class, verbose)
    
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}{'='*70}")
    print("✅ TODOS LOS TESTS COMPLETADOS")
    print(f"{'='*70}{Colors.ENDC}\n")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Ejecuta tests del sistema de permisos'
    )
    parser.add_argument(
        '--test',
        type=int,
        choices=[1, 2, 3, 4, 5],
        help='Número del test a ejecutar (1-5)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Mostrar output detallado'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Ejecutar comandos de setup antes de los tests'
    )
    
    args = parser.parse_args()
    
    # Setup opcional
    if args.setup:
        print(f"\n{Colors.WARNING}🔧 Ejecutando comandos de setup...{Colors.ENDC}")
        call_command('sync_permissions', verbosity=0)
        call_command('setup_test_roles', verbosity=0)
        print(f"{Colors.OKGREEN}✅ Setup completado{Colors.ENDC}\n")
    
    # Ejecutar tests
    if args.test:
        tests = {
            1: ('PermissionsCreationTestCase', 'Creación de Permisos'),
            2: ('RolePermissionsTestCase', 'Asignación a Roles'),
            3: ('UserPermissionsTestCase', 'Herencia de Usuarios'),
            4: ('ContextProcessorTestCase', 'Context Processor'),
            5: ('DecoratorTestCase', 'Decorador @require_permission'),
        }
        
        test_class, desc = tests[args.test]
        print_banner()
        print_test_info(args.test, desc)
        run_single_test(test_class, args.verbose)
    else:
        run_all_tests(args.verbose)


if __name__ == '__main__':
    main()