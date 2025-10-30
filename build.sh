#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Recolectar archivos estáticos
python manage.py collectstatic --no-input

# Ejecutar migraciones
python manage.py migrate

# Sincronizar permisos personalizados
python manage.py sync_permissions

# Configurar permisos de roles (opcional, comentar si ya se ejecutó)
# python manage.py setup_test_roles
