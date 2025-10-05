@echo off
REM filepath: c:\proyecto-is2\casa_de_cambios\setup_system.bat

echo ============================================================
echo   SISTEMA DE GESTION DE PERMISOS - INICIALIZACION
echo ============================================================
echo.

REM PASO 1: Aplicar migraciones
echo [PASO 1] Aplicando migraciones de base de datos...
python manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo en migraciones
    pause
    exit /b 1
)
echo OK: Migraciones aplicadas
echo.

REM PASO 2: Sincronizar permisos personalizados
echo [PASO 2] Sincronizando permisos personalizados...
python manage.py sync_permissions
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo en sincronizacion
    pause
    exit /b 1
)
echo OK: Permisos sincronizados
echo.

REM PASO 3: Cargar fixtures de roles
echo [PASO 3] Cargando roles desde fixtures...
python manage.py loaddata roles/fixtures/roles_data.json
if %ERRORLEVEL% NEQ 0 (
    echo ADVERTENCIA: Error al cargar roles ^(puede que ya existan^)
)
echo.

REM PASO 4: Cargar fixtures de usuarios
echo [PASO 4] Cargando usuarios de prueba desde fixtures...
python manage.py loaddata users/fixtures/users_data.json
if %ERRORLEVEL% NEQ 0 (
    echo ADVERTENCIA: Error al cargar usuarios ^(puede que ya existan^)
)
echo.

REM PASO 5: Asignar permisos a roles
echo [PASO 5] Asignando permisos a roles...
python manage.py setup_test_roles
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al asignar permisos
    pause
    exit /b 1
)
echo OK: Permisos asignados
echo.

REM PASO 6: Mostrar matriz de permisos
echo [PASO 6] Generando matriz de permisos...
python manage.py show_permission_matrix
echo.

REM PASO 7: Resumen final
echo ============================================================
echo              CONFIGURACION COMPLETADA
echo ============================================================
echo.
echo CREDENCIALES DE ACCESO:
echo ------------------------------------------------------------
echo.
echo ADMIN:
echo    Usuario: admin / test_admin
echo    Email: admin@gmail.com / test_admin@test.com
echo    Contraseña: admin123
echo.
echo OPERADOR:
echo    Usuario: test_operador
echo    Email: test_operador@test.com
echo    Contraseña: admin123
echo.
echo CLIENTE:
echo    Usuario: test_cliente
echo    Email: test_cliente@test.com
echo    Contraseña: admin123
echo.
echo ------------------------------------------------------------
echo.
echo Servidor listo. Ejecute:
echo    python manage.py runserver
echo.
pause