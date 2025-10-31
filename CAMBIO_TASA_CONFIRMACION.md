# Implementación de Confirmación de Transacción por Cambio de Tasa

## 📋 Resumen

Se ha implementado un nuevo flujo para manejar transacciones cuando ocurre un cambio en la tasa de cambio de las divisas. Ahora, en lugar de cancelar automáticamente las transacciones pendientes, el sistema las marca como "Requiere Confirmación" y permite al cliente decidir qué hacer.

## 🎯 Objetivo

Cuando una transacción está en estado "Pendiente" y ocurre un cambio en la tasa de cambio de la divisa correspondiente, en lugar de cancelarla automáticamente:

1. La transacción pasa a un nuevo estado: **"Requiere Confirmación"**
2. Se notifica al cliente por sistema y/o correo electrónico
3. El cliente puede elegir entre dos opciones:
   - **Recalcular**: Actualizar los montos con la tasa actual y continuar
   - **Cancelar**: Cancelar la transacción definitivamente

## 🔧 Cambios Implementados

### 1. Modelo de Transacción (`transacciones/models.py`)

#### Nuevo Estado
- Se agregó el estado `'requiere_confirmacion'` a `ESTADO_CHOICES`
- Se aumentó el `max_length` de los campos de estado a 25 caracteres

#### Nuevos Métodos

**`recalcular_montos_con_tasa_actual()`**
- Calcula los nuevos montos de la transacción usando la cotización actual
- Retorna un diccionario con:
  - `nueva_tasa`: La tasa de cambio actual
  - `nuevo_monto_origen`: Monto origen recalculado
  - `nuevo_monto_destino`: Monto destino recalculado
  - `tasa_anterior`: Tasa que tenía la transacción
  - `monto_origen_anterior`: Monto origen original
  - `monto_destino_anterior`: Monto destino original

**`marcar_como_requiere_confirmacion(razon)`**
- Cambia el estado de la transacción a 'requiere_confirmacion'
- Crea un registro en el historial de cambios
- Envía una notificación al cliente

**`_enviar_notificacion_requiere_confirmacion(razon, notificacion_obj)`**
- Envía un correo electrónico informando que la transacción requiere confirmación
- Respeta la configuración de notificaciones del usuario

#### Señal Modificada

**`cancelar_transacciones_pendientes_por_tasa`**
- Ahora llama a `marcar_como_requiere_confirmacion()` en lugar de `cancelar_automaticamente()`
- Las transacciones pendientes afectadas por cambio de tasa pasan a "Requiere Confirmación"

### 2. Vista de Confirmación (`transacciones/views.py`)

**`confirmar_transaccion_nueva_tasa(request, numero_transaccion)`**
- Vista protegida que solo el cliente propietario puede acceder
- Muestra las dos opciones: recalcular o cancelar
- En GET: Muestra la comparación de montos (anterior vs nuevo)
- En POST: Procesa la decisión del cliente
  - **Si elige "recalcular"**: Actualiza los montos y vuelve a estado "Pendiente"
  - **Si elige "cancelar"**: Cancela la transacción definitivamente

### 3. Template (`transacciones/templates/confirmar_transaccion_nueva_tasa.html`)

Características del template:
- Muestra información completa de la transacción
- Comparación visual de montos (anterior → nuevo)
- Dos opciones claramente diferenciadas con cards interactivas
- Validación de formulario en JavaScript
- Campo opcional para razón de cancelación
- Checkbox de confirmación requerido

### 4. Estilos y Visualización

Se agregó el estilo para el nuevo estado en los siguientes templates:
- `historial_cliente.html`: Color naranja (#fd7e14) para "Requiere Confirmación"
- `historial_admin.html`: Badge naranja con el nuevo estado
- `detalle_transaccion.html`: Badge naranja con ícono de advertencia

Se agregaron botones de acción:
- En el historial del cliente: Botón "Confirmar" para transacciones que requieren confirmación
- En el detalle de transacción: Alerta y botón prominente para ir a la confirmación

### 5. URLs (`transacciones/urls.py`)

Nueva ruta:
```python
path('confirmar-nueva-tasa/<str:numero_transaccion>/', 
     views.confirmar_transaccion_nueva_tasa, 
     name='confirmar_nueva_tasa')
```

### 6. Migraciones

**`transacciones/migrations/0005_alter_historialtransaccion_estado_anterior_and_more.py`**
- Altera el campo `estado` en `Transaccion` (max_length=25)
- Altera el campo `estado_anterior` en `HistorialTransaccion` (max_length=25)
- Altera el campo `estado_nuevo` en `HistorialTransaccion` (max_length=25)

## 📧 Notificaciones

Cuando una transacción pasa a "Requiere Confirmación":

### Notificación del Sistema
```
Su transacción {numero_transaccion} requiere confirmación debido a un cambio en la cotización. 
Por favor, ingrese a su historial de transacciones para confirmar o cancelar la operación.
```

### Correo Electrónico
```
Asunto: Confirmación Requerida - Transacción #{numero_transaccion}

Estimado(a) cliente,

Te informamos que tu transacción de cambio #{numero_transaccion} REQUIERE CONFIRMACIÓN.

Razón: Cotización de {divisa} ha sido actualizada en el sistema.

La cotización de la divisa extranjera ha sido actualizada en nuestro sistema, 
lo que afecta la tasa de cambio con la que iniciaste tu transacción.

Por favor, ingresa a tu historial de transacciones donde podrás:
1. Recalcular los montos con la tasa actual y continuar con la transacción, o
2. Cancelar la transacción

Gracias por tu comprensión.
Equipo de Soporte - Global Exchange
```

## 🔄 Flujo Completo

```
1. Cliente crea una transacción (Estado: Pendiente)
   ↓
2. Se actualiza la cotización de la divisa
   ↓
3. Señal detecta transacciones pendientes afectadas
   ↓
4. Transacción pasa a "Requiere Confirmación"
   ↓
5. Se envía notificación al cliente
   ↓
6. Cliente ve la alerta en su historial
   ↓
7. Cliente hace clic en "Confirmar"
   ↓
8. Se muestra comparación de montos
   ↓
9. Cliente elige:
   
   OPCIÓN A: Recalcular
   - Se actualizan los montos con la tasa actual
   - Transacción vuelve a "Pendiente"
   - Cliente puede continuar con el pago
   
   OPCIÓN B: Cancelar
   - Transacción pasa a "Cancelada"
   - Cliente puede crear una nueva transacción
```

## 🎨 Colores de Estados

| Estado | Color | Código | Descripción |
|--------|-------|--------|-------------|
| Pendiente | Amarillo | `#ffc107` | Esperando acción del cliente |
| **Requiere Confirmación** | **Naranja** | **`#fd7e14`** | **Requiere decisión por cambio de tasa** |
| Pagada | Verde | `#28a745` | Pago registrado |
| Completado | Verde Oscuro | `#198754` | Transacción finalizada |
| Cancelada | Rojo | `#dc3545` | Cancelada por cliente o sistema |
| Anulada | Gris | `#6c757d` | Anulada por administrador |

## 🔒 Permisos

- Vista `confirmar_transaccion_nueva_tasa` requiere:
  - `transacciones.view_propias_transacciones`
  - El cliente debe ser el propietario de la transacción

## 📊 Ejemplo de Comparación de Montos

```
Tasa de Cambio
6,500.00 → 6,650.00

Monto en PYG
650,000 → 665,000

Monto en USD
100.00 → 100.00
```

## ✅ Testing Realizado

- [x] Migración aplicada correctamente
- [x] Sistema verifica sin errores (`python manage.py check`)
- [x] Nuevo estado agregado al modelo
- [x] Método de recálculo implementado
- [x] Vista de confirmación creada
- [x] Template funcional con validación JavaScript
- [x] Estilos aplicados en todos los templates
- [x] Notificaciones configuradas
- [x] URLs configuradas

## 🚀 Próximos Pasos para Pruebas

1. Crear una transacción de compra o venta
2. Cambiar la cotización de la divisa correspondiente
3. Verificar que la transacción pase a "Requiere Confirmación"
4. Verificar notificación en el sistema
5. Verificar correo electrónico (si está configurado)
6. Probar la vista de confirmación
7. Probar ambas opciones (recalcular y cancelar)
8. Verificar que los montos se actualicen correctamente
9. Verificar que el historial registre todos los cambios

## 📝 Notas Importantes

- El método `cancelar_automaticamente()` se mantiene para casos especiales donde se necesite cancelar directamente
- La señal solo afecta transacciones en estado "Pendiente"
- No se procesan cambios de tasa para divisas PYG
- El recálculo respeta los decimales de cada divisa (PYG: 0, otras: 2)
- El sistema mantiene compatibilidad con el flujo anterior

---

**Fecha de Implementación:** 31 de octubre de 2025  
**Rama:** feature/GLEX-20-Simulador-terminal-servicio  
**Desarrollador:** GitHub Copilot Assistant  
**Estado:** ✅ Implementado y listo para pruebas
