# Sistema de Procesamiento TAUSER

## 📋 Resumen

Este documento describe el flujo completo de procesamiento de transacciones en los terminales TAUSER, incluyendo retiros (compras) y depósitos (ventas).

## 🔄 Flujo Completo de Retiro (Compra)

### 1. **Inicio del Proceso**
- Cliente accede a `/tauser/` desde el terminal
- Selecciona el terminal activo
- Ingresa código TAUSER de 8 dígitos

### 2. **Verificación MFA** (si está habilitado)
- Sistema verifica `MFAConfig.mfa_tauser_enabled`
- Si está activado: envía OTP de 6 dígitos por email
- Cliente ingresa OTP
- Sistema valida y marca sesión como verificada

### 3. **Vista de Detalles**
- Vista: `mostrar_detalle_retiro`
- Template: `detalle_retiro.html`
- Muestra:
  - Información de la transacción
  - Monto a retirar
  - Denominaciones disponibles con stock
  - Botón "Procesar Retiro"

### 4. **Procesamiento del Retiro**
- Vista: `procesar_retiro` (POST)
- **Validaciones:**
  - ✅ Sesión MFA verificada
  - ✅ Transacción tipo 'compra'
  - ✅ Estado 'pagada'
  - ✅ Stock suficiente en terminal

- **Acciones:**
  1. **Cálculo de denominaciones**
     ```python
     resultado = calcular_desglose_optimo(inventarios, monto)
     # Returns: {posible, desglose, sobrante, monto_cubierto}
     ```
  
  2. **Actualización de inventario**
     ```python
     # Por cada denominación usada:
     inventario.cantidad_disponible -= cantidad
     
     # Registro en DesgloseDenominacionOperacion
     DesgloseDenominacionOperacion.objects.create(
         terminal=terminal,
         denominacion=denominacion,
         cantidad=cantidad,
         tipo_operacion='retiro',
         monto_operacion=monto
     )
     ```
  
  3. **Actualización de inventario general**
     ```python
     inventario_divisa.cantidad_disponible -= monto_destino
     ```
  
  4. **Cambio de estado**
     ```python
     transaccion.estado = 'completado'
     
     # Registro en historial
     HistorialTransaccion.objects.create(
         transaccion=transaccion,
         estado_anterior='pagada',
         estado_nuevo='completado',
         observaciones='Retiro procesado en terminal X (TAUSER)'
     )
     ```
  
  5. **Registro en terminal**
     ```python
     RegistroTransaccionTerminal.objects.create(
         terminal=terminal,
         transaccion=transaccion,
         tipo_operacion='retiro',
         exitosa=True
     )
     ```
  
  6. **Limpieza de sesión**
     ```python
     request.session.flush()
     ```

### 5. **Resultado**
- ✅ Mensaje de éxito con monto entregado
- 💵 Instrucción para recoger dinero
- 🔙 Redirección a página principal

---

## 🔄 Flujo Completo de Depósito (Venta)

### 1. **Inicio del Proceso**
- Cliente accede a `/tauser/` desde el terminal
- Ingresa código TAUSER
- Verifica MFA (si está habilitado)

### 2. **Vista de Detalles**
- Vista: `mostrar_detalle_deposito`
- Template: `detalle_deposito.html`
- Muestra:
  - Monto a depositar
  - Monto a recibir
  - Denominaciones aceptadas
  - Botón "Confirmar Depósito"

### 3. **Procesamiento del Depósito**
- Vista: `procesar_pago` (POST)
- **Validaciones:**
  - ✅ Sesión MFA verificada
  - ✅ Transacción tipo 'venta'
  - ✅ Estado 'pendiente' o 'pagada'

- **Acciones:**
  1. **Simulación de aceptación de billetes**
     - En producción: integrar con validador de billetes físico
     - Actualmente: aceptación automática
  
  2. **Actualización de inventario**
     ```python
     inventario_divisa, created = InventarioDivisaTerminal.objects.get_or_create(
         terminal=terminal,
         divisa=divisa_origen
     )
     inventario_divisa.cantidad_disponible += monto_origen
     ```
  
  3. **Cambio de estado**
     ```python
     transaccion.estado = 'completado'
     
     HistorialTransaccion.objects.create(
         estado_anterior=estado_anterior,
         estado_nuevo='completado',
         observaciones='Depósito procesado en terminal X (TAUSER)'
     )
     ```
  
  4. **Registro en terminal**
     ```python
     RegistroTransaccionTerminal.objects.create(
         terminal=terminal,
         tipo_operacion='deposito',
         exitosa=True
     )
     ```
  
  5. **Limpieza de sesión**

### 4. **Resultado**
- ✅ Confirmación de depósito
- 💰 Información de monto recibido
- 🔙 Redirección a página principal

---

## 🛡️ Seguridad

### Variables de Sesión
```python
# Establecidas durante verificación
request.session['transaccion_tauser_id'] = transaccion_id
request.session['terminal_tauser_codigo'] = terminal_codigo
request.session['transaccion_mfa_verificada'] = True
```

### Validaciones en Cada Vista
1. ✅ **MFA verificado**: `request.session.get('transaccion_mfa_verificada')`
2. ✅ **ID de transacción coincide**: comparación con sesión
3. ✅ **Terminal activo**: `Terminal.is_activa=True`
4. ✅ **Estado correcto**: 
   - Retiro: `tipo='compra' AND estado='pagada'`
   - Depósito: `tipo='venta' AND estado IN ['pendiente', 'pagada']`

### Limpieza Automática
- `request.session.flush()` al completar transacción
- Previene reutilización de sesiones
- Elimina todos los datos sensibles

---

## 📊 Modelos Involucrados

### Actualización de Inventario
```
InventarioDivisaTerminal
├── terminal: FK -> Terminal
├── divisa: FK -> Divisa
└── cantidad_disponible: Decimal (actualizado en cada operación)

InventarioDenominacionTerminal
├── terminal: FK -> Terminal
├── denominacion: FK -> Denominacion
└── cantidad_disponible: Integer (decrementado en retiros)
```

### Registro de Operaciones
```
DesgloseDenominacionOperacion
├── terminal: FK -> Terminal
├── denominacion: FK -> Denominacion
├── cantidad: Integer
├── tipo_operacion: 'retiro' | 'deposito'
└── monto_operacion: Decimal

RegistroTransaccionTerminal
├── terminal: FK -> Terminal
├── transaccion: FK -> Transaccion
├── tipo_operacion: 'retiro' | 'deposito'
├── exitosa: Boolean
└── observaciones: Text
```

### Historial de Transacciones
```
HistorialTransaccion
├── transaccion: FK -> Transaccion
├── estado_anterior: 'pagada' | 'pendiente'
├── estado_nuevo: 'completado'
├── observaciones: "Retiro/Depósito procesado en terminal X (TAUSER)"
└── modificado_por: NULL (sistema TAUSER)
```

---

## 🧮 Algoritmo de Denominaciones

### Función Principal: `calcular_desglose_optimo`

```python
def calcular_desglose_optimo(inventarios, monto_solicitado):
    """
    Algoritmo greedy para calcular el desglose óptimo de denominaciones.
    Prioriza billetes de mayor valor para minimizar cantidad de billetes.
    
    Args:
        inventarios: QuerySet de InventarioDenominacionTerminal
        monto_solicitado: Decimal con el monto a desglosar
    
    Returns:
        {
            'posible': bool,
            'desglose': {
                'denom_id': {
                    'inventario': objeto,
                    'cantidad': int,
                    'valor': Decimal
                }
            },
            'sobrante': Decimal,
            'monto_cubierto': Decimal
        }
    """
```

### Estrategia Greedy
1. Ordenar denominaciones de mayor a menor valor
2. Para cada denominación:
   - Calcular cuántos billetes se necesitan
   - Limitar por stock disponible
   - Restar del monto pendiente
3. Verificar si se cubrió el monto completo

### Ejemplo
```python
# Solicitud: 150 USD
# Disponible: 100 (x2), 50 (x3), 20 (x5), 10 (x4)

# Resultado:
# - 1 x 100 USD = 100
# - 1 x 50 USD = 50
# Total: 150 USD (2 billetes)
```

---

## 🔧 Manejo de Errores

### Stock Insuficiente
```python
if not resultado['posible']:
    messages.error(
        f'No hay suficiente stock. '
        f'Disponible: {resultado["monto_cubierto"]}, '
        f'Solicitado: {monto_solicitado}'
    )
    return redirect('mostrar_detalle_retiro')
```

### Transacción Atómica
```python
try:
    with transaction.atomic():
        # Todas las operaciones
        # Si falla cualquiera, se revierte todo
except Exception as e:
    logger.error(f"Error: {e}")
    messages.error('Error al procesar')
    return redirect('detalle')
```

### Estados Inválidos
```python
# Retiro
if tipo != 'compra' or estado != 'pagada':
    messages.error('Transacción no puede ser procesada')
    return redirect('menu')

# Depósito  
if tipo != 'venta' or estado not in ['pendiente', 'pagada']:
    messages.error('Transacción no puede ser procesada')
    return redirect('menu')
```

---

## 📝 Logs Generados

### Formato
```python
logger.info(f"Retiro exitoso: Terminal {terminal.codigo}, Transacción {transaccion.id}")
logger.error(f"Error al procesar: {e}", exc_info=True)
```

### Eventos Registrados
- ✅ Inicio de procesamiento
- ✅ Cálculo de denominaciones
- ✅ Actualización de inventario
- ✅ Cambio de estado
- ❌ Errores de validación
- ❌ Excepciones durante procesamiento

---

## 🎯 Próximas Mejoras

### Task 6: Algoritmo con Backtracking
- Implementar búsqueda exhaustiva cuando greedy falla
- Optimizar para mínima cantidad de billetes
- Considerar múltiples combinaciones

### Task 7: Validación de Depósito
- Agregar input manual de denominaciones depositadas
- Validar contra denominaciones aceptadas
- Verificar sumas correctas

### Task 8: Panel de Limpieza
- Vista admin para archivar transacciones antiguas
- Filtros por fecha/estado/divisa
- Soft-delete o archivo en tabla separada

---

## 📚 Referencias

- **Vistas**: `tauser/views_external.py` (líneas 890-1046)
- **Servicios**: `tauser/services.py`
- **Templates**: `tauser/templates/tauser_external/`
- **Modelos**: `tauser/models.py`, `transacciones/models.py`
- **MFA Config**: `docs/TAUSER_MFA_CONFIG.md`

---

**Fecha de actualización**: $(date)
**Versión**: 1.0
**Estado**: ✅ Implementación completa de procesamiento básico
