# Script para iniciar Celery Worker
Write-Host "Iniciando Celery Worker..." -ForegroundColor Cyan
poetry run celery -A casa_de_cambios worker --loglevel=info --pool=solo
