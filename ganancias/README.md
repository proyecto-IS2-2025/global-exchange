# Módulo de Ganancias - Global Exchange

## Descripción

Este módulo proporciona un tablero de control completo para el seguimiento y análisis de las ganancias generadas por las transacciones en el sistema Global Exchange.

## Características Principales

### 📊 Tablero de Control de Ganancias
- **Visualización de ganancias totales** por período (día, semana, mes, año)
- **Ganancias por comisiones**: Seguimiento detallado de las comisiones cobradas
- **Ganancias por spread**: Análisis del spread en las operaciones de cambio
- **Gráficos interactivos**: Evolución temporal y distribución por tipo
- **Análisis por divisa**: Desglose de ganancias por cada divisa operada

### 📈 Comparación de Períodos
- Comparación mes actual vs mes anterior
- Comparación año actual vs año anterior
- Evolución de últimos 12 meses
- Cálculo automático de variaciones porcentuales

### 🎯 Métricas y KPIs
- Ganancia total consolidada
- Promedio de ganancia por transacción
- Top 10 transacciones con mayor ganancia
- Cantidad de transacciones procesadas
- Distribución porcentual por tipo de ganancia

## Instalación y Configuración

### 1. Ejecutar Migraciones

```bash
python manage.py makemigrations ganancias
python manage.py migrate ganancias
```

### 2. Calcular Ganancias de Transacciones Existentes

Para calcular las ganancias de todas las transacciones completadas existentes:

```bash
python manage.py calcular_ganancias
```

Para recalcular todas las ganancias (incluso las que ya existen):

```bash
python manage.py calcular_ganancias --recalcular
```

### 3. Configurar Permisos

Desde el shell de Django:

```python
from ganancias.permissions import crear_permisos_ganancias
crear_permisos_ganancias()
```

Luego asignar los permisos a los grupos correspondientes:
- `ganancias.view_registroganancia` - Ver registros de ganancias
- `ganancias.change_registroganancia` - Modificar registros de ganancias
- `ganancias.view_dashboard_ganancias` - Ver tablero de ganancias
- `ganancias.view_comparacion_ganancias` - Ver comparaciones
- `ganancias.export_reportes_ganancias` - Exportar reportes

## Uso

### Acceso al Tablero

Los administradores con los permisos adecuados verán una nueva tarjeta "Ganancias" en el menú principal de staff. Al hacer clic, accederán al tablero de control.

**URL directa**: `/ganancias/tablero/`

### Filtros Disponibles

El tablero permite filtrar por:
- **Períodos rápidos**: Hoy, Última Semana, Mes Actual, Mes Anterior, Año Actual
- **Rango personalizado**: Selección manual de fecha inicio y fecha fin

### Actualización de Datos

El botón "Actualizar Datos" en el tablero permite recalcular las ganancias de transacciones que no tienen registro asociado.

## Modelos

### RegistroGanancia
Almacena la ganancia individual de cada transacción completada:
- Monto de comisión
- Monto de spread
- Monto total
- Divisa de referencia
- Porcentaje de comisión aplicado
- Fecha de la transacción

### ResumenGananciaDiaria
Consolidado diario de ganancias:
- Total de comisiones del día
- Total de spread del día
- Total general
- Cantidad de transacciones

### ResumenGananciaMensual
Consolidado mensual de ganancias:
- Total de comisiones del mes
- Total de spread del mes
- Total general
- Cantidad de transacciones
- Promedio diario

## Cálculo Automático

El sistema calcula automáticamente las ganancias cuando:
1. Una transacción cambia su estado a "completado"
2. Se actualiza una transacción que ya está completada

Esto se maneja mediante señales de Django (`post_save`).

## API Endpoints

### `/ganancias/api/evolucion/`
Retorna datos de evolución temporal para gráficos.

**Parámetros**:
- `periodo`: mes_actual, mes_anterior, año
- `tipo`: diaria, mensual

### `/ganancias/api/por-divisa/`
Retorna distribución de ganancias por divisa.

**Parámetros**:
- `periodo`: mes_actual, año

## Integración con Transacciones

El módulo se integra automáticamente con el módulo de transacciones:
- Detecta automáticamente el medio de pago utilizado
- Extrae el porcentaje de comisión del medio de pago
- Calcula el monto de comisión sobre la base en PYG
- Identifica la divisa extranjera de la operación

## Próximas Mejoras

- [ ] Exportación de reportes a PDF/Excel
- [ ] Gráficos de tendencias predictivas
- [ ] Alertas de variaciones significativas
- [ ] Análisis de rentabilidad por cliente
- [ ] Dashboard personalizable
- [ ] Cálculo de spread real (diferencia entre tasa de compra y venta)

## Soporte

Para reportar problemas o sugerencias, contactar al equipo de desarrollo.
