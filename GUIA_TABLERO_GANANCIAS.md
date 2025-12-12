# 📊 Tablero de Control de Ganancias - Guía de Uso

## ✅ Sistema Instalado Correctamente

Se ha creado exitosamente el módulo de **Tablero de Control de Ganancias** para Global Exchange.

---

## 🚀 Pasos para Empezar a Usar el Sistema

### 1. Configurar Permisos (Solo Primera Vez)

Ejecuta el siguiente comando en la terminal:

```bash
python manage.py shell
```

Luego ejecuta:

```python
from ganancias.permissions import crear_permisos_ganancias
crear_permisos_ganancias()
exit()
```

### 2. Asignar Permisos a Grupos de Usuarios

Ve al panel de administración de Django y asigna estos permisos al grupo **admin**:

- ✅ `ganancias | registro de ganancia | Can view registro de ganancia`
- ✅ `ganancias | registro de ganancia | Can change registro de ganancia`

### 3. Calcular Ganancias de Transacciones Existentes

Para calcular las ganancias de todas las transacciones completadas que ya existen en tu sistema:

```bash
python manage.py calcular_ganancias
```

Este comando:
- ✅ Analiza todas las transacciones en estado "completado"
- ✅ Calcula las comisiones basándose en el medio de pago
- ✅ Genera registros de ganancia automáticamente
- ✅ Actualiza los resúmenes diarios y mensuales

---

## 📱 Cómo Acceder al Tablero

1. **Inicia sesión** con una cuenta de administrador
2. En el menú principal de staff verás una nueva tarjeta: **"Ganancias"** con un ícono de gráfico verde
3. Haz clic en la tarjeta para acceder al tablero

**URL Directa**: `http://localhost:8000/ganancias/tablero/`

---

## 🎯 Funcionalidades del Tablero

### Panel Principal

#### 📊 Tarjetas de Resumen (4 métricas principales)

1. **GANANCIA TOTAL**
   - Muestra el total de ganancias del período seleccionado
   - Incluye variación porcentual vs período anterior

2. **POR COMISIONES**
   - Total de comisiones cobradas
   - Porcentaje respecto al total

3. **POR SPREAD**
   - Total de ganancias por spread
   - Porcentaje respecto al total

4. **TRANSACCIONES**
   - Cantidad de transacciones procesadas
   - Promedio de ganancia por transacción

#### 🔍 Filtros Disponibles

**Períodos Rápidos:**
- Hoy
- Última Semana
- Mes Actual (por defecto)
- Mes Anterior
- Año Actual

**Rango Personalizado:**
- Selecciona fecha de inicio y fin manualmente

#### 📈 Gráficos Interactivos

1. **Evolución de Ganancias** (línea temporal)
   - Comisiones (verde)
   - Spread (azul)
   - Total (rojo)

2. **Distribución por Tipo** (gráfico circular)
   - Proporción entre comisiones y spread

#### 💰 Ganancias por Divisa

Tabla detallada que muestra:
- Divisa y nombre
- Total de ganancia
- Cantidad de transacciones
- Promedio por transacción
- Porcentaje del total (barra visual)

#### 🏆 Top 10 Transacciones

Lista de las transacciones que generaron mayor ganancia:
- Número de transacción
- Cliente
- Divisa
- Tipo (comisión/spread)
- Montos desglosados
- Fecha y hora

---

## 📊 Comparación de Períodos

Accede desde el botón **"Comparar Períodos"** en el tablero.

### Comparaciones Disponibles

1. **Mes Actual vs Mes Anterior**
   - Totales lado a lado
   - Desglose de comisiones y spread
   - Indicador de incremento/disminución

2. **Año Actual vs Año Anterior**
   - Comparación anual completa
   - Variación porcentual

3. **Evolución Últimos 12 Meses**
   - Gráfico de barras apiladas
   - Tabla detallada mensual
   - Promedio por transacción

---

## ⚙️ Funciones Administrativas

### Actualizar Datos

El botón **"Actualizar Datos"** en el tablero permite:
- Recalcular ganancias de transacciones sin registro
- Actualizar resúmenes diarios y mensuales
- Útil cuando se completan transacciones manualmente

### Calcular Ganancias Manualmente

Desde la terminal:

```bash
# Calcular solo transacciones nuevas sin registro
python manage.py calcular_ganancias

# Recalcular TODAS las ganancias
python manage.py calcular_ganancias --recalcular
```

---

## 🔄 Funcionamiento Automático

El sistema calcula las ganancias **automáticamente** cuando:

1. ✅ Una transacción cambia su estado a "completado"
2. ✅ Se guarda una transacción que ya está completada

**No necesitas hacer nada manualmente** - el sistema se actualiza solo.

---

## 📋 Ejemplo de Uso Típico

1. **Inicio del día**: Accede al tablero con período "Hoy"
2. **Análisis semanal**: Cambia a "Última Semana" para ver tendencias
3. **Reporte mensual**: Usa "Mes Actual" y compara con "Mes Anterior"
4. **Análisis por divisa**: Revisa qué divisas generan más ganancias
5. **Identificación de oportunidades**: Analiza el Top 10 de transacciones

---

## 🎨 Características Visuales

- 🎨 **Diseño moderno** con tarjetas y gráficos interactivos
- 📱 **Responsive** - funciona en desktop, tablet y móvil
- 🌈 **Código de colores** para identificar rápidamente métricas
- 📊 **Gráficos con Chart.js** para visualización dinámica
- ⚡ **Animaciones suaves** al hacer hover sobre elementos

---

## 🔐 Seguridad y Permisos

Solo los usuarios con los siguientes permisos pueden acceder:
- `ganancias.view_registroganancia` - Ver el tablero
- `ganancias.change_registroganancia` - Actualizar datos

Por defecto, solo los **administradores** tienen acceso.

---

## 💡 Tips y Mejores Prácticas

1. **Revisa el tablero diariamente** para monitorear el desempeño
2. **Compara períodos** para identificar tendencias
3. **Analiza por divisa** para optimizar operaciones
4. **Usa el Top 10** para identificar clientes de alto valor
5. **Exporta datos** (función próximamente) para reportes externos

---

## ❓ Solución de Problemas

### No veo la tarjeta "Ganancias" en el menú

**Solución**: Verifica que tu usuario tenga el permiso `ganancias.view_registroganancia`

### No hay datos en el tablero

**Solución**: Ejecuta `python manage.py calcular_ganancias` para procesar transacciones existentes

### Los totales parecen incorrectos

**Solución**: Ejecuta `python manage.py calcular_ganancias --recalcular` para recalcular todo

---

## 📧 Soporte

Para dudas o problemas, contacta al equipo de desarrollo.

---

**¡Disfruta del nuevo Tablero de Control de Ganancias! 📊✨**
