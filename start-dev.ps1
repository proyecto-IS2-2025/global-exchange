# Script para iniciar el entorno completo de Global Exchange con Notificaciones
# Autor: Sistema de Notificaciones
# Descripción: Inicia Redis, Celery Worker, Celery Beat y Django en terminales separadas

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Global Exchange - Entorno de Desarrollo" -ForegroundColor Cyan
Write-Host "  con Notificaciones Periódicas" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que Docker Desktop está corriendo
Write-Host "Verificando Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✓ Docker está corriendo" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker no está corriendo. Por favor, inicia Docker Desktop." -ForegroundColor Red
    Write-Host "  Descarga: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Limpiar contenedor Redis existente si existe
Write-Host "Limpiando contenedor Redis anterior..." -ForegroundColor Yellow
docker stop redis-global-exchange 2>$null
docker rm redis-global-exchange 2>$null

# Iniciar Redis
Write-Host "Iniciando Redis..." -ForegroundColor Yellow
docker run -d -p 6379:6379 --name redis-global-exchange redis:alpine
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Redis iniciado correctamente" -ForegroundColor Green
} else {
    Write-Host "✗ Error al iniciar Redis" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

Start-Sleep -Seconds 2

# Obtener la ruta del proyecto
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Iniciando servicios..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Función para iniciar un proceso en una nueva ventana de PowerShell
function Start-ServiceWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$Color
    )
    
    Write-Host "► Iniciando: $Title" -ForegroundColor $Color
    
    $psCommand = @"
Set-Location '$projectPath'
`$host.UI.RawUI.WindowTitle = '$Title - Global Exchange'
Write-Host '============================================' -ForegroundColor $Color
Write-Host '  $Title' -ForegroundColor $Color
Write-Host '============================================' -ForegroundColor $Color
Write-Host ''
Write-Host 'Activando entorno virtual...' -ForegroundColor Yellow
& '.\venv\Scripts\Activate.ps1'
Write-Host 'Ejecutando: $Command' -ForegroundColor Yellow
Write-Host ''
Invoke-Expression '$Command'
Write-Host ''
Write-Host 'Presiona Enter para cerrar esta ventana...' -ForegroundColor Red
Read-Host
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $psCommand
    Start-Sleep -Seconds 1
}

# Iniciar Celery Worker
Start-ServiceWindow -Title "Celery Worker" -Command "celery -A casa_de_cambios worker --loglevel=info -P solo" -Color "Magenta"

Start-Sleep -Seconds 3

# Iniciar Celery Beat
Start-ServiceWindow -Title "Celery Beat" -Command "celery -A casa_de_cambios beat --loglevel=info" -Color "Cyan"

Start-Sleep -Seconds 2

# Iniciar Django
Start-ServiceWindow -Title "Django Server" -Command "python manage.py runserver" -Color "Green"

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  ✓ Todos los servicios iniciados" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Servicios corriendo:" -ForegroundColor Yellow
Write-Host "  1. Redis          -> localhost:6379" -ForegroundColor White
Write-Host "  2. Celery Worker  -> Procesando tareas" -ForegroundColor White
Write-Host "  3. Celery Beat    -> Programando tareas cada 5 min" -ForegroundColor White
Write-Host "  4. Django Server  -> http://127.0.0.1:8000" -ForegroundColor White
Write-Host ""
Write-Host "Accede a tu aplicación en: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para detener todos los servicios:" -ForegroundColor Yellow
Write-Host "  1. Cierra las 3 ventanas de PowerShell que se abrieron" -ForegroundColor White
Write-Host "  2. Ejecuta: docker stop redis-global-exchange" -ForegroundColor White
Write-Host ""
Write-Host "Presiona Enter para salir (los servicios seguirán corriendo)..." -ForegroundColor Gray
Read-Host
