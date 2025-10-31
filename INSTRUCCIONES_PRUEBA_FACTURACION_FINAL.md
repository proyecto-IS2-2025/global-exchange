# 🧪 INSTRUCCIONES DE PRUEBA - SISTEMA DE FACTURACIÓN AUTOMÁTICA

**Sistema:** Facturación Electrónica integrado con SIFEN (Paraguay)  
**Estado:** ✅ Configurado y funcionando  
**Última actualización:** 30 de octubre de 2025

---

## ✅ CAMBIOS IMPLEMENTADOS - RESUMEN

### Backend (`services.py`):
1. ✅ **Inserción de pago obligatoria** - gPaConEIni tabla
2. ✅ **URLs corregidas** - Incluye subdirectorio `/YYYYMM/`
3. ✅ **Nueva función** `actualizar_estado_factura()` - Busca PDF real con glob
4. ✅ **Punto de expedición** - Corregido a '003'

### Views (`views.py`):
1. ✅ Función `actualizar_estado()` actualizada

### Frontend (`detalle_factura.html`):
1. ✅ **Alerta de procesamiento** - Mensaje de espera con timer
2. ✅ **Botón deshabilitado** - Durante procesamiento SIFEN
3. ✅ **Auto-refresh** - Cada 15 segundos si está procesando

---

## 🚀 FLUJO DE PRUEBA END-TO-END

### Paso 1: Levantar el sistema

```bash
cd /home/jose/proyecto_is2/global-exchange
./levantar_sistema.sh
```

**Verificar:**
- ✅ Django corriendo en `http://localhost:8000`
- ✅ SQL Proxy corriendo (4 contenedores)
- ✅ Redis corriendo

---

### Paso 2: Verificar contenedores SQL Proxy

```bash
cd /home/jose/proyecto_is2/sql-proxy01
docker-compose ps
```

**Esperado:**
```
NAME                  STATUS    PORTS
sql-proxy01-db-1      Up        5432->45432
sql-proxy01-web-1     Up        8080
sql-proxy01-web-sched-1  Up     (scheduler)
sql-proxy01-nginx-1   Up        80->40080
```

---

### Paso 3: Realizar una compra de divisas

1. **Ir a:** `http://localhost:8000`
2. **Iniciar sesión** con un usuario cliente
3. **Navegar a:** Comprar/Vender Divisas
4. **Realizar operación:**
   - Tipo: Compra
   - Moneda: USD
   - Monto: 100 USD
   - Método de pago: Tarjeta (Stripe)

5. **Completar pago con Stripe Test:**
   - Tarjeta: `4242 4242 4242 4242`
   - Fecha: Cualquier fecha futura
   - CVV: Cualquier 3 dígitos
   - ZIP: Cualquier 5 dígitos

---

### Paso 4: Verificar estado inicial de la factura

**La página debería mostrar:**

```
┌─────────────────────────────────────────────┐
│ ⏳ Procesando en SIFEN                     │
│                                             │
│ La factura está siendo procesada por SIFEN. │
│ Este proceso puede tomar entre 30-60 seg.   │
│                                             │
│  [🔄 Actualizar Estado]                     │
│                                             │
│ Última actualización: 30/10/2025 21:31:34   │
└─────────────────────────────────────────────┘

Documentos:
┌─────────────────────────────────────────────┐
│  [⏳ PDF procesándose...]   (deshabilitado) │
│  Espere 30-60 segundos y actualice          │
└─────────────────────────────────────────────┘
```

**La página se auto-refrescará cada 15 segundos**

---

### Paso 5: Esperar aprobación de SIFEN

**Timing esperado:**
- **0-20 segundos:** Estado = 'Confirmado'
- **20-40 segundos:** Estado = 'Sol.Aprobacion' (Solicitud de Aprobación)
- **40-60 segundos:** Estado = 'Aprobado' ✅

**Verificar en logs del scheduler:**
```bash
docker logs -f sql-proxy01-web-sched-1
```

**Debe mostrar:**
```
Ejecutando tarea do_de...
Estado actualizado: Sol.Aprobacion
...
Estado actualizado: Aprobado
PDF generado: /kude/202510/001-003-XXXXXXX_timestamp.pdf
```

---

### Paso 6: Verificar factura aprobada

**Después de ~60 segundos**, la página debe mostrar:

```
┌─────────────────────────────────────────────┐
│ Estado SIFEN:  ✅ Aprobado                  │
│ CDC: 01025957333001003000006612025...       │
└─────────────────────────────────────────────┘

Documentos:
┌─────────────────────────────────────────────┐
│  [📄 Descargar PDF]   (habilitado)          │
│  [📋 Descargar XML]   (staff only)          │
└─────────────────────────────────────────────┘
```

---

### Paso 7: Descargar y verificar PDF

**Click en "Descargar PDF"**

**URL esperada:**
```
http://localhost:40080/kude/202510/001-003-0000067_20251030_213134_944599.pdf
```

**El PDF debe contener:**
- ✅ Logo de empresa
- ✅ Datos de la empresa (RUC 2595733-3)
- ✅ Datos del cliente
- ✅ Detalles de la transacción
- ✅ CDC (Código de Control)
- ✅ QR Code
- ✅ Información del timbrado

---

## 🔍 VERIFICACIONES EN BASE DE DATOS

### Ver factura en Django:

```bash
cd /home/jose/proyecto_is2/global-exchange
python manage.py shell
```

```python
from facturacion_electronica.models import FacturaElectronica

# Ver última factura
factura = FacturaElectronica.objects.latest('id')
print(f"Número: {factura.numero_completo}")
print(f"Estado: {factura.estado}")
print(f"Estado SIFEN: {factura.estado_sifen}")
print(f"CDC: {factura.cdc}")
print(f"PDF: {factura.url_kude_pdf}")
print(f"XML: {factura.url_kude_xml}")
```

**Salida esperada:**
```
Número: 001-003-0000067
Estado: aprobado
Estado SIFEN: Aprobado
CDC: 01025957333001003000006712025103012412685114
PDF: http://localhost:40080/kude/202510/001-003-0000067_20251030_213134_944599.pdf
XML: http://localhost:40080/kude/202510/001-003-0000067_20251030_213133_989027.xml
```

---

### Ver factura en SQL Proxy:

```bash
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT id, dnumdoc, dpunexp, estado, estado_sifen, cdc FROM public.de ORDER BY id DESC LIMIT 1;"
```

**Salida esperada:**
```
 id  | dnumdoc | dpunexp |  estado  | estado_sifen |            cdc
-----+---------+---------+----------+--------------+-------------------------------
 67  | 0000067 |   003   | Aprobado |   Aprobado   | 010259573330010030000067120...
```

---

### Verificar pago insertado:

```bash
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT de_id, itipago, dmontipag FROM public.gPaConEIni WHERE de_id = 67;"
```

**Salida esperada:**
```
 de_id | itipago | dmontipag
-------+---------+-----------
    67 |    1    |     0
```

**Si NO aparece → ❌ ERROR - El sistema no insertó el pago**

---

### Verificar archivo PDF generado:

```bash
ls -lh /home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/202510/ | grep 0000067
```

**Salida esperada:**
```
-rw-r--r-- 1 root root  74K Oct 30 21:31 001-003-0000067_20251030_213134_944599.pdf
-rw-r--r-- 1 root root 7.9K Oct 30 21:31 001-003-0000067_20251030_213133_989027.xml
```

---

## ⚠️ PROBLEMAS COMUNES Y SOLUCIONES

### Problema 1: "PDF procesándose..." nunca cambia a "Descargar PDF"

**Causa:** La factura no se aprobó en SIFEN

**Solución:**
```bash
# 1. Ver estado en SQL Proxy
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT dnumdoc, estado, estado_sifen, descripcion_sifen FROM public.de WHERE dnumdoc = '0000067';"

# 2. Ver logs del scheduler
docker logs sql-proxy01-web-sched-1 --tail 50

# 3. Actualizar manualmente desde Django admin
# http://localhost:8000/admin/facturacion_electronica/facturaelectronica/
```

---

### Problema 2: Error "El operador ESI no tiene permiso..."

**Causa:** Punto de expedición incorrecto

**Verificar config:**
```bash
grep -A5 "punto_expedicion" /home/jose/proyecto_is2/global-exchange/facturacion_electronica/config.py
```

**Debe decir:**
```python
'punto_expedicion': '003'  # ✅ CORRECTO
```

**Si dice '001' → ❌ ERROR - Cambiar a '003'**

---

### Problema 3: Error "list index out of range"

**Causa:** Falta insertar pago en gPaConEIni

**Verificar en código:**
```bash
grep -A10 "gPaConEIni" /home/jose/proyecto_is2/global-exchange/facturacion_electronica/services.py
```

**Debe tener:**
```python
# OBLIGATORIO: Insertar forma de pago
insert_pago_query = f"""
INSERT INTO public.gPaConEIni
...
"""
```

---

### Problema 4: URL del PDF es incorrecta

**Ejemplo de error:**
- URL mostrada: `http://localhost:40080/kude/0000067.pdf` ❌
- URL correcta: `http://localhost:40080/kude/202510/001-003-0000067_timestamp.pdf` ✅

**Solución:**
```bash
# Verificar que services.py tiene la corrección
grep -A3 "directorio_fecha" /home/jose/proyecto_is2/global-exchange/facturacion_electronica/services.py
```

**Debe tener:**
```python
directorio_fecha = fecha_actual.strftime("%Y%m")  # 202510
url_kude_base = f"{SQL_PROXY_CONFIG['kude_url']}/{directorio_fecha}"
```

---

### Problema 5: La página no se auto-refresca

**Causa:** JavaScript no se ejecutó

**Verificar en el template:**
```bash
tail -10 /home/jose/proyecto_is2/global-exchange/facturacion_electronica/templates/facturacion/detalle_factura.html
```

**Debe contener:**
```django-html
{% if factura.estado_sifen == 'Procesando' ... %}
<script>
setTimeout(function() {
    location.reload();
}, 15000);
</script>
{% endif %}
```

---

## 📊 MÉTRICAS DE ÉXITO

### ✅ Criterios de aceptación:

1. **Generación automática:** Factura se crea al confirmar compra
2. **Tiempo de procesamiento:** 30-60 segundos hasta aprobación
3. **Estado mostrado:** "Procesando" → "Aprobado"
4. **PDF descargable:** URL correcta con subdirectorio de fecha
5. **CDC generado:** Código de control válido
6. **Auto-refresh:** Página se actualiza sola cada 15 segundos
7. **Botón deshabilitado:** No permite descargar hasta aprobación

### 📈 Estadísticas esperadas:

- **Tasa de éxito:** 100% de facturas aprobadas por SIFEN
- **Tiempo promedio:** 45 segundos desde generación hasta PDF disponible
- **Errores:** 0% (con configuración correcta)

---

## 🎯 CHECKLIST DE PRUEBA

```
[ ] Sistema levantado (Django + SQL Proxy + Redis)
[ ] Contenedores SQL Proxy corriendo (4 de 4)
[ ] Usuario puede iniciar sesión
[ ] Puede realizar compra de divisas
[ ] Pago con Stripe funciona
[ ] Factura se genera automáticamente
[ ] Página muestra "Procesando en SIFEN"
[ ] Botón PDF está deshabilitado durante procesamiento
[ ] Página se auto-refresca cada 15 segundos
[ ] Después de 60 segundos, estado cambia a "Aprobado"
[ ] Botón PDF se habilita
[ ] PDF se descarga correctamente
[ ] URL del PDF es correcta (incluye /YYYYMM/)
[ ] PDF contiene todos los datos requeridos
[ ] CDC está presente en el PDF
[ ] Verificación en base de datos SQL Proxy OK
[ ] Tabla gPaConEIni tiene entrada de pago
[ ] Archivo PDF existe en volumes/web/kude/YYYYMM/
```

---

## 🚨 COMANDOS DE EMERGENCIA

### Resetear base de datos de facturas (SOLO PARA DESARROLLO):

```bash
cd /home/jose/proyecto_is2/global-exchange
python manage.py shell
```

```python
from facturacion_electronica.models import FacturaElectronica
FacturaElectronica.objects.all().delete()
print("Todas las facturas eliminadas")
```

---

### Ver todas las facturas generadas:

```bash
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT id, dnumdoc, dpunexp, estado, estado_sifen, TO_CHAR(fch_ins, 'YYYY-MM-DD HH24:MI:SS') as creado FROM public.de ORDER BY id DESC LIMIT 10;"
```

---

### Eliminar factura en SQL Proxy (SOLO PARA DESARROLLO):

```bash
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "DELETE FROM public.gPaConEIni WHERE de_id = 67;
   DELETE FROM public.gCamItem WHERE de_id = 67;
   DELETE FROM public.de WHERE id = 67;"
```

---

## 📞 SOPORTE

Si encuentras problemas, verifica:

1. **Logs de Django:**
   ```bash
   cd /home/jose/proyecto_is2/global-exchange
   tail -f logs/django.log
   ```

2. **Logs de SQL Proxy (scheduler):**
   ```bash
   docker logs -f sql-proxy01-web-sched-1
   ```

3. **Estado de contenedores:**
   ```bash
   cd /home/jose/proyecto_is2/sql-proxy01
   docker-compose ps
   ```

---

**El sistema está listo para evaluación en ambiente de producción** 🎉
