# 🔧 CONFIGURACIÓN DE RANGO DE FACTURAS - Guía Práctica

## 🎯 Objetivo

Configurar tu máquina local para generar facturas en el **rango asignado a ti** sin conflictos con tus compañeros.

---

## 📋 Paso 1: Conocer tu rango asignado

### Ejecutar el script de coordinación:

```bash
cd /home/jose/proyecto_is2/global-exchange
poetry run python obtener_proximo_numero.py
```

### Coordinar con el equipo:

Ejemplo de coordinación en WhatsApp/Telegram:

```
José: Voy a usar del 83 al 132 (50 facturas)
María: Yo del 133 al 182 (50 facturas)
Pedro: Yo del 183 al 232 (50 facturas)
```

---

## 🔧 Paso 2: Configurar tu archivo .env

### Editar el archivo `.env` en la raíz del proyecto:

```bash
cd /home/jose/proyecto_is2/global-exchange
nano .env  # o code .env
```

### Agregar/modificar estas líneas:

```bash
# ============================================================
# CONFIGURACIÓN DE FACTURACIÓN - RANGO ASIGNADO
# ============================================================

# 🔢 RANGO DE NUMERACIÓN DE FACTURAS
# Configura tu rango asignado según la coordinación con el equipo
# Ejemplo: Si te asignaron del 83 al 132
FACTURACION_NUMERO_INICIAL=83
FACTURACION_NUMERO_FINAL=132

# 📍 PUNTO DE EXPEDICIÓN (no cambiar si no es necesario)
FACTURACION_ESTABLECIMIENTO=001
FACTURACION_PUNTO_EXPEDICION=003

# ⚠️ IMPORTANTE: Cada desarrollador debe tener un rango diferente
# ⚠️ No uses números fuera de tu rango asignado
```

### Ejemplo de configuración para cada desarrollador:

**José (Desarrollador 1):**
```bash
FACTURACION_NUMERO_INICIAL=83
FACTURACION_NUMERO_FINAL=132
```

**María (Desarrollador 2):**
```bash
FACTURACION_NUMERO_INICIAL=133
FACTURACION_NUMERO_FINAL=182
```

**Pedro (Desarrollador 3):**
```bash
FACTURACION_NUMERO_INICIAL=183
FACTURACION_NUMERO_FINAL=232
```

---

## ✅ Paso 3: Verificar la configuración

### Ejecutar el script de verificación:

```bash
poetry run python manage.py shell
```

```python
from facturacion_electronica.utils import obtener_configuracion_facturacion

config = obtener_configuracion_facturacion()
print(f"Rango asignado: {config['numero_inicial']} - {config['numero_final']}")
print(f"Próximo número a usar: {config['numero_actual']}")
```

### Resultado esperado:

```
Rango asignado: 83 - 132
Próximo número a usar: 0000083
```

---

## 🚀 Paso 4: Generar tu primera factura de prueba

### Opción A: Desde el admin de Django

1. Acceder a http://localhost:8000/admin
2. Ir a **Facturación Electrónica** > **Facturas**
3. Crear nueva factura
4. El número se asignará automáticamente dentro de tu rango

### Opción B: Desde el código

```python
from facturacion_electronica.services import FacturacionService

servicio = FacturacionService()

# El número se obtiene automáticamente de tu rango
factura = servicio.crear_factura_venta(
    cliente_id=1,
    items=[
        {
            'descripcion': 'Cambio de USD a PYG',
            'cantidad': 100,
            'precio_unitario': 7350,
            'iva_tasa': 10
        }
    ]
)

print(f"Factura generada: {factura.numero_factura}")
print(f"Estado: {factura.estado_sifen}")
```

### Opción C: Desde la interfaz web

1. Login en http://localhost:8000
2. Ir a **Transacciones** > **Nueva Venta**
3. Completar los datos de la venta
4. El sistema generará la factura automáticamente

---

## 🔍 Paso 5: Verificar que funciona correctamente

### Verificar el número generado:

```bash
poetry run python manage.py shell
```

```python
from facturacion_electronica.models import FacturaElectronica

# Ver la última factura que generaste
ultima = FacturaElectronica.objects.filter(
    usuario_creacion='tu_usuario'  # Reemplaza con tu usuario
).order_by('-fecha_emision').first()

print(f"Número: {ultima.numero_factura}")
print(f"Estado: {ultima.estado_sifen}")
print(f"CDC: {ultima.cdc}")
```

### Verificar que está en tu rango:

```python
import os
numero = int(ultima.numero_factura.split('-')[-1])
inicio = int(os.getenv('FACTURACION_NUMERO_INICIAL', '51'))
fin = int(os.getenv('FACTURACION_NUMERO_FINAL', '100'))

if inicio <= numero <= fin:
    print(f"✅ OK: El número {numero} está en tu rango ({inicio}-{fin})")
else:
    print(f"❌ ERROR: El número {numero} está FUERA de tu rango ({inicio}-{fin})")
```

---

## ⚠️ Problemas Comunes

### Problema 1: "El número generado no está en mi rango"

**Causa:** No configuraste el `.env` correctamente

**Solución:**
```bash
# Verificar que el .env tiene las variables correctas
cat .env | grep FACTURACION_NUMERO

# Reiniciar el servidor Django
pkill -f runserver
poetry run python manage.py runserver
```

---

### Problema 2: "Ya alcancé el límite de mi rango"

**Causa:** Generaste más de 50 facturas (tu rango asignado)

**Solución:**
```bash
# 1. Consultar el estado
poetry run python obtener_proximo_numero.py

# 2. Coordinar un nuevo rango con el equipo
# Ejemplo: Si ya usaste 83-132, pide el 233-282

# 3. Actualizar tu .env
FACTURACION_NUMERO_INICIAL=233
FACTURACION_NUMERO_FINAL=282
```

---

### Problema 3: "El número ya existe (error de duplicado)"

**Causa:** Otro compañero usó ese número

**Solución:**
```bash
# 1. Verificar qué números están ocupados
poetry run python obtener_proximo_numero.py

# 2. Coordinar nuevamente con el equipo
# 3. Asegurarse de que cada uno tiene un rango diferente
```

---

## 📊 Monitoreo del uso de tu rango

### Script para ver cuántas facturas has usado:

```bash
poetry run python manage.py shell
```

```python
import os
from facturacion_electronica.models import FacturaElectronica

inicio = int(os.getenv('FACTURACION_NUMERO_INICIAL', '51'))
fin = int(os.getenv('FACTURACION_NUMERO_FINAL', '100'))

# Contar facturas en tu rango
total = FacturaElectronica.objects.filter(
    numero_factura__gte=f'001-003-{str(inicio).zfill(7)}',
    numero_factura__lte=f'001-003-{str(fin).zfill(7)}'
).count()

disponibles = (fin - inicio + 1) - total
porcentaje = (total / (fin - inicio + 1)) * 100

print(f"📊 Estadísticas de tu rango ({inicio}-{fin}):")
print(f"   Usadas: {total}")
print(f"   Disponibles: {disponibles}")
print(f"   Porcentaje usado: {porcentaje:.1f}%")

if disponibles < 10:
    print(f"\n⚠️  ADVERTENCIA: Te quedan menos de 10 facturas disponibles!")
    print(f"   Coordina un nuevo rango con el equipo.")
```

---

## 🎯 Resumen

### Checklist de configuración:

- [ ] Ejecuté `obtener_proximo_numero.py` para ver el estado actual
- [ ] Coordiné mi rango con el equipo (ejemplo: 83-132)
- [ ] Edité mi archivo `.env` con `FACTURACION_NUMERO_INICIAL` y `FACTURACION_NUMERO_FINAL`
- [ ] Reinicié el servidor Django
- [ ] Generé una factura de prueba
- [ ] Verifiqué que el número está en mi rango
- [ ] (Opcional) Configuré el script de monitoreo

---

## 📞 ¿Necesitas ayuda?

### Si el sistema no genera números automáticamente:

1. Verifica que el archivo `facturacion_electronica/utils.py` existe y tiene la función `obtener_proximo_numero_factura()`
2. Verifica que el servicio está importando correctamente esa función
3. Consulta con José (el dueño del repo) para asegurarte de que el código está actualizado

### Si hay conflictos de numeración:

1. Ejecuta `poetry run python obtener_proximo_numero.py` para ver el estado real
2. Coordina con el equipo en tiempo real
3. Asegúrate de que cada uno tiene un rango exclusivo

---

**¡Configuración completa! Ahora puedes generar facturas sin conflictos. 🎉**
