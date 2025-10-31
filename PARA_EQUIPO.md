# 🎯 PARA LOS INTEGRANTES DEL EQUIPO

## ⚠️ URGENTE: Configurar Rango de Facturas

Cada uno debe configurar su propio rango de números de factura para evitar conflictos.

---

## 🚀 Setup SUPER Rápido (1 comando, 30 segundos)

### ✨ **NUEVO: Configuración Automática** ✨

Ejecuta este comando y el sistema te configura todo automáticamente:

```bash
cd global-exchange
poetry run python configurar_rango_automatico.py
```

**Eso es todo.** El script:
1. ✅ Consulta el último número usado (actualmente: 82)
2. ✅ Te asigna automáticamente los próximos 50 números (83-132)
3. ✅ Actualiza tu archivo `.env` con la configuración
4. ✅ Verifica que todo esté correcto

**Resultado:**
```
================================================================================
🎉 CONFIGURACIÓN COMPLETADA
================================================================================

✅ Tu rango de facturas:
   Número inicial: 0000083
   Número final: 0000132
   Total disponible: 50 facturas

✅ ¡Todo listo! Puedes generar facturas sin conflictos con tus compañeros.
================================================================================
```

---

## 🔄 ¿Qué Pasa si Varios lo Ejecutan al Mismo Tiempo?

**No hay problema.** Cada uno obtiene un rango único basado en el momento exacto en que ejecuta el script:

- **José** ejecuta primero → obtiene 83-132
- **María** ejecuta después → obtiene 133-182  
- **Pedro** ejecuta al final → obtiene 183-232

El sistema asigna rangos **secuencialmente** sin solapamiento.

---

## 📊 Método Manual (si prefieres coordinar antes)

### 1️⃣ Ver el estado actual

```bash
poetry run python obtener_proximo_numero.py
```

### 2️⃣ Coordinar con el equipo

**En el chat del grupo:**
```
José: Voy a usar del 83 al 132
María: Yo del 133 al 182  
Pedro: Yo del 183 al 232
```

### 3️⃣ Configurar manualmente tu `.env`

```bash
# Editar el archivo .env
nano .env  # o code .env
```

**Agregar estas líneas:**
```bash
FACTURACION_NUMERO_INICIAL=83    # ← Tu número inicial
FACTURACION_NUMERO_FINAL=132     # ← Tu número final
```

### 4️⃣ Verificar configuración

```bash
poetry run python verificar_configuracion_rango.py
```

---

## 📊 Estado Actual del Sistema

```
Última factura generada: 001-003-0000082
Próximo número disponible: 001-003-0000083

📈 Total de facturas: 13
   ✅ Aprobadas: 8
   ⏳ En proceso: 1
   ❓ Otros: 4
```

---

## 📝 Asignación de Rangos Sugerida

| Desarrollador | Rango | Variables en .env |
|--------------|-------|-------------------|
| Desarrollador 1 | 83 - 132 | `FACTURACION_NUMERO_INICIAL=83`<br>`FACTURACION_NUMERO_FINAL=132` |
| Desarrollador 2 | 133 - 182 | `FACTURACION_NUMERO_INICIAL=133`<br>`FACTURACION_NUMERO_FINAL=182` |
| Desarrollador 3 | 183 - 232 | `FACTURACION_NUMERO_INICIAL=183`<br>`FACTURACION_NUMERO_FINAL=232` |

**Cada rango tiene 50 números** (suficiente para desarrollo y pruebas).

---

## 🔧 Cómo Generar Facturas

Una vez configurado tu rango, puedes generar facturas de 3 formas:

### Opción 1: Desde el código

```python
from facturacion_electronica.utils import obtener_proximo_numero_factura

# El número se obtiene automáticamente de tu rango
numero = obtener_proximo_numero_factura()
print(f"Próximo número: {numero}")  # 001-003-0000083
```

### Opción 2: Desde una venta

Al crear una venta, la factura se genera automáticamente con el próximo número disponible de tu rango.

### Opción 3: Desde el admin de Django

1. http://localhost:8000/admin
2. Facturación Electrónica > Nueva Factura
3. El número se asigna automáticamente

---

## ❌ Problemas Comunes

### "Ya alcancé el límite de mi rango"

```bash
# Ver cuántos números te quedan
poetry run python verificar_configuracion_rango.py

# Si necesitas más, coordina un nuevo rango:
# Ejemplo: Si ya usaste 83-132, pide el 233-282
```

### "El número ya existe"

Esto significa que alguien más usó ese número. Ejecuta:

```bash
poetry run python obtener_proximo_numero.py
```

Y coordina nuevamente con el equipo.

### "No encuentro el archivo .env"

```bash
# Copiar el ejemplo
cp .env.example .env

# Editar y agregar tus variables
nano .env
```

---

## 📚 Más Información

- **Guía completa:** `COORDINACION_NUMEROS_FACTURA.md`
- **Configuración detallada:** `CONFIGURACION_RANGO_FACTURAS.md`
- **Resumen técnico:** `RESUMEN_SOLUCION_FACTURAS.md`
- **Consultas SQL:** `consultar_facturas_sifen.sql`

---

## ✅ Checklist

- [ ] Ejecuté `obtener_proximo_numero.py`
- [ ] Coordiné mi rango con el equipo (ejemplo: 83-132)
- [ ] Edité mi `.env` con `FACTURACION_NUMERO_INICIAL` y `FACTURACION_NUMERO_FINAL`
- [ ] Ejecuté `verificar_configuracion_rango.py` y todo está OK
- [ ] Generé una factura de prueba
- [ ] La factura tiene un número dentro de mi rango

---

**Si tienes dudas, consulta con el equipo o revisa la documentación completa.** 🚀
