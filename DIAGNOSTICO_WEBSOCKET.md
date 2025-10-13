# 🔍 Guía de Diagnóstico - Notificaciones en Tiempo Real

## ❌ Problema Actual

Las notificaciones se crean correctamente en la base de datos, pero **no llegan en tiempo real** al navegador. Necesitas recargar la página para verlas.

## 🎯 Causas Posibles

### 1. WebSocket No Conectado
El navegador no está conectado al WebSocket, por lo que no puede recibir notificaciones en tiempo real.

**Verificación:**
- Abre la consola del navegador (F12)
- Busca mensajes como:
  - ✅ `"WebSocket conectado"` o `"Conectado al sistema de notificaciones"`
  - ❌ `"WebSocket connection failed"` o errores de conexión

### 2. Redis BZPOPMIN Todavía Activo
Aunque actualizamos Redis a 5.0.14, puede que el error persista si:
- El navegador tiene la conexión antigua cacheada
- Django no reinició correctamente

**Verificación en logs de Django:**
```
Exception inside application: unknown command 'BZPOPMIN'
```

### 3. Channel Layer No Configurado
Django Channels no puede comunicarse con Redis.

## ✅ Soluciones

### Solución 1: Verificar WebSocket en el Navegador

1. **Abre la consola del navegador** (F12)
2. **Ve a la pestaña Console**
3. **Recarga la página** (F5)
4. **Busca estos mensajes:**

```javascript
// ✅ CORRECTO - Deberías ver:
WebSocket conectado
✓ Conectado al sistema de notificaciones en tiempo real
Notificaciones pendientes: X

// ❌ ERROR - Si ves:
WebSocket connection to 'ws://127.0.0.1:8000/ws/notificaciones/' failed
Error al conectar WebSocket: ...
```

### Solución 2: Forzar Reconexión del WebSocket

**En la consola del navegador, ejecuta:**

```javascript
// Cerrar conexión actual si existe
if (window.notifSocket) {
    window.notifSocket.close();
}

// Reconectar
window.location.reload();
```

### Solución 3: Verificar Logs de Django

**Mira la terminal de Django y busca:**

```
✅ CORRECTO:
WebSocket HANDSHAKING /ws/notificaciones/ [127.0.0.1:xxxxx]
WebSocket CONNECT /ws/notificaciones/ [127.0.0.1:xxxxx]
✓ Usuario user1 conectado a notificaciones WebSocket

❌ ERROR:
Exception inside application: unknown command 'BZPOPMIN'
WebSocket DISCONNECT /ws/notificaciones/ [127.0.0.1:xxxxx]
```

### Solución 4: Reiniciar Todo el Sistema

Si nada funciona, reinicia todos los servicios:

1. **Detener todo:**
   ```powershell
   # Detener Redis
   Get-Process redis-server | Stop-Process -Force
   
   # Detener Python (Django, Celery)
   Get-Process python | Stop-Process -Force
   ```

2. **Iniciar de nuevo:**
   ```powershell
   # Terminal 1: Redis
   .\start_redis.ps1
   
   # Terminal 2: Django
   make run
   
   # Terminal 3: Celery Worker
   .\start_celery_worker.ps1
   
   # Terminal 4: Celery Beat
   .\start_celery_beat.ps1
   ```

3. **En el navegador:**
   - Cierra todas las pestañas de localhost:8000
   - Abre una nueva pestaña
   - Ve a http://127.0.0.1:8000
   - Inicia sesión
   - Abre F12 y verifica la consola

### Solución 5: Verificar Configuración de Redis

**Verifica que Redis 5.0.14 está corriendo:**

```powershell
.\redis-server\redis-cli.exe INFO server | Select-String "redis_version"
```

**Debe responder:** `redis_version:5.0.14.1`

## 🧪 Prueba Manual

Para verificar que el sistema funciona:

1. **Configura una notificación para dentro de 2 minutos:**
   - Ve a `/notificaciones/`
   - Nueva Alerta → Reporte Periódico
   - Diaria, Hora: (hora actual + 2 minutos)
   - Guarda

2. **Mantén la página abierta (NO recargues)**

3. **Espera los 2 minutos**

4. **Deberías ver:**
   - ✅ Toast notification aparece automáticamente
   - ✅ Contador de notificaciones se actualiza
   - ✅ En la consola: mensaje del WebSocket

5. **Si NO ves el toast:**
   - ❌ El WebSocket no está funcionando
   - Sigue las soluciones anteriores

## 📋 Checklist de Verificación

- [ ] Redis 5.0.14 está corriendo
- [ ] Django está corriendo
- [ ] Celery Worker está corriendo
- [ ] Celery Beat está corriendo
- [ ] En la consola del navegador aparece "WebSocket conectado"
- [ ] En logs de Django aparece "Usuario conectado a notificaciones WebSocket"
- [ ] NO hay errores "BZPOPMIN" en los logs
- [ ] NO hay errores "WebSocket failed" en la consola del navegador

## 🎯 Próximos Pasos

1. **Primero:** Verifica la consola del navegador (F12)
2. **Segundo:** Verifica los logs de Django
3. **Tercero:** Si hay errores BZPOPMIN, reinicia Django
4. **Cuarto:** Prueba con una notificación de prueba

---

**Recuerda:** Las notificaciones **SÍ se están creando** (por eso las ves al recargar). El único problema es la **entrega en tiempo real** vía WebSocket.
