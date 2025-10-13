# Script para iniciar el sistema de notificaciones periódicas
# Abre 3 ventanas: Django Server, Celery Worker y Celery Beat

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 INICIANDO SISTEMA DE NOTIFICACIONES" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Obtener la ruta actual
$projectPath = $PSScriptRoot

# Verificar Redis
Write-Host "📡 Verificando Redis (Memurai)..." -ForegroundColor Yellow
try {
    $redisStatus = Get-Service Memurai -ErrorAction SilentlyContinue
    if ($null -eq $redisStatus) {
        Write-Host "⚠️  Memurai no está instalado" -ForegroundColor Red
        Write-Host "   Descarga desde: https://www.memurai.com/get-memurai" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Presiona Enter para continuar de todas formas"
    } elseif ($redisStatus.Status -ne "Running") {
        Write-Host "⚠️  Redis no está corriendo. Intentando iniciar..." -ForegroundColor Yellow
        Start-Service Memurai
        Start-Sleep -Seconds 2
        Write-Host "✅ Redis iniciado" -ForegroundColor Green
    } else {
        Write-Host "✅ Redis está corriendo" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  No se pudo verificar Redis: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Iniciar Django Server
Write-Host "🌐 Iniciando Django Development Server..." -ForegroundColor Yellow
$djangoWindow = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectPath'; Write-Host '🌐 DJANGO SERVER' -ForegroundColor Cyan; .\venv\Scripts\Activate.ps1; python manage.py runserver"
) -PassThru

Start-Sleep -Seconds 3
Write-Host "✅ Django Server iniciado (PID: $($djangoWindow.Id))" -ForegroundColor Green
Write-Host ""

# Iniciar Celery Worker
Write-Host "⚙️  Iniciando Celery Worker..." -ForegroundColor Yellow
$workerWindow = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectPath'; Write-Host '⚙️  CELERY WORKER' -ForegroundColor Cyan; .\venv\Scripts\Activate.ps1; celery -A casa_de_cambios worker --loglevel=info --pool=solo"
) -PassThru

Start-Sleep -Seconds 3
Write-Host "✅ Celery Worker iniciado (PID: $($workerWindow.Id))" -ForegroundColor Green
Write-Host ""

# Iniciar Celery Beat
Write-Host "⏰ Iniciando Celery Beat Scheduler..." -ForegroundColor Yellow
$beatWindow = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectPath'; Write-Host '⏰ CELERY BEAT' -ForegroundColor Cyan; .\venv\Scripts\Activate.ps1; celery -A casa_de_cambios beat --loglevel=info"
) -PassThru

Start-Sleep -Seconds 2
Write-Host "✅ Celery Beat iniciado (PID: $($beatWindow.Id))" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ SISTEMA INICIADO CORRECTAMENTE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Información:" -ForegroundColor Cyan
Write-Host "   • Django Server:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   • WebSocket:      ws://127.0.0.1:8000/ws/notificaciones/" -ForegroundColor White
Write-Host "   • Redis:          localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Monitoreo:" -ForegroundColor Cyan
Write-Host "   • Django PID:     $($djangoWindow.Id)" -ForegroundColor White
Write-Host "   • Worker PID:     $($workerWindow.Id)" -ForegroundColor White
Write-Host "   • Beat PID:       $($beatWindow.Id)" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Para detener todos los procesos, cierra esta ventana" -ForegroundColor Yellow
Write-Host "   o ejecuta: taskkill /PID $($djangoWindow.Id) /PID $($workerWindow.Id) /PID $($beatWindow.Id) /F" -ForegroundColor Yellow
Write-Host ""

# Mantener esta ventana abierta
Read-Host "Presiona Enter para cerrar esta ventana (los servicios seguirán corriendo)"
