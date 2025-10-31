# 🔢 Coordinación de Números de Factura - Trabajo en Equipo

## ❌ Problema Identificado

Cuando varios desarrolladores trabajan en sus máquinas locales generando facturas de prueba, surge el siguiente problema:

- **Desarrollador A** genera facturas desde el número 51
- **Desarrollador B** también genera facturas desde el número 51  
- **Desarrollador C** también genera facturas desde el número 51

**Resultado:** Conflictos de numeración cuando intentan sincronizar o cuando las facturas llegan a SIFEN.

## ✅ Solución

Necesitan **consultar el último número de factura ya generado** y coordinar rangos entre el equipo.

---

## 📊 Métodos para Consultar el Último Número

### Método 1: Script Python (RECOMENDADO)

El script más simple para obtener el próximo número disponible:

```bash
cd /home/jose/proyecto_is2/global-exchange
python obtener_proximo_numero.py
```

**Salida esperada:**
```
================================================================================
🔍 CONSULTANDO ÚLTIMO NÚMERO DE FACTURA
================================================================================

📋 ÚLTIMA FACTURA REGISTRADA:
   Número: 0000075
   Estado: Aprobado
   Fecha: 2025-10-31 01:38:22
   CDC: 01025957333001001000000752025103118628147910

✅ PRÓXIMO NÚMERO DISPONIBLE: 0000076

📊 ESTADÍSTICAS:
   ✅ Aprobado: 45
   ❌ Rechazado: 3
   ⏳ SOL.APROBACION: 2

💡 RECOMENDACIÓN PARA EL EQUIPO:
   Coordinen quién usa qué rango de números:
   - Desarrollador 1: 0000076 - 0000125
   - Desarrollador 2: 0000126 - 0000175
   - Desarrollador 3: 0000176 - 0000225
================================================================================
```

---

### Método 2: Consulta SQL Directa

Si prefieres SQL, usa el archivo `consultar_facturas_sifen.sql`:

#### Opción A: Desde Docker (SQL Proxy)
```bash
docker exec -it sql-proxy01-db-1 psql -U postgres -d fs_db
```

Luego ejecuta:
```sql
-- Ver última factura aprobada
SELECT 
    numero_factura,
    estado_sifen,
    cdc,
    fecha_emision,
    monto_total
FROM facturacion_electronica_facturaelectronica
WHERE estado_sifen IN ('Aprobado', 'Aprobado con observación')
ORDER BY numero_factura DESC
LIMIT 1;
```

#### Opción B: Desde Django dbshell
```bash
python manage.py dbshell
```

Luego copia y pega las consultas del archivo `consultar_facturas_sifen.sql`.

---

### Método 3: Django Shell

```bash
python manage.py shell
```

```python
from facturacion_electronica.models import FacturaElectronica
from django.db.models import Max

# Obtener último número
ultimo = FacturaElectronica.objects.aggregate(Max('numero_factura'))
print(f"Último número: {ultimo['numero_factura__max']}")

# Próximo número
proximo = int(ultimo['numero_factura__max']) + 1
print(f"Próximo número: {proximo:07d}")

# Contar por estado
from django.db.models import Count
stats = FacturaElectronica.objects.values('estado_sifen').annotate(total=Count('id'))
for s in stats:
    print(f"{s['estado_sifen']}: {s['total']}")
```

---

## 🤝 Coordinación en Equipo

### Estrategia 1: Asignación de Rangos por Desarrollador

Una vez que conocen el próximo número disponible (ejemplo: **76**), asignen rangos:

| Desarrollador | Rango Asignado | Cantidad |
|--------------|----------------|----------|
| José | 0000076 - 0000125 | 50 facturas |
| María | 0000126 - 0000175 | 50 facturas |
| Pedro | 0000176 - 0000225 | 50 facturas |

**Implementación:**
Cada desarrollador debe configurar en su `.env` local:

```bash
# José
NUMERO_FACTURA_INICIO=76
NUMERO_FACTURA_FIN=125

# María  
NUMERO_FACTURA_INICIO=126
NUMERO_FACTURA_FIN=175

# Pedro
NUMERO_FACTURA_INICIO=176
NUMERO_FACTURA_FIN=225
```

---

### Estrategia 2: Base de Datos Compartida

**Opción mejor:** En lugar de trabajar con bases de datos locales independientes, usen:

1. **Ambiente de desarrollo compartido** (todos apuntan a la misma BD de desarrollo)
2. **SQL Proxy compartido** (todos consultan el mismo SQL Proxy)
3. **Sincronización diaria** (al inicio del día, todos ejecutan el script para ver el estado)

---

## 📋 Consultas SQL Útiles

### 1. Ver todas las facturas generadas hoy
```sql
SELECT 
    numero_factura,
    estado_sifen,
    fecha_emision,
    monto_total,
    cliente_nombre
FROM facturacion_electronica_facturaelectronica
WHERE DATE(fecha_emision) = CURRENT_DATE
ORDER BY numero_factura DESC;
```

### 2. Verificar si un número específico existe
```sql
SELECT 
    numero_factura,
    estado_sifen,
    cdc
FROM facturacion_electronica_facturaelectronica
WHERE numero_factura = '0000051';
```

Si devuelve resultados, ese número **YA ESTÁ USADO**.

### 3. Encontrar "huecos" en la numeración
```sql
WITH numeros_usados AS (
    SELECT CAST(numero_factura AS INTEGER) as num
    FROM facturacion_electronica_facturaelectronica
    WHERE numero_factura ~ '^[0-9]+$'
)
SELECT 
    num,
    num + 1 as siguiente,
    CASE 
        WHEN num + 1 NOT IN (SELECT num FROM numeros_usados) 
        THEN 'HUECO ENCONTRADO'
        ELSE 'OK'
    END as verificacion
FROM numeros_usados
ORDER BY num;
```

---

## 🔄 Workflow Recomendado

### Al inicio de cada día o sprint:

1. **Todos ejecutan el script:**
   ```bash
   python obtener_proximo_numero.py
   ```

2. **Se coordinan en grupo:**
   - "Yo voy a usar del 76 al 100"
   - "Yo del 101 al 150"
   - "Yo del 151 al 200"

3. **Configuran sus `.env` locales** con sus rangos asignados

4. **Al final del día, sincronizan:**
   - Ejecutan nuevamente el script
   - Ven cuántas facturas se generaron
   - Planifican el próximo día

---

## 🚨 Prevención de Conflictos

### Opción A: Validación antes de generar
Modifica tu código para validar antes de generar una factura:

```python
def generar_factura(numero_factura):
    # Verificar si el número ya existe
    existe = FacturaElectronica.objects.filter(
        numero_factura=numero_factura
    ).exists()
    
    if existe:
        raise ValueError(
            f"El número {numero_factura} ya fue usado. "
            f"Ejecuta: python obtener_proximo_numero.py"
        )
    
    # Continuar con la generación...
```

### Opción B: Auto-incremento
Mejor aún, usa auto-incremento desde la base de datos:

```python
def obtener_proximo_numero_factura():
    from django.db.models import Max
    
    ultimo = FacturaElectronica.objects.aggregate(
        Max('numero_factura')
    )['numero_factura__max']
    
    if ultimo:
        proximo = int(ultimo) + 1
    else:
        proximo = 1
    
    return f"{proximo:07d}"  # Formato: 0000001
```

---

## 📚 Información de la API de Factura Segura

Según la documentación oficial, **NO existe** una operación directa de la API para listar todas las facturas generadas.

Las operaciones disponibles son:
- `generar_de` - Generar nueva factura
- `get_estado_sifen` - Consultar estado de una factura **conociendo su CDC**
- `sol_cancelacion` - Solicitar cancelación
- `sol_inutilizacion` - Solicitar inutilización

**Por lo tanto, la única forma confiable es:**
1. ✅ Consultar tu propia base de datos local
2. ✅ Consultar la base de datos compartida (SQL Proxy)
3. ❌ NO puedes listar facturas desde la API sin conocer el CDC

---

## 🎯 Recomendación Final

### Para este Sprint:

1. **Ejecuten el script ahora mismo:**
   ```bash
   python obtener_proximo_numero.py
   ```

2. **Coordinen en grupo** (por Slack/WhatsApp/Telegram):
   ```
   José: Voy a usar números del 76 al 125
   María: Yo del 126 al 175
   Pedro: Yo del 176 al 225
   ```

3. **Cada uno configure su `.env`** con su rango

4. **Al finalizar el Sprint**, ejecuten nuevamente el script para verificar el estado final

---

## 📞 ¿Necesitas ayuda?

Si tienes problemas ejecutando los scripts:

1. Verifica que estés en el directorio correcto:
   ```bash
   cd /home/jose/proyecto_is2/global-exchange
   ```

2. Verifica que tengas las variables de entorno:
   ```bash
   cat .env | grep DATABASE
   ```

3. Verifica la conexión a la base de datos:
   ```bash
   python manage.py dbshell
   ```

4. Ejecuta el script de diagnóstico:
   ```bash
   python consultar_ultimo_numero_factura.py
   ```

---

## 📝 Archivos Creados

- `obtener_proximo_numero.py` - Script simple para obtener el próximo número
- `consultar_ultimo_numero_factura.py` - Script completo con múltiples métodos
- `consultar_facturas_sifen.sql` - Consultas SQL útiles
- `COORDINACION_NUMEROS_FACTURA.md` - Este documento

---

**¡Buena suerte con el Sprint! 🚀**
