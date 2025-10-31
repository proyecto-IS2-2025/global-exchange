# 🔧 Corrección: Operaciones Exentas de IVA en Compraventa de Divisas

## 📋 Problema Identificado

El sistema estaba generando facturas con **IVA incluido** (10%) para operaciones de compraventa de divisas, lo cual es **INCORRECTO** según la legislación paraguaya.

**Ejemplo del problema:**
- Cliente compra $100 USD
- Monto en PYG: 100.000 Gs.
- **ERROR:** Sistema calculaba como si hubiera IVA:
  - Base: 90.909 Gs. (100.000 / 1.10)
  - IVA 10%: 9.091 Gs.
  - Total: 100.000 Gs.
- **Resultado:** PDF mostraba totales incorrectos

## ✅ Solución Aplicada

### Fundamento Legal

Según la **Ley Tributaria de Paraguay**, la **compraventa de divisas** está **EXENTA** de IVA (Impuesto al Valor Agregado).

### Cambio en el Código

**Archivo:** `facturacion_electronica/services.py`
**Función:** `generar_factura_automatica()`
**Líneas:** ~477-487

**ANTES (INCORRECTO):**
```python
items = [{
    'descripcion': descripcion,
    'cantidad': 1,
    'precio_unitario': monto_pyg,
    'descuento': 0,
    'afectacion_iva': '1',  # ❌ Gravado (INCORRECTO)
    'proporcion_iva': '100',
    'tasa_iva': '10'  # ❌ IVA 10% (INCORRECTO)
}]
```

**DESPUÉS (CORRECTO):**
```python
items = [{
    'descripcion': descripcion,
    'cantidad': 1,
    'precio_unitario': monto_pyg,  # Monto completo
    'descuento': 0,
    'afectacion_iva': '3',  # ✅ EXENTO (compraventa de divisas)
    'proporcion_iva': '0',  # ✅ 0% de proporción gravada
    'tasa_iva': '0'  # ✅ Sin IVA
}]
```

## 📊 Mapeo de Campos SIFEN

### Campo E731 - iAfecIVA (Indicador de Afectación Tributaria)

| Código | Descripción | Uso |
|--------|-------------|-----|
| 1 | Gravado IVA | Productos/servicios normales con IVA |
| 2 | Exonerado | Casos especiales de exoneración |
| **3** | **Exento** | **✅ Compraventa de divisas** |
| 4 | Gravado parcial | Operaciones mixtas |

### Campos Relacionados

- **E732 - dPropIVA:** Proporción gravada = `0` (0% para exentos)
- **E733 - dTasaIVA:** Tasa de IVA = `0` (sin IVA)
- **F002 - dSubExe:** Subtotal exento (auto-calculado por SQL Proxy)
- **F008 - dTotOpe:** Total operación = monto completo (sin IVA)

## ✅ Resultado Esperado en el PDF

### Antes (INCORRECTO)
```
Gravadas 10%:    90.909 Gs.
IVA 10%:          9.091 Gs.
Total:          100.000 Gs.
```

### Después (CORRECTO)
```
Exentas:        100.000 Gs.
Gravadas 10%:         0 Gs.
IVA 10%:              0 Gs.
Total:          100.000 Gs.
```

## 🔍 Impacto del Cambio

### ✅ Lo que NO cambia (sigue funcionando)
- Conexión con SQL Proxy ✅
- Estructura de tablas (de, gCamItem, gPaConEIni, gActEco) ✅
- Generación de CDC ✅
- Aprobación de SIFEN ✅
- Descarga de PDF/XML ✅

### ✅ Lo que SÍ cambia (se corrige)
- Campo `iAfecIVA`: `1` → `3` (Gravado → Exento)
- Campo `dTasaIVA`: `10` → `0` (10% → 0%)
- Campo `dPropIVA`: `100` → `0` (100% → 0%)
- Totales en PDF: Ahora aparece en "Exentas" en lugar de "Gravadas 10%"

## 🧪 Prueba de Validación

### Comandos para Probar
```bash
# 1. Verificar sintaxis
poetry run python manage.py check

# 2. Hacer una compra de prueba
# - Ir a http://localhost:8000
# - Comprar cualquier divisa (ej: $100 USD)
# - Esperar 2-3 minutos

# 3. Verificar factura
# - Ir a http://localhost:8000/facturacion/mis-facturas/
# - Descargar PDF
# - Verificar que aparezca en "Exentas" (no en "Gravadas")
```

### Checklist de Verificación
- [ ] Factura se genera sin errores
- [ ] Estado SIFEN: "Aprobado"
- [ ] PDF descarga correctamente
- [ ] En el PDF:
  - [ ] **Exentas:** [monto completo] ✅
  - [ ] **Gravadas 10%:** 0 Gs. ✅
  - [ ] **IVA 10%:** 0 Gs. ✅
  - [ ] **Total:** [monto completo] ✅

## 📚 Referencias

### Documentación SIFEN
- **Manual Técnico v150:** Campo E731 (iAfecIVA) - Indicador de afectación tributaria
- **Valores permitidos:** 1=Gravado, 2=Exonerado, 3=Exento, 4=Gravado parcial
- **Sección F:** Campos de totales (dSubExe, dSub10, dTotOpe)

### Legislación Paraguaya
- La compraventa de divisas está **EXENTA** de IVA
- No se calcula ni se cobra IVA en estas operaciones
- El monto total de la operación va en el campo "Exentas"

## 🎯 Conclusión

**Cambio realizado:** 3 líneas de código
**Impacto:** Corrección legal y fiscal crítica
**Riesgo:** Bajo (solo afecta cálculo de IVA, no estructura)
**Testing:** Requerido (validar PDF muestre totales correctos)

---
**Fecha:** 31 de octubre de 2025
**Estado:** ✅ Implementado y validado sintácticamente
**Pendiente:** Prueba end-to-end con generación de factura real
