# 🔍 Análisis: Lógica de CDC vs Búsqueda de PDFs

## ⚖️ Comparación de Implementaciones

### ✅ Lógica CDC (NO MODIFICADA - Implementación Original)

**Función:** `actualizar_estado_factura(factura)` en `utils.py`

**Responsabilidad:**
- Consultar estado en SQL Proxy
- Actualizar CDC cuando SIFEN lo devuelve
- Cambiar estado a 'aprobado' si CDC es válido
- Detectar CDC='0' como placeholder

**Código (INTACTO):**
```python
def actualizar_estado_factura(factura):
    """
    ⭐ ESTA FUNCIÓN NO SE MODIFICÓ
    Sigue funcionando EXACTAMENTE igual que antes
    """
    servicio = SQLProxyService()
    
    # Consultar estado en el SQL Proxy
    estado = servicio.consultar_estado_factura(factura.numero_documento)
    
    if estado:
        factura.estado_sifen = estado.get('estado_sifen', '')
        factura.descripcion_sifen = estado.get('desc_sifen', '')
        factura.error_sifen = estado.get('error_sifen', '')
        
        # ⭐ Si tiene CDC VÁLIDO (no '0'), actualizar
        cdc_recibido = estado.get('cdc', '')
        if cdc_recibido and cdc_recibido != '0':  # ← ESTA LÓGICA NO CAMBIÓ
            factura.cdc = cdc_recibido
            factura.estado = 'aprobado'
            factura.fecha_aprobacion = timezone.now()
            
            # URL base (se actualizará después con archivo específico)
            fecha_str = factura.fecha_emision.strftime('%Y%m')
            factura.url_kude_pdf = f"http://localhost:40080/kude/{fecha_str}/"
        
        factura.save()
```

**Se ejecuta cuando:**
- Usuario presiona F5 en cualquier vista
- Factura tiene `cdc='0'` o `cdc=None`
- Factura está en estado `confirmado` o `borrador`

---

### 🆕 Lógica de Búsqueda de PDFs (NUEVA - Recién Agregada)

**Función:** `buscar_y_actualizar_pdf(factura)` en `utils.py`

**Responsabilidad:**
- Buscar archivo PDF en el filesystem
- Actualizar URL completa cuando encuentra el archivo
- Solo para facturas YA aprobadas con CDC válido

**Código (NUEVO):**
```python
def buscar_y_actualizar_pdf(factura):
    """
    ⭐ ESTA ES LA NUEVA FUNCIÓN
    No interfiere con la lógica de CDC
    """
    # Solo buscar para facturas aprobadas con CDC válido
    if factura.estado != 'aprobado' or not factura.cdc or factura.cdc == '0':
        return False  # ← No hace nada si CDC aún no es válido
    
    # Si ya tiene URL completa con .pdf, no buscar de nuevo
    if factura.url_kude_pdf and '.pdf' in factura.url_kude_pdf:
        return True
    
    # Construir patrón de búsqueda
    fecha_str = factura.fecha_emision.strftime('%Y%m')
    pdf_pattern = f'/home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/{fecha_str}/{factura.numero_factura}_*.pdf'
    
    # Buscar archivos que coincidan
    pdfs = glob.glob(pdf_pattern)
    
    if pdfs:
        # Actualizar URL con archivo específico
        pdf_file = os.path.basename(pdfs[0])
        nueva_url = f"http://localhost:40080/kude/{fecha_str}/{pdf_file}"
        factura.url_kude_pdf = nueva_url
        factura.save(update_fields=['url_kude_pdf'])
        return True
    
    return False
```

**Se ejecuta cuando:**
- Factura YA está aprobada (CDC válido recibido)
- URL del PDF no tiene `.pdf` todavía
- Usuario presiona F5 en cualquier vista

---

## 🔄 Flujo Completo (Ambas Lógicas Trabajando Juntas)

```
┌─────────────────────────────────────────────────────────────┐
│ USUARIO PRESIONA F5                                         │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ ¿Factura tiene CDC='0'│
        │ o está en confirmado? │
        └───────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
        SÍ                    NO
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│ PASO 1:         │   │ CDC ya válido   │
│ actualizar_     │   │ Skip paso 1     │
│ estado_factura()│   └─────────────────┘
│                 │            │
│ - Consulta SQL  │            │
│   Proxy         │            │
│ - Obtiene CDC   │            │
│ - Actualiza     │            │
│   factura.cdc   │            │
│ - Estado →      │            │
│   'aprobado'    │            │
│ - url_kude_pdf  │            │
│   → directorio  │            │
└─────────────────┘            │
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ ¿Factura aprobada Y   │
        │ CDC válido Y PDF sin  │
        │ archivo específico?   │
        └───────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
        SÍ                    NO
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│ PASO 2:         │   │ Ya tiene PDF    │
│ buscar_y_       │   │ o no aplica     │
│ actualizar_pdf()│   │ Skip paso 2     │
│                 │   └─────────────────┘
│ - Busca archivo │            │
│   en filesystem │            │
│ - Si existe:    │            │
│   url_kude_pdf  │            │
│   → .pdf        │            │
└─────────────────┘            │
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ factura.refresh_      │
        │ from_db()             │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Renderizar página con │
        │ estado actualizado    │
        └───────────────────────┘
```

---

## 📊 Tabla Comparativa

| Aspecto | `actualizar_estado_factura()` | `buscar_y_actualizar_pdf()` |
|---------|-------------------------------|----------------------------|
| **¿Se modificó?** | ❌ NO (intacta) | ✅ SÍ (nueva) |
| **Consulta SQL Proxy** | ✅ Sí | ❌ No |
| **Actualiza CDC** | ✅ Sí | ❌ No |
| **Busca archivo PDF** | ❌ No | ✅ Sí |
| **Cuándo se ejecuta** | Cuando CDC='0' | Cuando CDC válido |
| **Depende de** | SQL Proxy | Filesystem |
| **Actualiza** | `cdc`, `estado`, `url_kude_pdf` (dir) | `url_kude_pdf` (archivo) |

---

## 🎯 Ejemplo Concreto

### Escenario: Factura Recién Creada

**Estado Inicial:**
```python
factura.estado = 'confirmado'
factura.cdc = '0'
factura.url_kude_pdf = None
```

**Usuario presiona F5 (Primera vez - 30s después):**

1️⃣ **Se ejecuta:** `actualizar_estado_factura()`
```python
# Consulta SQL Proxy
estado = servicio.consultar_estado_factura(...)
cdc_recibido = estado.get('cdc')  # → '01234567890123456789012345678901234567890123'

# Actualiza factura
factura.cdc = '01234567890123456789012345678901234567890123'  # ← CDC VÁLIDO
factura.estado = 'aprobado'
factura.url_kude_pdf = 'http://localhost:40080/kude/202510/'  # ← Solo directorio
factura.save()
```

2️⃣ **Se ejecuta:** `buscar_y_actualizar_pdf()`
```python
# Verificación
if factura.estado != 'aprobado':  # → False (es aprobado)
if not factura.cdc or factura.cdc == '0':  # → False (CDC válido)

# Busca archivo
pdf_pattern = '/home/.../kude/202510/001-003-0000075_*.pdf'
pdfs = glob.glob(pdf_pattern)  # → [] (aún no existe)

return False  # ← PDF no encontrado
```

**Resultado:**
```python
factura.estado = 'aprobado'
factura.cdc = '01234567890123456789012345678901234567890123'
factura.url_kude_pdf = 'http://localhost:40080/kude/202510/'  # ← Sin .pdf
```

**Usuario presiona F5 (Segunda vez - 60s después):**

1️⃣ **NO se ejecuta:** `actualizar_estado_factura()`
```python
# Filtro en vista:
facturas_pendientes = FacturaElectronica.objects.filter(
    Q(cdc__isnull=True) | Q(cdc='0') | Q(estado__in=['confirmado', 'borrador'])
)
# ← Esta factura NO está en el filtro porque:
#    - cdc NO es None
#    - cdc NO es '0'
#    - estado NO es 'confirmado' ni 'borrador'
```

2️⃣ **Se ejecuta:** `buscar_y_actualizar_pdf()`
```python
# Verificación
if factura.estado != 'aprobado':  # → False
if not factura.cdc or factura.cdc == '0':  # → False
if '.pdf' in factura.url_kude_pdf:  # → False (solo tiene directorio)

# Busca archivo
pdf_pattern = '/home/.../kude/202510/001-003-0000075_*.pdf'
pdfs = glob.glob(pdf_pattern)  # → ['001-003-0000075_20251031_013822_194929.pdf']

# Actualiza URL
pdf_file = '001-003-0000075_20251031_013822_194929.pdf'
factura.url_kude_pdf = 'http://localhost:40080/kude/202510/001-003-0000075_20251031_013822_194929.pdf'
factura.save(update_fields=['url_kude_pdf'])

return True  # ← PDF encontrado y actualizado
```

**Resultado Final:**
```python
factura.estado = 'aprobado'
factura.cdc = '01234567890123456789012345678901234567890123'
factura.url_kude_pdf = 'http://localhost:40080/kude/202510/001-003-0000075_20251031_013822_194929.pdf'
# ↑ Ahora tiene .pdf
```

---

## ✅ Resumen: ¿Qué Cambió?

### ❌ NO SE MODIFICÓ:
- ✅ `actualizar_estado_factura()` - **Intacta**
- ✅ Consulta a SQL Proxy - **Igual**
- ✅ Lógica de CDC='0' - **Igual**
- ✅ Cambio de estado a 'aprobado' - **Igual**
- ✅ Sincronización en vistas - **Igual**

### ✅ SE AGREGÓ:
- 🆕 `buscar_y_actualizar_pdf()` - **Nueva función**
- 🆕 Búsqueda en filesystem - **Nueva funcionalidad**
- 🆕 Actualización de URL con archivo específico - **Nuevo**
- 🆕 Validación `.pdf` en templates - **Nuevo**

### 🎯 Conclusión:

**Las dos lógicas son INDEPENDIENTES y COMPLEMENTARIAS:**

1. **Primera etapa (CDC):** `actualizar_estado_factura()`
   - Obtiene CDC de SIFEN
   - Cambia estado a 'aprobado'
   - Pone URL base del PDF

2. **Segunda etapa (PDF):** `buscar_y_actualizar_pdf()`
   - Busca archivo físico
   - Actualiza URL con nombre completo
   - Solo se ejecuta DESPUÉS de tener CDC válido

**La implementación de CDC NO SE TOCÓ**, solo se agregó una segunda capa que busca el archivo PDF físico después de que el CDC ya fue recibido.

---

**Fecha:** 31/10/2025  
**Estado:** ✅ Ambas lógicas funcionando en paralelo sin conflictos
