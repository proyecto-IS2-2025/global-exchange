# 🚀 INICIO RÁPIDO - Para los Integrantes del Equipo

## ⚠️ URGENTE: No usen el número 51

El sistema ya tiene **82 facturas generadas**. El próximo número disponible es **83**.

---

## ⚡ Configuración AUTOMÁTICA (30 segundos)

### **NUEVO: Solo ejecuta este comando** ✨

```bash
cd /home/jose/proyecto_is2/global-exchange
poetry run python configurar_rango_automatico.py
```

**Eso es TODO.** El script hace todo automáticamente:
1. ✅ Ve que el último número usado es **82**
2. ✅ Te asigna automáticamente del **83 al 132** (50 números)
3. ✅ Actualiza tu `.env` con la configuración
4. ✅ Verifica que todo esté correcto
5. ✅ ¡Listo para usar!

---

## 🤔 ¿Y si varios lo ejecutamos al mismo tiempo?

**No hay problema.** Cada uno obtiene un rango único:

- **Primero en ejecutar** → obtiene 83-132
- **Segundo en ejecutar** → obtiene 133-182
- **Tercero en ejecutar** → obtiene 183-232

El sistema asigna rangos **secuencialmente** sin colisiones.

---

## 📋 Qué hacer AHORA (método manual - OPCIONAL)

Si prefieres coordinar manualmente con el equipo antes de configurar:

### 1. Ejecutar el script:

```bash
cd /home/jose/proyecto_is2/global-exchange
poetry run python obtener_proximo_numero.py
```

### 2. Verás algo como esto:

```
================================================================================
🔍 CONSULTANDO ÚLTIMO NÚMERO DE FACTURA
================================================================================

📋 ÚLTIMA FACTURA REGISTRADA:
   Número completo: 001-003-0000082
   ...

✅ PRÓXIMO NÚMERO DISPONIBLE:
   Formato completo: 001-003-0000083
   Solo número: 0000083

💡 RECOMENDACIÓN PARA EL EQUIPO:
   Coordinen quién usa qué rango de números:
   - Desarrollador 1: 0000083 - 0000132
   - Desarrollador 2: 0000133 - 0000182
   - Desarrollador 3: 0000183 - 0000232
```

### 3. Coordinar en el grupo:

Escriban en WhatsApp/Telegram:

```
[Tu nombre]: Voy a usar del 83 al 132
[Otro]: Yo del 133 al 182
[Otro]: Yo del 183 al 232
```

### 4. Anotar tu rango asignado:

```bash
# Agregar en tu .env local:
FACTURACION_NUMERO_INICIAL=83
FACTURACION_NUMERO_FINAL=132
```

### 5. Verificar tu configuración:

```bash
poetry run python verificar_configuracion_rango.py
```

**Deberías ver:**
```
✅ Configuración correcta!
   Puedes generar facturas del 83 al 132
   Tienes 50 números disponibles
```

### 6. ¡Listo para generar facturas!

Ahora cuando generes una factura, el sistema automáticamente:
- ✅ Usará el próximo número disponible en tu rango
- ✅ Validará que esté dentro de tu rango asignado
- ✅ Te avisará si te estás quedando sin números
- ✅ Evitará conflictos con tus compañeros

---

## ✅ Listo!

Ya pueden trabajar sin conflictos de numeración.

---

## ❓ Preguntas Frecuentes

### P: ¿Por qué no puedo usar el número 51?
**R:** Porque ya hay 82 facturas generadas en el sistema. Si usas el 51, habrá un conflicto con una factura existente.

### P: ¿Cómo sé qué número usar?
**R:** Ejecuta el script `obtener_proximo_numero.py` y te dirá cuál es el próximo disponible.

### P: ¿Puedo consultar sin el script?
**R:** Sí, usa SQL:
```bash
poetry run python manage.py dbshell
```
```sql
SELECT numero_factura FROM facturacion_electronica_facturaelectronica 
ORDER BY fecha_emision DESC LIMIT 1;
```

### P: ¿Qué pasa si dos personas usan el mismo número?
**R:** SIFEN rechazará la segunda factura por número duplicado. Por eso deben coordinarse.

### P: ¿Hay forma automática de evitar esto?
**R:** Sí, implementar auto-incremento en el código (ver `COORDINACION_NUMEROS_FACTURA.md` para detalles).

---

## 📞 ¿Problemas?

1. **Error al ejecutar el script:**
   ```bash
   # Asegúrate de estar en el directorio correcto
   cd /home/jose/proyecto_is2/global-exchange
   
   # Verifica que poetry esté instalado
   poetry --version
   
   # Verifica las variables de entorno
   cat .env | grep DATABASE
   ```

2. **No aparecen facturas:**
   - Verifica que estés conectado a la base de datos correcta
   - Revisa que haya facturas generadas previamente

3. **Otro problema:**
   - Consulta `COORDINACION_NUMEROS_FACTURA.md` (documentación completa)
   - Consulta `RESUMEN_SOLUCION_FACTURAS.md` (resumen ejecutivo)

---

## 📚 Más Información

- **Documentación completa:** `COORDINACION_NUMEROS_FACTURA.md`
- **Resumen ejecutivo:** `RESUMEN_SOLUCION_FACTURAS.md`
- **Consultas SQL:** `consultar_facturas_sifen.sql`
- **API de Factura Segura:** `API de Factura Segura para ESI v01 (1).pdf`

---

**Resumen en 1 línea:**
Ejecuta `poetry run python obtener_proximo_numero.py`, coordina tu rango con el equipo, y trabaja sin conflictos. 🎯
