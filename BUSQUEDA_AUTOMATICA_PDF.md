# 🔍 Búsqueda Automática de PDFs - Sistema de Facturación

## 📋 Descripción

Sistema implementado para buscar automáticamente los archivos PDF de facturas electrónicas en el servidor cada vez que se accede a una página o se refresca (F5).

## 🎯 Objetivo

Habilitar el botón de descarga de PDF **solo cuando el archivo existe físicamente** en el servidor, similar a cómo funciona la sincronización del CDC con SIFEN.

## ⚙️ Implementación

### 1. Función Helper (`utils.py`)

```python
def buscar_y_actualizar_pdf(factura):
    """
    Busca el archivo PDF en el filesystem y actualiza la URL en la factura.
    
    - Solo para facturas aprobadas con CDC válido
    - Si ya tiene URL completa con .pdf, no busca de nuevo
    - Busca en: /sql-proxy01/volumes/web/kude/YYYYMM/001-003-NNNNNNN_*.pdf
    - Actualiza automáticamente la URL si encuentra el archivo
    """
```

**Lógica:**
1. ✅ Verifica que `estado == 'aprobado'`
2. ✅ Verifica que `cdc` existe y no es `'0'`
3. ✅ Si ya tiene URL con `.pdf`, retorna (no busca de nuevo)
4. 🔍 Busca archivos que coincidan con el patrón
5. 💾 Actualiza `url_kude_pdf` si encuentra el archivo
6. 📝 Registra en logs el resultado

### 2. Vistas Actualizadas

#### `detalle_factura()`
```python
# AUTO-BUSCAR PDF: Si está aprobada pero no tiene URL del PDF completa
if factura.estado == 'aprobado' and factura.cdc and factura.cdc != '0':
    if not factura.url_kude_pdf or '.pdf' not in factura.url_kude_pdf:
        buscar_y_actualizar_pdf(factura)
        factura.refresh_from_db()
```

#### `lista_facturas()` y `mis_facturas()`
```python
# Buscar PDFs en el filesystem para facturas aprobadas sin URL completa
from .utils import buscar_y_actualizar_pdf
for factura in list(facturas_pendientes) + list(facturas_sin_pdf):
    if factura.estado == 'aprobado' and factura.cdc and factura.cdc != '0':
        buscar_y_actualizar_pdf(factura)
```

### 3. Templates - Lógica de Botones

```django
{# Botón habilitado SOLO si tiene CDC válido Y PDF existe #}
{% if factura.estado == 'aprobado' and factura.cdc and factura.cdc != '0' and factura.url_kude_pdf %}
    <a href="{% url 'facturacion:descargar_pdf' factura.id %}" class="btn btn-success">
        <i class="fas fa-file-pdf"></i> Descargar PDF
    </a>
{% elif factura.estado == 'aprobado' and factura.cdc and factura.cdc != '0' and not factura.url_kude_pdf %}
    <button class="btn btn-warning" disabled>
        <i class="fas fa-hourglass-half"></i> PDF generándose...
    </button>
{% else %}
    <button class="btn btn-warning" disabled>
        <i class="fas fa-hourglass-half"></i> Esperando aprobación SIFEN...
    </button>
{% endif %}
```

## 🔄 Flujo Completo

### Escenario 1: Factura Recién Creada
```
1. Usuario compra → Factura creada
2. Estado: confirmado, CDC: '0'
3. Botón: "Esperando aprobación SIFEN..." (amarillo, deshabilitado)
4. Usuario presiona F5
5. Sistema consulta SQL Proxy → CDC válido recibido
6. Sistema busca PDF → No existe aún
7. Botón: "PDF generándose..." (amarillo, deshabilitado)
```

### Escenario 2: PDF Generado en el Servidor
```
8. SIFEN genera PDF en /kude/YYYYMM/001-003-NNNNNNN_YYYYMMDD_HHMMSS_NNNNNN.pdf
9. Usuario presiona F5
10. Sistema busca PDF → ¡Encontrado!
11. url_kude_pdf actualizado
12. Botón: "Descargar PDF" (verde, HABILITADO) ✅
```

## 📂 Ubicación de Archivos PDF

**Patrón de búsqueda:**
```
/home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/{YYYYMM}/{numero_factura}_*.pdf
```

**Ejemplo:**
```
/home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/202510/001-003-0000075_20251031_013822_194929.pdf
```

**URL generada:**
```
http://localhost:40080/kude/202510/001-003-0000075_20251031_013822_194929.pdf
```

## 🎨 Estados del Botón

| Estado Factura | CDC | PDF Existe | Botón |
|----------------|-----|------------|-------|
| `confirmado` o `borrador` | `'0'` o `null` | ❌ | 🟡 "Esperando aprobación..." (disabled) |
| `aprobado` | Válido | ❌ | 🟡 "PDF generándose..." (disabled) |
| `aprobado` | Válido | ✅ | 🟢 "Descargar PDF" (enabled) |
| `rechazado` | - | - | ⚪ "PDF no disponible" (disabled) |

## ✅ Ventajas del Sistema

1. **Automático**: No requiere intervención manual
2. **Reactivo**: Funciona con F5 (refresh manual)
3. **Eficiente**: Solo busca cuando es necesario
4. **Robusto**: Maneja errores sin romper la página
5. **Consistente**: Misma lógica en todas las vistas
6. **UX Claro**: Usuario ve estado exacto del proceso

## 🧪 Cómo Probar

```bash
# 1. Crear factura de prueba
cd /home/jose/proyecto_is2/global-exchange
poetry run python manage.py shell

# 2. Verificar estado inicial
from facturacion_electronica.models import FacturaElectronica
factura = FacturaElectronica.objects.latest('id')
print(f"Estado: {factura.estado}")
print(f"CDC: {factura.cdc}")
print(f"PDF: {factura.url_kude_pdf}")

# 3. Probar búsqueda manual
from facturacion_electronica.utils import buscar_y_actualizar_pdf
resultado = buscar_y_actualizar_pdf(factura)
print(f"PDF encontrado: {resultado}")
factura.refresh_from_db()
print(f"Nueva URL: {factura.url_kude_pdf}")
```

## 🔧 Troubleshooting

### Problema: Botón no se habilita después de F5

**Verificar:**
```bash
# 1. ¿Existe el archivo PDF?
ls -la /home/jose/proyecto_is2/sql-proxy01/volumes/web/kude/202510/001-003-*

# 2. ¿La factura tiene CDC válido?
poetry run python manage.py shell
>>> from facturacion_electronica.models import FacturaElectronica
>>> f = FacturaElectronica.objects.get(numero_factura='001-003-0000075')
>>> print(f"CDC: {f.cdc} (longitud: {len(f.cdc) if f.cdc else 0})")

# 3. ¿La URL se actualizó?
>>> print(f"URL: {f.url_kude_pdf}")
>>> print(f"Contiene .pdf: {'.pdf' in f.url_kude_pdf if f.url_kude_pdf else False}")
```

### Problema: Error 404 al descargar PDF

**Causa:** URL generada incorrectamente

**Solución:**
1. Verificar que el servidor web está corriendo en `localhost:40080`
2. Verificar que el directorio `/kude/` es accesible
3. Verificar permisos del archivo PDF

## 📊 Logs

**Búsqueda exitosa:**
```
INFO - 📄 PDF encontrado y actualizado para 001-003-0000075: 001-003-0000075_20251031_013822_194929.pdf
```

**PDF no encontrado aún:**
```
DEBUG - PDF no encontrado aún para 001-003-0000075 en /home/.../kude/202510/001-003-0000075_*.pdf
```

**Error en búsqueda:**
```
WARNING - Error buscando PDF para 001-003-0000075: [Errno 2] No such file or directory
```

## 🚀 Próximos Pasos (Opcional)

1. **WebSocket**: Notificación en tiempo real cuando el PDF se genera
2. **Caché**: Almacenar resultado de búsqueda por 5 minutos
3. **Batch**: Buscar PDFs para múltiples facturas en paralelo
4. **Admin**: Comando para buscar PDFs de todas las facturas pendientes

---

**Fecha de implementación:** 31/10/2025  
**Versión:** 1.0  
**Estado:** ✅ Implementado y funcionando
