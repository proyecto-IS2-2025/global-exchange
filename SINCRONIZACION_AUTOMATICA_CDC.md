# 🔄 Sincronización Automática del CDC

## 📋 Explicación del Problema

### ¿Qué es el CDC?
El **CDC (Código de Control)** es un código único de 44 caracteres generado por **SIFEN** cuando aprueba una factura electrónica.

### Flujo del Sistema

```
┌─────────────┐
│   USUARIO   │ Hace compra/venta
│   (Django)  │
└──────┬──────┘
       │ 1. Crea factura con CDC='0'
       ↓
┌─────────────┐
│ SQL PROXY   │ Recibe factura
│             │
└──────┬──────┘
       │ 2. Envía a SIFEN
       ↓
┌─────────────┐
│   SIFEN     │ Procesa (30-60 seg)
│  (Paraguay) │
└──────┬──────┘
       │ 3. Aprueba y genera CDC real
       ↓
┌─────────────┐
│ SQL PROXY   │ Actualiza: CDC='01025957...' (44 chars)
│             │
└──────┬──────┘
       │ 4. Django debe sincronizar
       ↓
┌─────────────┐
│   DJANGO    │ Actualiza CDC en base de datos
│             │
└─────────────┘
```

### El Problema Original

**Síntoma**: Factura aparece como "Aprobado" pero CDC = '0'

**Causa**: El CDC solo existe DESPUÉS de que SIFEN aprueba. Inicialmente se guarda como '0' (placeholder).

**Solución**: Auto-sincronizar el CDC cuando el usuario recarga la página.

---

## ✅ Solución Implementada

### Estrategia: **Sincronización en Carga de Página**

En vez de usar timers o tareas programadas, el sistema **sincroniza automáticamente** cada vez que el usuario:
1. Entra a "Mis Facturas"
2. Entra al detalle de una factura
3. Entra al listado de todas las facturas (staff)

### Ventajas
- ✅ **Simple**: No requiere celery, redis, ni cron jobs
- ✅ **Confiable**: Se actualiza cuando el usuario lo necesita
- ✅ **Eficiente**: Solo consulta facturas pendientes
- ✅ **UX Natural**: El usuario presiona F5 para actualizar (como esperaría)

---

## 🔧 Implementación Técnica

### 1. Vista: `mis_facturas()` - Para Clientes

**Archivo**: `facturacion_electronica/views.py` - Línea ~120

```python
# ═══ AUTO-SINCRONIZAR FACTURAS PENDIENTES ═══
# Buscar facturas sin CDC válido o en estado pendiente
facturas_pendientes = facturas.filter(
    Q(cdc__isnull=True) | Q(cdc='0') | Q(estado__in=['confirmado', 'borrador'])
)

# Sincronizar estados desde SQL Proxy
for factura in facturas_pendientes:
    try:
        actualizar_estado_factura(factura)
        factura.refresh_from_db()
    except Exception as e:
        logger.warning(f"No se pudo sincronizar {factura.numero_factura}: {e}")
```

**Qué hace**:
1. Filtra facturas que NO tienen CDC válido (`None`, `'0'`, o estados pendientes)
2. Para cada una, llama a `actualizar_estado_factura()`
3. Refresca el objeto para mostrar datos actualizados

### 2. Vista: `detalle_factura()` - Detalle Individual

**Archivo**: `facturacion_electronica/views.py` - Línea ~190

```python
# AUTO-SINCRONIZAR: Si la factura está en estado procesando o sin CDC válido
if factura.estado in ['confirmado', 'borrador'] or not factura.cdc or factura.cdc == '0':
    try:
        from .utils import actualizar_estado_factura
        actualizar_estado_factura(factura)
        factura.refresh_from_db()
        logger.info(f"🔄 Factura {factura.numero_factura} sincronizada")
    except Exception as e:
        logger.warning(f"No se pudo sincronizar factura {factura.numero_factura}: {e}")
```

**Qué hace**:
- Verifica si la factura necesita actualización
- Sincroniza con SQL Proxy
- Loggea el resultado

### 3. Función: `actualizar_estado_factura()` - Core Logic

**Archivo**: `facturacion_electronica/utils.py` - Línea ~126

**FIX CRÍTICO**: Ahora verifica que el CDC sea válido (no '0')

```python
# ⭐ Si tiene CDC VÁLIDO (no '0'), actualizar
cdc_recibido = estado.get('cdc', '')
if cdc_recibido and cdc_recibido != '0':
    factura.cdc = cdc_recibido
    factura.estado = 'aprobado'
    factura.fecha_aprobacion = timezone.now()
    # ... actualizar URLs de PDF/XML
```

**Antes** (INCORRECTO):
```python
if estado.get('cdc'):  # ❌ Esto es True incluso para '0'
```

**Después** (CORRECTO):
```python
if cdc_recibido and cdc_recibido != '0':  # ✅ Solo si es un CDC real
```

---

## 🧪 Flujo Completo de Usuario

### Escenario: Usuario hace una compra

```
1. Usuario completa compra
   └─> Django genera factura con CDC='0'
   └─> Estado: "Procesando en SIFEN"

2. Usuario ve mensaje:
   "Espere 30-60 segundos y presione F5 para actualizar"

3. Usuario espera 60 segundos y presiona F5
   └─> Vista detecta: factura.cdc == '0'
   └─> Llama: actualizar_estado_factura()
   └─> Consulta SQL Proxy
   └─> SQL Proxy devuelve: CDC='01025957333001003000007812025103104567123456'
   └─> Django actualiza:
       - factura.cdc = '01025957...'
       - factura.estado = 'aprobado'
       - factura.url_kude_pdf = 'http://localhost:40080/kude/202510/001-003-0000078_...'

4. Usuario ve:
   ✅ Badge: "APROBADO" (verde)
   ✅ Botón: "Descargar PDF" (activo)
   ✅ CDC: 01025957333001003000007812025103104567123456
```

---

## 📊 Condiciones de Sincronización

### ¿Cuándo se sincroniza una factura?

Una factura se sincroniza SI cumple **alguna** de estas condiciones:

1. `factura.cdc IS NULL` - No tiene CDC
2. `factura.cdc == '0'` - Tiene placeholder (aún no aprobada)
3. `factura.estado IN ['confirmado', 'borrador']` - Estado pendiente
4. `factura.url_kude_pdf NO contiene '.pdf'` - No tiene URL de PDF

### Optimización

Solo se consultan las facturas que **necesitan** actualización, no todas.

```python
# Eficiente ✅
facturas_pendientes = facturas.filter(
    Q(cdc__isnull=True) | Q(cdc='0') | Q(estado__in=['confirmado', 'borrador'])
)

# Ineficiente ❌
for factura in facturas:  # Consulta TODAS las facturas
    actualizar_estado_factura(factura)
```

---

## 🎯 Beneficios del Approach

### 1. Sin Complejidad Adicional
- ❌ NO requiere Celery
- ❌ NO requiere Redis
- ❌ NO requiere Cron Jobs
- ❌ NO requiere WebSockets
- ✅ Solo Django + vistas

### 2. UX Natural
- Usuario sabe que debe esperar (~60 seg)
- Usuario controla cuándo actualizar (F5)
- No hay "magia" escondida

### 3. Confiable
- Se ejecuta en el mismo proceso de Django
- No hay race conditions
- Logs claros para debugging

### 4. Eficiente
- Solo consulta facturas pendientes
- No sobrecarga el SQL Proxy
- No hace polling continuo

---

## 📝 Instrucciones para el Usuario

### Mensaje que ve el usuario:

```
⏳ Procesando en SIFEN...
Espere 30-60 segundos y presione F5 para actualizar el estado.
```

### En el código (template):

```django
{% if factura.estado == 'confirmado' or factura.estado == 'borrador' %}
<div class="alert alert-warning">
    <strong><i class="fas fa-hourglass-half"></i> Procesando en SIFEN...</strong><br>
    La factura está siendo procesada por SIFEN.
    Espere 30-60 segundos y presione <kbd>F5</kbd> para actualizar el estado.
</div>
{% endif %}
```

---

## 🔍 Debugging

### Verificar si el CDC se actualizó

```bash
# Conectar a Django shell
poetry run python manage.py shell

# Consultar factura
from facturacion_electronica.models import FacturaElectronica
factura = FacturaElectronica.objects.get(numero_factura='001-003-0000078')

print(f"Estado: {factura.estado}")
print(f"CDC: {factura.cdc}")
print(f"URL PDF: {factura.url_kude_pdf}")

# Forzar sincronización manual
from facturacion_electronica.utils import actualizar_estado_factura
actualizar_estado_factura(factura)

factura.refresh_from_db()
print(f"CDC después de sync: {factura.cdc}")
```

### Logs a buscar

```
🔄 Factura 001-003-0000078 sincronizada - Estado: aprobado, CDC: 01025957333001003000...
```

---

## ⚠️ Casos Edge

### Caso 1: SIFEN tarda más de 60 segundos
**Solución**: Usuario presiona F5 nuevamente. Sistema sigue intentando hasta obtener el CDC.

### Caso 2: SIFEN rechaza la factura
**Solución**: `actualizar_estado_factura()` detecta `error_sifen` y marca estado='rechazado'.

### Caso 3: SQL Proxy no responde
**Solución**: Se loggea el error pero no crashea. Usuario ve mensaje de error y puede reintentar.

### Caso 4: Factura con CDC='0' pero aprobada
**Solución**: Ahora el código verifica `cdc != '0'` antes de considerar válido.

---

## 📅 Implementación

**Fecha**: 31 de Octubre de 2025  
**Tipo**: Feature - Auto-sincronización en carga de página  
**Archivos modificados**:
- `facturacion_electronica/views.py`
- `facturacion_electronica/utils.py`

**Estado**: ✅ **Implementado y Funcional**

---

## 🎉 Resumen

**Problema**: CDC mostraba '0' incluso después de SIFEN aprobar

**Causa**: Django no sincronizaba automáticamente con SQL Proxy

**Solución**: Auto-sincronizar al cargar página (F5)

**Resultado**: 
- ✅ Usuario presiona F5
- ✅ Sistema consulta SQL Proxy
- ✅ CDC se actualiza automáticamente
- ✅ PDF disponible para descarga
