#!/bin/sh

# Ejecuta las migraciones de la base de datos
python manage.py migrate --noinput

# Inicia Gunicorn
exec gunicorn --bind 0.0.0.0:8000 casa_de_cambios.wsgi:application