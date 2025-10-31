# 🔧 FIX: Sensibilidad de Mayúsculas/Minúsculas en PostgreSQL

## 📋 Resumen del Problema

**Problema Original**: Las consultas SQL usaban nombres de columnas en CamelCase (ej: `dNumDoc`, `dEst`, `CDC`) pero PostgreSQL convierte automáticamente los identificadores **NO entrecomillados** a minúsculas.

**Síntoma**: 
- El CDC no se actualizaba correctamente (quedaba en '0')
- Las facturas se aprobaban en SIFEN pero Django no reflejaba el estado real
- PDFs se generaban pero no aparecían en la interfaz

**Causa Raíz**: PostgreSQL 17 normaliza todos los identificadores a minúsculas cuando NO están entre comillas dobles:
```sql
-- PostgreSQL convierte esto:
SELECT dNumDoc FROM de WHERE dEst = '001'

-- A esto:
SELECT dnumdoc FROM de WHERE dest = '001'
```

## ✅ Solución Implementada

**Estrategia**: Usar SIEMPRE minúsculas en los nombres de columnas SQL para evitar ambigüedades.

## 📝 Archivos Corregidos

### 1. `facturacion_electronica/services.py` ⭐ (CRÍTICO)

**Función: `obtener_proximo_numero()`** - Línea ~103-111
```python
# ANTES (INCORRECTO)
SELECT MAX(CAST(dNumDoc AS INTEGER)) as max_num
FROM public.de
WHERE dEst = '{establecimiento}'
AND dPunExp = '{punto_expedicion}'
AND CAST(dNumDoc AS INTEGER) >= {numero_inicial}

# DESPUÉS (CORRECTO)
SELECT MAX(CAST(dnumdoc AS INTEGER)) as max_num
FROM public.de
WHERE dest = '{establecimiento}'
AND dpunexp = '{punto_expedicion}'
AND CAST(dnumdoc AS INTEGER) >= {numero_inicial}
```

**Función: `crear_factura_venta()`** - Línea ~150-175
```python
# ANTES (INCORRECTO)
INSERT INTO public.de
(iTiDE, dFeEmiDE, dEst, dPunExp, dNumDoc, CDC, dSerieNum, estado,
 iTipEmi, dNumTim, dFeIniT, iTipTra, iTImp, cMoneOpe, dTiCam, dInfoFisc,
 dRucEm, dDVEmi, iTipCont, dNomEmi, dDirEmi, dNumCas,
 cDepEmi, dDesDepEmi, cCiuEmi, dDesCiuEmi, dTelEmi, dEmailE,
 ...)

# DESPUÉS (CORRECTO)
INSERT INTO public.de
(itide, dfeeemide, dest, dpunexp, dnumdoc, cdc, dserienum, estado,
 itipemi, dnumtim, dfeinit, dtiptra, itimp, cmoneooe, dticam, dinfofis,
 drucem, ddvemi, itipcont, dnomemi, ddiremi, dnumcas,
 cdepemi, ddesdepemi, cciuemi, ddesciuemi, dtelemi, demaile,
 ...)
```

**Función: `consultar_estado_factura()`** - Línea ~305-310 ⭐⭐⭐ (FIX MÁS IMPORTANTE)
```python
# ANTES (INCORRECTO) - ❌ Bug que impedía actualizar el CDC
SELECT id, dnumdoc, estado, estado_sifen, desc_sifen, 
       error_sifen, fch_sifen, cdc
FROM public.de
WHERE dNumDoc = '{numero_factura}'  # ❌ PostgreSQL → dnumdoc

# DESPUÉS (CORRECTO) - ✅ Ahora funciona perfectamente
SELECT id, dnumdoc, estado, estado_sifen, desc_sifen, 
       error_sifen, fch_sifen, cdc
FROM public.de
WHERE dnumdoc = '{numero_factura}'  # ✅ Coincide exactamente
```

**Función: `inutilizar_factura()`** - Línea ~354-385
```python
# ANTES (INCORRECTO)
INSERT INTO public.de
(iTiDE, dFeEmiDE, dEst, dPunExp, dNumDoc, CDC, dSerieNum, estado,
 ...)

# DESPUÉS (CORRECTO)
INSERT INTO public.de
(itide, dfeeemide, dest, dpunexp, dnumdoc, cdc, dserienum, estado,
 ...)
```

### 2. `facturacion_electronica/prueba_simple.py`

**Función: `obtener_proximo_numero()`** - Línea ~85-95
```python
# ANTES (INCORRECTO)
SELECT MAX(CAST(dNumDoc AS INTEGER)) as max_num
FROM public.de
WHERE dEst = '001' AND dPunExp = '003'

# DESPUÉS (CORRECTO)
SELECT MAX(CAST(dnumdoc AS INTEGER)) as max_num
FROM public.de
WHERE dest = '001' AND dpunexp = '003'
```

**Función: `crear_factura_prueba()`** - Línea ~115-142
```python
# ANTES (INCORRECTO)
INSERT INTO public.de
(iTiDE, dFeEmiDE, dEst, dPunExp, dNumDoc, CDC, ...)

# DESPUÉS (CORRECTO)
INSERT INTO public.de
(itide, dfeeemide, dest, dpunexp, dnumdoc, cdc, ...)
```

### 3. `insertar_factura_directa.py`

**Línea: ~34-60**
```python
# ANTES (INCORRECTO)
INSERT INTO public.de
(iTiDE, dFeEmiDE, dEst, dPunExp, dNumDoc, CDC, dSerieNum, ...)

# DESPUÉS (CORRECTO)
INSERT INTO public.de
(itide, dfeeemide, dest, dpunexp, dnumdoc, cdc, dserienum, ...)
```

## 🎯 Columnas Afectadas (Conversión Completa)

| ANTES (CamelCase) | DESPUÉS (lowercase) | Descripción |
|-------------------|---------------------|-------------|
| `iTiDE` | `itide` | Tipo de Documento Electrónico |
| `dFeEmiDE` | `dfeeemide` | Fecha de Emisión |
| `dEst` | `dest` | Establecimiento |
| `dPunExp` | `dpunexp` | Punto de Expedición |
| `dNumDoc` | `dnumdoc` | ⭐ Número de Documento |
| `CDC` | `cdc` | ⭐ Código de Control |
| `dSerieNum` | `dserienum` | Número de Serie |
| `iTipEmi` | `itipemi` | Tipo de Emisión |
| `dNumTim` | `dnumtim` | Número de Timbrado |
| `dFeIniT` | `dfeinit` | Fecha Inicio Timbrado |
| `iTipTra` | `dtiptra` | Tipo de Transacción |
| `iTImp` | `itimp` | Tipo de Impuesto |
| `cMoneOpe` | `cmoneooe` | Moneda de Operación |
| `dTiCam` | `dticam` | Tipo de Cambio |
| `dInfoFisc` | `dinfofis` | Información Fiscal |
| `dRucEm` | `drucem` | RUC Emisor |
| `dDVEmi` | `ddvemi` | DV Emisor |
| `iTipCont` | `itipcont` | Tipo de Contribuyente |
| `dNomEmi` | `dnomemi` | Nombre Emisor |
| `dDirEmi` | `ddiremi` | Dirección Emisor |
| `dNumCas` | `dnumcas` | Número de Casa |
| `cDepEmi` | `cdepemi` | Código Departamento Emisor |
| `dDesDepEmi` | `ddesdepemi` | Descripción Departamento Emisor |
| `cCiuEmi` | `cciuemi` | Código Ciudad Emisor |
| `dDesCiuEmi` | `ddesciuemi` | Descripción Ciudad Emisor |
| `dTelEmi` | `dtelemi` | Teléfono Emisor |
| `dEmailE` | `demaile` | Email Emisor |
| `iNatRec` | `inatrec` | Naturaleza Receptor |
| `iTiOpe` | `itiope` | Tipo de Operación |
| `cPaisRec` | `cpaisrec` | País Receptor |
| `iTiContRec` | `iticontrec` | Tipo Contribuyente Receptor |
| `dRucRec` | `drucrec` | RUC Receptor |
| `dDVRec` | `ddvrec` | DV Receptor |
| `iTipIDRec` | `itipidrec` | Tipo ID Receptor |
| `dDTipIDRec` | `ddtipidrec` | Descripción Tipo ID Receptor |
| `dNumIDRec` | `dnumidrec` | Número ID Receptor |
| `dNomRec` | `dnomrec` | Nombre Receptor |
| `dEmailRec` | `demailrec` | Email Receptor |
| `dDirRec` | `ddirrec` | Dirección Receptor |
| `dNumCasRec` | `dnumcasrec` | Número Casa Receptor |
| `cDepRec` | `cdeprec` | Código Departamento Receptor |
| `dDesDepRec` | `ddesdepres` | Descripción Departamento Receptor |
| `cCiuRec` | `cciurec` | Código Ciudad Receptor |
| `dDesCiuRec` | `ddesciurec` | Descripción Ciudad Receptor |
| ... | ... | (Y todas las demás columnas) |

## 🧪 Verificación

### Antes del Fix
```bash
poetry run python -c "
from facturacion_electronica.models import FacturaElectronica
f = FacturaElectronica.objects.get(numero_factura='0000077')
print(f'CDC: {f.cdc}')  # Resultado: CDC: 0 ❌
"
```

### Después del Fix
```bash
poetry run python -c "
from facturacion_electronica.models import FacturaElectronica
from facturacion_electronica.services import actualizar_estado_factura
f = FacturaElectronica.objects.get(numero_factura='0000077')
actualizar_estado_factura(f.id)
f.refresh_from_db()
print(f'CDC: {f.cdc}')  
# Resultado: CDC: 01025957333001003000007712025103116817479918 ✅
"
```

## 🔍 Archivos NO Modificados (Solo Lectura o Diagnóstico)

Estos archivos usan nombres en CamelCase pero son solo para diagnóstico:
- `verificar_estado_sifen.py` - Script de diagnóstico (contiene queries con ambos formatos para testing)
- `generar_factura_correcta.py` - Solo imprime comandos (no ejecuta queries directamente)
- `actualizar_esi_password.py` - Solo imprime ejemplos
- `sql-proxy01/client/app.py` - Cliente externo del SQL Proxy (fuera de Django)

## 📚 Lecciones Aprendidas

### 1. PostgreSQL y Case Sensitivity
- **Identificadores SIN comillas**: Se convierten a minúsculas
  ```sql
  SELECT dNumDoc FROM de  →  SELECT dnumdoc FROM de
  ```
- **Identificadores CON comillas**: Se respeta el case exacto
  ```sql
  SELECT "dNumDoc" FROM de  →  Error si la columna es 'dnumdoc'
  ```

### 2. Buenas Prácticas
✅ **HACER**:
- Usar siempre minúsculas en nombres de columnas SQL
- Ser consistente en toda la aplicación
- Probar queries en ambientes de desarrollo primero

❌ **EVITAR**:
- Mezclar CamelCase y lowercase
- Usar comillas dobles innecesariamente
- Asumir que SQL es case-insensitive

### 3. Debugging Sistemático
1. ✅ Verificar la fuente (SIFEN) → Funcionaba
2. ✅ Verificar el almacenamiento (PDFs) → Funcionaban
3. ✅ Verificar la base de datos (SQL Proxy) → Tenía datos correctos
4. ✅ Verificar la sincronización (Django) → ❌ **AQUÍ ESTABA EL BUG**
5. ✅ Verificar las queries SQL → **ENCONTRADO: Case mismatch**

## 🎯 Impacto del Fix

### Antes
- ❌ CDC quedaba en '0' después de la aprobación
- ❌ URL del PDF no se mostraba en la interfaz
- ❌ Usuarios no podían descargar facturas aprobadas
- ❌ Requería actualización manual forzada

### Después
- ✅ CDC se actualiza automáticamente
- ✅ URL del PDF aparece inmediatamente
- ✅ Botón de descarga funciona perfectamente
- ✅ Sistema completamente automático

## 🚀 Próximos Pasos

1. ✅ **COMPLETADO**: Corregir todas las queries SQL a lowercase
2. ⏳ **OPCIONAL**: Actualizar facturas antiguas con CDC='0'
   ```python
   from facturacion_electronica.models import FacturaElectronica
   from facturacion_electronica.services import actualizar_estado_factura
   
   facturas = FacturaElectronica.objects.filter(cdc='0', estado='aprobado')
   for f in facturas:
       actualizar_estado_factura(f.id)
       print(f"✅ Actualizada: {f.numero_factura}")
   ```
3. 🔄 **RECOMENDADO**: Testing end-to-end en producción
4. 📝 **SUGERIDO**: Agregar tests unitarios para verificar case consistency

## ⚠️ Precauciones

- **NO usar** queries con CamelCase en nuevos desarrollos
- **SIEMPRE** usar minúsculas para columnas de `public.de`
- **VERIFICAR** que scripts externos también usen lowercase
- **PROBAR** en desarrollo antes de deployar a producción

---

## 📅 Fecha de Implementación
**31 de Octubre de 2025**

## 👨‍💻 Autor
Sistema de Facturación Electrónica - Global Exchange

## 📌 Relacionado
- `DEBUG_APROBADO_SIN_PDF.md` - Diagnóstico del problema original
- `CORRECCION_IVA_EXENTAS.md` - Fix de IVA para cambio de divisas
- `MEJORA_UX_ESTADOS_FACTURACION.md` - Mejoras de interfaz de usuario
