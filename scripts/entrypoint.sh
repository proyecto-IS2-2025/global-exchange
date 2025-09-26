#!/bin/sh
# Espera a que la base de datos esté lista
# El host es el nombre del servicio de la base de datos en docker-compose.yml
# En este caso, 'db'
/app/scripts/wait-for-it.sh db:5432 --timeout=30

python manage.py makemigrations --noinput
# Aplica las migraciones de Django
python manage.py migrate --noinput

# Arranca el servidor de desarrollo
python manage.py runserver 0.0.0.0:8000