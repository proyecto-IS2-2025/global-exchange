# Script para iniciar Celery Beat
Write-Host "Iniciando Celery Beat..." -ForegroundColor Cyan
poetry run celery -A casa_de_cambios beat --loglevel=info
