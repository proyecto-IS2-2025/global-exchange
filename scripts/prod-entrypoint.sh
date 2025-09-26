#!/bin/sh

# Espera a que la base de datos esté disponible
/app/scripts/wait-for-it.sh db:5432 --timeout=30 --strict -- \

# Ejecuta las migraciones de la base de datos
poetry run python manage.py migrate --noinput

# Inicia Gunicorn
exec poetry run gunicorn --bind 0.0.0.0:8000 casa_de_cambios.wsgi:application