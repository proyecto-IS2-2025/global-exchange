#!/bin/bash
echo "Preparando el entorno..."
./migrate.sh

echo "Iniciando el servidor de desarrollo..."
python manage.py runserver 127.0.0.1:8000