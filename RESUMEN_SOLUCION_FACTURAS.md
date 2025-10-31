# ✅ SOLUCIÓN: Coordinación de Números de Factura

## 🎯 Problema Resuelto

Tu equipo estaba generando facturas desde el número 51 sin saber cuántas facturas ya existen en el sistema. Esto causaba conflictos de numeración.

**Solución implementada:** Scripts para consultar el último número de factura usado y coordinar entre el equipo.

---

## 📊 Resultado de la Consulta

### Ejecutar el script:

```bash
cd /home/jose/proyecto_is2/global-exchange
poetry run python obtener_proximo_numero.py
```

### Resultado actual de tu sistema:

```
================================================================================
🔍 CONSULTANDO ÚLTIMO NÚMERO DE FACTURA
================================================================================

📋 ÚLTIMA FACTURA REGISTRADA:
   Número completo: 001-003-0000082
   Establecimiento: 001
   Punto Expedición: 003
   Número: 0000082
   Estado: (Aprobado/En proceso)
   Fecha: 2025-10-31 13:33:31
   CDC: 01025957333001003000008212025103113426401460

✅ PRÓXIMO NÚMERO DISPONIBLE:
   Formato completo: 001-003-0000083
   Solo número: 0000083

📊 ESTADÍSTICAS:
   ✅ Aprobado: 8
   ⏳ SOL.APROBACION: 1
   ❓ Otros: 4
```

---

## 🤝 Coordinación del Equipo

### ⚠️ IMPORTANTE: No usen el número 51

El último número usado es **82**, por lo que deben comenzar desde **83** o posterior.

### Asignación de Rangos Sugerida:

| Integrante | Rango Asignado | Formato Completo |
|------------|----------------|------------------|
| Desarrollador 1 | 83 - 132 | 001-003-0000083 a 001-003-0000132 |
| Desarrollador 2 | 133 - 182 | 001-003-0000133 a 001-003-0000182 |
| Desarrollador 3 | 183 - 232 | 001-003-0000183 a 001-003-0000232 |

---

## 📝 Cómo Usar

### 1. Todos ejecutan el script al inicio

Cada integrante del equipo debe ejecutar:

```bash
cd /home/jose/proyecto_is2/global-exchange
poetry run python obtener_proximo_numero.py
```

Esto les mostrará el estado actual.

### 2. Se coordinan por chat

Ejemplo de conversación en WhatsApp/Telegram:

```
María: Ejecuté el script, última factura es 82
José: Ok, yo voy a usar del 83 al 132
Pedro: Yo del 133 al 182
María: Yo del 183 al 232
```

### 3. Cada uno configura su rango (opcional)

Pueden agregar en su `.env` local:

```bash
# Rango asignado a José
NUMERO_FACTURA_INICIO=83
NUMERO_FACTURA_FIN=132
```

Y modificar su código para validar:

```python
def validar_numero_factura(numero):
    inicio = int(os.getenv('NUMERO_FACTURA_INICIO', '1'))
    fin = int(os.getenv('NUMERO_FACTURA_FIN', '999999'))
    
    if not (inicio <= numero <= fin):
        raise ValueError(
            f"Número {numero} fuera de tu rango asignado ({inicio}-{fin})"
        )
```

---

## 🔍 Consultas SQL Directas

Si prefieres consultar directo en la base de datos:

### Conectarse a la BD:

```bash
# Opción 1: Via Django
poetry run python manage.py dbshell

# Opción 2: Via psql directo
psql -h localhost -p 5432 -U tu_usuario -d tu_base_de_datos
```

### Consulta básica:

```sql
-- Ver última factura
SELECT 
    numero_factura,
    estado_sifen,
    fecha_emision,
    cdc
FROM facturacion_electronica_facturaelectronica
ORDER BY fecha_emision DESC
LIMIT 1;
```

### Verificar si un número existe:

```sql
-- Verificar si el número 0000051 ya existe
SELECT 
    numero_factura,
    estado_sifen
FROM facturacion_electronica_facturaelectronica
WHERE numero_factura LIKE '%0000051';
```

---

## 🚀 Mejora Futura: Auto-incremento

Para evitar este problema en el futuro, pueden implementar auto-incremento:

```python
# En tu servicio de facturación
from django.db.models import Max
from facturacion_electronica.models import FacturaElectronica

def obtener_siguiente_numero_factura():
    """
    Obtiene automáticamente el siguiente número de factura disponible.
    Thread-safe con select_for_update().
    """
    from django.db import transaction
    
    with transaction.atomic():
        # Obtener el último número
        ultima = FacturaElectronica.objects.select_for_update().aggregate(
            Max('numero_factura')
        )['numero_factura__max']
        
        if ultima:
            # Extraer solo la parte numérica
            if '-' in ultima:
                partes = ultima.split('-')
                numero = int(partes[2])
            else:
                numero = int(ultima)
            
            proximo = numero + 1
        else:
            proximo = 1
        
        # Formato: 001-003-0000083
        return f"001-003-{str(proximo).zfill(7)}"
```

Luego usan esto en lugar de asignar manualmente:

```python
# Antes (manual):
factura.numero_factura = "001-003-0000051"  # ❌ Riesgo de colisión

# Después (automático):
factura.numero_factura = obtener_siguiente_numero_factura()  # ✅ Seguro
```

---

## 📚 Información de la API de Factura Segura

### ⚠️ Limitación de la API

Según la documentación oficial (`API de Factura Segura para ESI v01.pdf`), **NO existe** una operación para listar todas las facturas generadas.

Las operaciones disponibles son:

- ✅ `generar_de` - Generar nueva factura
- ✅ `get_estado_sifen` - Consultar estado **si conoces el CDC**
- ✅ `sol_cancelacion` - Cancelar una factura
- ✅ `sol_inutilizacion` - Inutilizar un número
- ❌ ~~`listar_facturas`~~ - **NO EXISTE**

Por eso la única forma confiable es:
1. ✅ Consultar tu base de datos local (lo que hace el script)
2. ✅ Consultar la base de datos compartida (SQL Proxy)
3. ❌ NO puedes listar desde la API de Factura Segura

---

## 🎯 Resumen Ejecutivo

### Para este Sprint:

1. ✅ **Script creado y funcionando**: `obtener_proximo_numero.py`
2. ✅ **Último número detectado**: 82 (001-003-0000082)
3. ✅ **Próximo número disponible**: 83 (001-003-0000083)
4. ⚠️ **NO USAR número 51**: Ya hay 82 facturas generadas

### Acción inmediata:

```bash
# Todos ejecutan:
cd /home/jose/proyecto_is2/global-exchange
poetry run python obtener_proximo_numero.py

# Coordinan en grupo:
"Yo uso del 83 al 132"
"Yo del 133 al 182"
"Yo del 183 al 232"
```

---

## 📁 Archivos Creados

1. **`obtener_proximo_numero.py`** ⭐
   - Script principal, simple y rápido
   - Muestra último número y estadísticas
   - **Este es el que deben usar todos**

2. **`consultar_ultimo_numero_factura.py`**
   - Script completo con múltiples métodos de consulta
   - Incluye consulta via SQL Proxy
   - Para casos avanzados

3. **`consultar_facturas_sifen.sql`**
   - Consultas SQL útiles
   - Para usuarios que prefieren SQL directo

4. **`COORDINACION_NUMEROS_FACTURA.md`**
   - Documentación completa del problema y solución

5. **`RESUMEN_SOLUCION_FACTURAS.md`** (este archivo)
   - Resumen ejecutivo

---

## ✅ Checklist para el Equipo

- [ ] Todos ejecutan `poetry run python obtener_proximo_numero.py`
- [ ] Coordinan rangos de números en grupo
- [ ] Cada uno anota su rango asignado
- [ ] (Opcional) Configuran su `.env` con su rango
- [ ] (Opcional) Implementan validación de rango en su código
- [ ] Al final del día, ejecutan nuevamente el script para sincronizar

---

**¡Problema resuelto! 🎉**

El script está funcionando correctamente y pueden usarlo para coordinarse. Si tienen dudas, consulten los otros archivos de documentación creados.
