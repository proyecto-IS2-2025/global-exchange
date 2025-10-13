# Script para iniciar Redis 5.0.14
Write-Host "Iniciando Redis Server 5.0.14..." -ForegroundColor Cyan

# Verificar si Redis ya esta corriendo
$redisProcess = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue

if ($redisProcess) {
    Write-Host "[OK] Redis ya esta corriendo (PID: $($redisProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "Iniciando Redis..." -ForegroundColor Yellow
    Start-Process -FilePath ".\redis-server\redis-server.exe" -ArgumentList ".\redis-server\redis.windows.conf" -WindowStyle Normal
    Start-Sleep -Seconds 2
    
    $redisProcess = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
    if ($redisProcess) {
        Write-Host "[OK] Redis iniciado correctamente (PID: $($redisProcess.Id))" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Error al iniciar Redis" -ForegroundColor Red
        exit 1
    }
}

# Probar conexion
Write-Host "Probando conexion..." -ForegroundColor Yellow
$response = .\redis-server\redis-cli.exe ping
if ($response -eq "PONG") {
    Write-Host "[OK] Redis responde correctamente: $response" -ForegroundColor Green
    
    # Mostrar version
    $version = .\redis-server\redis-cli.exe INFO server | Select-String "redis_version"
    Write-Host "[INFO] $version" -ForegroundColor Cyan
} else {
    Write-Host "[ERROR] Redis no responde" -ForegroundColor Red
}
