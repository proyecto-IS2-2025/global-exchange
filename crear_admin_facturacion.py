#!/usr/bin/env python3
"""
Crear usuario administrador para acceder al sistema de facturación
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casa_de_cambios.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

print("=" * 70)
print("CREAR USUARIO ADMINISTRADOR PARA FACTURACIÓN")
print("=" * 70)
print()

# Crear usuario administrador
username = 'admin_fact'
password = 'admin123'
email = 'admin@globalexchange.com'

if User.objects.filter(username=username).exists():
    print(f"⚠️  El usuario '{username}' ya existe")
    user = User.objects.get(username=username)
else:
    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        is_staff=True,
        is_superuser=False
    )
    print(f"✅ Usuario '{username}' creado exitosamente")

# Asignar al grupo administrador
try:
    grupo_admin = Group.objects.get(name='administrador')
    user.groups.add(grupo_admin)
    print(f"✅ Usuario asignado al grupo 'administrador'")
except Group.DoesNotExist:
    print("⚠️  Grupo 'administrador' no existe, pero el usuario tiene is_superuser=True")

print()
print("=" * 70)
print("CREDENCIALES PARA ACCEDER:")
print("=" * 70)
print(f"URL:        http://localhost:8000/facturacion/")
print(f"Usuario:    {username}")
print(f"Contraseña: {password}")
print("=" * 70)
