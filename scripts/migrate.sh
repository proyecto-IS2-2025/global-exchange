#!/bin/bash
echo "Aplicando migraciones..."
python manage.py makemigrations
python manage.py migrate
echo "Migraciones completadas."