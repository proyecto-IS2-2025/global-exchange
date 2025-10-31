# 🧪 INSTRUCCIONES PARA PROBAR EL SISTEMA DE FACTURACIÓN

**Fecha:** 30 de octubre de 2025  
**Sistema:** ✅ LEVANTADO Y FUNCIONANDO

---

## ✅ ESTADO ACTUAL DEL SISTEMA

### SQL Proxy (4 containers):
- ✅ `sql-proxy01-db-1` - PostgreSQL en puerto 45432
- ✅ `sql-proxy01-web-1` - API SIFEN
- ✅ `sql-proxy01-web-sched-1` - Scheduler (procesa cada 20s)
- ✅ `sql-proxy01-nginx-1` - Servidor de archivos PDF/XML (puerto 40080)

### Django:
- ✅ Servidor corriendo en `http://localhost:8000`
- ✅ Poetry virtualenv activo

---

## 📋 PASOS PARA PROBAR LA FACTURACIÓN

### 1️⃣ Acceder al sistema
```
URL: http://localhost:8000
```

### 2️⃣ Iniciar sesión
- Usuario: (tu usuario admin o de pruebas)
- Contraseña: (tu contraseña)

### 3️⃣ Realizar una compra de divisas

#### Opción A: Con interfaz web
```
1. Ir a: http://localhost:8000/operacion-divisas/comprar/
2. Seleccionar:
   - Divisa: USD (o la que tengas configurada)
   - Monto: 100 (o el monto que desees)
   - Medio de pago: Stripe o el que tengas activo
3. Completar el pago
4. Esperar confirmación
```

#### Opción B: Generar factura manualmente con script
```bash
cd /home/jose/proyecto_is2/global-exchange
poetry run python insertar_factura_directa.py
```

### 4️⃣ Ver la factura generada

Después de completar la compra, deberías ver:

```
✅ Factura generada: 001-003-XXXXXXX
⏳ Estado: Procesando en SIFEN
⏰ Tiempo estimado: 30-60 segundos
```

### 5️⃣ Verificar en la base de datos

```bash
# Ver última factura generada
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT id, dnumdoc, dpunexp, estado, estado_sifen, cdc 
   FROM public.de ORDER BY id DESC LIMIT 1;"

# Verificar que tiene pago insertado (CRÍTICO)
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT de_id, itipago, dmontipag 
   FROM public.gPaConEIni 
   WHERE de_id = (SELECT MAX(id) FROM de);"
```

### 6️⃣ Esperar aprobación de SIFEN

Durante los primeros 60 segundos verás:

```
🔵 Alerta azul: "Procesando en SIFEN"
⏱️ Mensaje: "Puede tomar 30-60 segundos"
🔄 Auto-refresh: Cada 15 segundos
⚠️ Botón PDF: Deshabilitado (amarillo) "PDF procesándose..."
```

### 7️⃣ Ver factura aprobada

Después de ~60 segundos:

```
✅ Estado: Aprobado
✅ CDC generado: 01025957333001003XXXXXXX...
✅ Botón PDF: Habilitado (verde)
✅ Botón XML: Habilitado (azul)
```

### 8️⃣ Descargar PDF

```
1. Click en "Descargar PDF"
2. Debería abrir/descargar: 001-003-XXXXXXX_YYYYMMDD_HHMMSS_RANDOM.pdf
3. Verificar que el PDF es oficial de SIFEN
```

### 9️⃣ Verificar archivos en el sistema

```bash
# Listar PDFs generados este mes
ls -lh /home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/$(date +%Y%m)/

# Abrir último PDF generado
xdg-open /home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/$(date +%Y%m)/*.pdf 2>/dev/null
```

---

## 🔍 VERIFICACIONES IMPORTANTES

### ✅ Checklist de validación:

- [ ] Factura se genera automáticamente después del pago
- [ ] Estado inicial: "Procesando" o "Confirmado"
- [ ] Alerta azul visible con mensaje de espera
- [ ] Auto-refresh funciona (página se recarga cada 15s)
- [ ] Botón PDF deshabilitado mientras procesa
- [ ] Después de ~60s: Estado cambia a "Aprobado"
- [ ] CDC se genera correctamente
- [ ] Botón PDF se habilita (verde)
- [ ] Click en PDF descarga archivo correcto
- [ ] PDF tiene formato oficial de SIFEN
- [ ] Punto de expedición es '003' (no '001')
- [ ] Tiene entrada en tabla gPaConEIni (pago)
- [ ] URL incluye subdirectorio /YYYYMM/
- [ ] Nombre de archivo incluye timestamp

---

## 🐛 SI ALGO FALLA

### Problema: Factura no se genera
```bash
# Ver logs de Django
tail -f /tmp/django.log

# Ver logs del scheduler
docker logs sql-proxy01-web-sched-1 --tail 50 -f
```

### Problema: Estado se queda en "Procesando" más de 2 minutos
```bash
# Ver logs del scheduler
docker logs sql-proxy01-web-sched-1 --tail 100

# Verificar estado en BD
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT dnumdoc, estado, estado_sifen, descripcion_sifen 
   FROM public.de ORDER BY id DESC LIMIT 1;"
```

### Problema: Error "list index out of range"
```bash
# Verificar si falta pago en gPaConEIni
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT d.id, d.dnumdoc, g.de_id as tiene_pago 
   FROM public.de d 
   LEFT JOIN public.gPaConEIni g ON d.id = g.de_id 
   ORDER BY d.id DESC LIMIT 5;"
```

### Problema: Error de permisos (El operador ESI no tiene permiso...)
```bash
# Este error YA ESTÁ RESUELTO
# Era porque punto_expedicion era '001' en vez de '003'
# Verificar configuración actual:
grep -n "punto_expedicion" /home/jose/proyecto_is2/global-exchange/facturacion_electronica/config.py
```

### Problema: PDF no descarga
```bash
# Verificar que existe el archivo
ls -lh /home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/$(date +%Y%m)/

# Verificar que nginx está corriendo
docker ps | grep nginx

# Verificar URL en base de datos
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT dnumdoc, url_kude_pdf FROM public.de ORDER BY id DESC LIMIT 1;" 2>/dev/null || echo "Usar Django admin"
```

---

## 📊 COMANDOS ÚTILES

### Ver todas las facturas generadas hoy:
```bash
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT id, dnumdoc, dpunexp, estado, estado_sifen 
   FROM public.de 
   WHERE fch_ins::date = CURRENT_DATE 
   ORDER BY id DESC;"
```

### Ver logs en tiempo real:
```bash
# Django
tail -f /tmp/django.log

# Scheduler (procesamiento de facturas)
docker logs sql-proxy01-web-sched-1 -f

# Nginx (descargas de PDF/XML)
docker logs sql-proxy01-nginx-1 -f
```

### Reiniciar solo el scheduler:
```bash
docker restart sql-proxy01-web-sched-1
```

### Detener sistema:
```bash
# Detener Django
pkill -f "manage.py runserver"

# Detener SQL Proxy
cd /home/jose/proyecto_is2/sql-proxy01
docker compose -f docker-compose.test.yml down
```

---

## ✅ RESULTADO ESPERADO

Al final de una prueba exitosa deberías tener:

```
✅ Factura número: 001-003-00000XX
✅ Estado: Aprobado
✅ Estado SIFEN: Aprobado
✅ CDC: 01025957333001003XXXXXXXXXXXXXXXX (44 dígitos)
✅ PDF descargado: 001-003-00000XX_YYYYMMDD_HHMMSS_RANDOM.pdf
✅ Tamaño PDF: ~70-80 KB
✅ XML generado: 001-003-00000XX_YYYYMMDD_HHMMSS_RANDOM.xml
✅ Tamaño XML: ~7-8 KB
```

---

## 🎯 URLs IMPORTANTES

- **Django Admin:** http://localhost:8000/admin/
- **Lista de facturas:** http://localhost:8000/facturacion/lista/
- **Comprar divisas:** http://localhost:8000/operacion-divisas/comprar/
- **Ver PDFs directamente:** http://localhost:40080/kude/YYYYMM/

---

## 📝 NOTAS FINALES

1. **Primera factura puede tardar más:** El scheduler toma 20 segundos entre ejecuciones
2. **Auto-refresh es cada 15s:** Puedes hacer click manual en "Actualizar Estado"
3. **PDF no existe hasta aprobación:** SIFEN genera el archivo cuando aprueba
4. **Nombre de archivo tiene timestamp:** No se puede predecir antes de la aprobación
5. **Punto '003' es CRÍTICO:** No cambiar a '001' o dará error de permisos

---

**¡Sistema listo para pruebas! 🚀**
