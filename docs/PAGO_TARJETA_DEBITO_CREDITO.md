# Pago Automático con Tarjeta de Débito/Crédito

## Descripción General

Este documento describe la funcionalidad de **pago automático con tarjeta de débito/crédito** para la compra de divisas, que funciona de manera similar al pago con billetera digital y cuenta bancaria.

## ⚠️ Importante: Diferencia con Stripe

Esta funcionalidad procesa pagos con tarjetas que **NO son procesadas por Stripe**. Se utiliza para tarjetas registradas en el módulo de banco local del sistema.

- ✅ **Usa esta funcionalidad**: Tarjetas registradas en el banco local (módulo `banco`)
- ❌ **NO usa esta funcionalidad**: Tarjetas procesadas por Stripe (usa el flujo de Stripe)

El sistema detecta automáticamente si la entidad es "Stripe" y redirige al procesador correspondiente.

## Flujo de Operación

### 1. Selección de Medio de Pago

Cuando un cliente realiza una compra de divisas:

1. El cliente ingresa el monto y la divisa que desea comprar
2. El sistema calcula el total en guaraníes (PYG)
3. El cliente selecciona su medio de pago
4. Si el medio de pago es una **Tarjeta de Crédito/Débito** (no Stripe), el sistema identifica la tarjeta por sus datos

### 2. Confirmación de Operación

Al confirmar la operación, el sistema:

1. Verifica que el medio de pago sea de tipo "Tarjeta de Crédito/Débito"
2. Verifica que la entidad NO sea "Stripe"
3. Extrae los datos de la tarjeta:
   - Número de tarjeta
   - Mes de vencimiento
   - Año de vencimiento
   - CVV/CVC
   - Entidad bancaria (opcional)

### 3. Procesamiento del Pago

El pago se realiza automáticamente:

1. **Búsqueda de tarjeta**: Se busca la tarjeta en el sistema por todos sus datos
   - Primero busca en tarjetas de débito
   - Si no encuentra, busca en tarjetas de crédito
   - Coincidencia exacta: número, mes, año, CVV (y opcionalmente entidad)

2. **Validación de fondos**:
   - **Débito**: Verifica saldo en cuenta asociada
   - **Crédito**: Verifica límite de crédito disponible

3. **Creación del pago**: Se crea un registro de `PagoTarjeta` que automáticamente:
   - **Si es débito**: Debita el saldo de la cuenta asociada
   - **Si es crédito**: Consume del límite de crédito
   - Acredita el monto a la cuenta bancaria de la empresa
   - Genera comprobante único (UUID)

4. **Actualización de transacción**: La transacción se marca como "pagada"

## Implementación Técnica

### Modelos Involucrados

#### `banco.TarjetaDebito`
- Almacena información de tarjetas de débito
- Relacionada con `Cuenta` (1:1)
- Campos de validación:
  - `numero`: Número de 16 dígitos
  - `mes_vencimiento`: Mes (1-12)
  - `anho_vencimiento`: Año
  - `cvv`: Código de seguridad (3 dígitos)
  - `entidad`: Banco emisor

#### `banco.TarjetaCredito`
- Almacena información de tarjetas de crédito
- Campos similares a TarjetaDebito
- Adicionales:
  - `limite_credito`: Límite máximo
  - `saldo_usado`: Crédito consumido
  - Método `disponible()`: Calcula crédito disponible

#### `banco.PagoTarjeta`
- Registra pagos con tarjeta
- Campos principales:
  - `tarjeta_debito`: Tarjeta de débito usada (opcional)
  - `tarjeta_credito`: Tarjeta de crédito usada (opcional)
  - `monto`: Monto del pago
  - `comprobante`: UUID único
  - `fecha`: Timestamp del pago

**Importante**: Solo puede tener `tarjeta_debito` O `tarjeta_credito`, no ambas.

#### `clientes.ClienteMedioDePago`
- Almacena la configuración del medio de pago del cliente
- Campo `datos_campos`: JSON con información de la tarjeta:
  - Número de tarjeta
  - Mes de vencimiento
  - Año de vencimiento
  - CVV
  - Entidad (opcional)

### Función Principal

**`realizar_pago_tarjeta(medio_datos, monto, referencia)`**

Ubicación: `transacciones/views.py`

**Parámetros:**
- `medio_datos`: Diccionario con información del medio de pago
- `monto`: Monto a pagar en guaraníes
- `referencia`: Referencia de la transacción (opcional)

**Retorno:**
```python
{
    'ok': bool,              # Indica si el pago fue exitoso
    'code': str,             # Código de respuesta ('00' = éxito)
    'message': str,          # Mensaje descriptivo
    'comprobante': str,      # UUID del comprobante (si exitoso)
    'tipo_tarjeta': str      # 'débito' o 'crédito'
}
```

**Proceso:**
1. Extrae datos de tarjeta de `medio_datos['datos_campos']`
2. Busca tarjeta de débito con esos datos exactos
3. Si no encuentra, busca tarjeta de crédito
4. Valida fondos/crédito disponible
5. Obtiene cuenta bancaria de la empresa
6. Crea `PagoTarjeta` (automáticamente debita/consume crédito)
7. Acredita manualmente a cuenta empresa
8. Retorna resultado con comprobante

### Integración en el Flujo de Compra

La integración se realiza en `crear_transaccion_desde_compra()`:

```python
# Después de crear la transacción
medio_datos = transaccion.get_medio_pago_info() or {}
tipo_medio = medio_datos.get('tipo', '').lower()

# Verificar si es tarjeta (pero NO Stripe)
if ('tarjeta' in tipo_medio or 'crédito' in tipo_medio or 'débito' in tipo_medio) 
   and 'stripe' not in tipo_medio:
    
    resultado = realizar_pago_tarjeta(
        medio_datos=medio_datos,
        monto=transaccion.monto_origen,
        referencia=transaccion.numero_transaccion
    )
    
    if resultado.get('ok'):
        # Marcar transacción como pagada
        transaccion.cambiar_estado('pagada', ...)
    else:
        # Manejar error
        ...
```

## Configuración de Medio de Pago

Para que un medio de pago funcione como tarjeta local:

1. **Tipo de medio**: NO debe ser `stripe`
2. **Nombre**: Debe contener "Tarjeta", "Crédito" o "Débito"
3. **Campos requeridos** en `datos_campos`:
   - `card_number` o `Número de tarjeta`: Número completo (16 dígitos)
   - `exp_month` o `Mes de vencimiento`: Mes (1-12)
   - `exp_year` o `Año de vencimiento`: Año (4 dígitos)
   - `cvc` o `CVV`: Código de seguridad (3 dígitos)
   - `Entidad` (opcional): Nombre del banco emisor

### Ejemplo de configuración:

```json
{
  "datos_campos": {
    "Número de tarjeta": "4111111111111111",
    "Mes de vencimiento": "12",
    "Año de vencimiento": "2027",
    "Código de seguridad": "123",
    "Entidad": "Banco Nacional"
  }
}
```

## Mensajes al Usuario

### Pago Exitoso (Débito)
```
✓ Pago exitoso con tarjeta de débito
  Comprobante: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Pago Exitoso (Crédito)
```
✓ Pago exitoso con tarjeta de crédito
  Comprobante: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Errores Posibles

| Código | Mensaje | Causa |
|--------|---------|-------|
| 12 | Datos de tarjeta incompletos | Faltan datos requeridos (número, vencimiento, CVV) |
| 14 | No se encontró tarjeta con los datos proporcionados | Los datos no coinciden con ninguna tarjeta registrada |
| 51 | Saldo insuficiente en cuenta | Débito sin fondos suficientes |
| 51 | Límite de crédito excedido | Crédito sin cupo disponible |
| 96 | Error al procesar pago con tarjeta | Error interno del sistema |

## Ventajas del Sistema

1. **Automatización**: El pago se procesa automáticamente sin intervención manual
2. **Seguridad**: Validación completa de datos de tarjeta
3. **Flexibilidad**: Soporta tanto débito como crédito
4. **Trazabilidad**: Cada pago genera un comprobante único
5. **Consistencia**: Usa el mismo flujo que billeteras y transferencias
6. **No dependencia**: No requiere servicios externos como Stripe

## Ejemplo de Uso Completo

### Escenario: Cliente compra USD 100 con tarjeta de débito

1. **Cliente**: María López
2. **Tarjeta**: Débito 4111-1111-1111-1111 (Banco Nacional)
3. **Operación**: Comprar USD 100
4. **Cálculo**: USD 100 = ₲750,000 (según tasa del día)
5. **Proceso**:
   - Sistema identifica tarjeta por número, vencimiento y CVV
   - Verifica cuenta asociada tenga saldo ✓
   - Crea PagoTarjeta:
     - Debita ₲750,000 de cuenta de María
     - Acredita ₲750,000 a cuenta empresa
   - Genera comprobante: `def456-ghi7-8901-23jk-lmno45678901`
   - Marca transacción como "pagada"
6. **Resultado**: 
   - Saldo cuenta María: reducido en ₲750,000
   - Transacción completada exitosamente

### Escenario: Cliente compra USD 200 con tarjeta de crédito

1. **Cliente**: Juan Pérez
2. **Tarjeta**: Crédito 5555-5555-5555-4444 (Banco Py)
3. **Límite**: ₲2,000,000 | Usado: ₲500,000 | Disponible: ₲1,500,000
4. **Operación**: Comprar USD 200
5. **Cálculo**: USD 200 = ₲1,500,000
6. **Proceso**:
   - Sistema identifica tarjeta
   - Verifica crédito disponible: ₲1,500,000 ≥ ₲1,500,000 ✓
   - Crea PagoTarjeta:
     - Consume ₲1,500,000 de límite de crédito
     - Acredita ₲1,500,000 a cuenta empresa
   - Genera comprobante
   - Marca transacción como "pagada"
7. **Resultado**:
   - Crédito usado Juan: ₲500,000 → ₲2,000,000
   - Crédito disponible: ₲0
   - Transacción completada

## Diferencias con Otros Métodos

### vs Billetera Digital

| Aspecto | Tarjeta | Billetera |
|---------|---------|-----------|
| Identificación | Número + Vencimiento + CVV | Número de teléfono |
| Fondos | Cuenta bancaria / Crédito | Saldo en billetera |
| Límites | Saldo cuenta / Límite crédito | Saldo billetera |
| Modelo de pago | PagoTarjeta | PagoBilletera |

### vs Transferencia Bancaria

| Aspecto | Tarjeta | Transferencia |
|---------|---------|---------------|
| Datos requeridos | Número + Venc. + CVV + Entidad | Número cuenta + Entidad |
| Origen fondos | Cuenta asociada / Crédito | Cuenta directa |
| Tipo de búsqueda | Coincidencia exacta múltiple | Cuenta por número |
| Validación | Tarjeta debe existir | Cuenta debe existir |

### vs Stripe

| Aspecto | Tarjeta Local | Stripe |
|---------|---------------|--------|
| Procesador | Interno (módulo banco) | API externa (Stripe) |
| Tarjetas | Registradas localmente | Cualquier tarjeta válida |
| Validación | Búsqueda en BD local | Validación Stripe |
| Comisiones | Sin comisiones externas | Comisiones Stripe |
| Internet | No requiere | Requiere conexión |

## Consideraciones de Seguridad

1. **Validación completa**: Todos los datos deben coincidir exactamente
2. **Atomicidad**: Toda la operación en transacción de BD
3. **Fondos verificados**: Validación antes de procesar
4. **Logs detallados**: Cada paso registrado con prefijo `[PAGO_TARJETA]`
5. **Datos sensibles**: Solo últimos 4 dígitos en logs
6. **Comprobantes únicos**: UUID para cada transacción

## Mantenimiento y Soporte

### Logs

Los logs se generan con el prefijo `[PAGO_TARJETA]`:

```python
logger.info(f"[PAGO_TARJETA] Iniciando pago desde tarjeta por monto={monto}")
logger.debug(f"[PAGO_TARJETA] Número de tarjeta encontrado: {numero_tarjeta[-4:]}")
logger.error(f"[PAGO_TARJETA] Error al procesar pago: {e}")
```

### Debugging

Para depurar problemas:

1. Verificar que el medio tenga tipo que contenga "tarjeta", "crédito" o "débito"
2. Verificar que NO contenga "stripe" en el tipo
3. Confirmar que `datos_campos` contenga todos los datos requeridos
4. Validar que exista la tarjeta en el sistema con datos exactos
5. Verificar fondos/crédito disponible
6. Confirmar que la cuenta empresa esté configurada

### Queries SQL Útiles

```sql
-- Ver tarjetas registradas
SELECT 'Débito' as tipo, numero, entidad_id, mes_vencimiento, anho_vencimiento
FROM banco_tarjetadebito
UNION ALL
SELECT 'Crédito' as tipo, numero, entidad_id, mes_vencimiento, anho_vencimiento
FROM banco_tarjetacredito;

-- Pagos del día con tarjeta
SELECT * FROM banco_pagotarjeta
WHERE DATE(fecha) = CURRENT_DATE
ORDER BY fecha DESC;

-- Verificar tarjeta específica
SELECT * FROM banco_tarjetadebito
WHERE numero = '4111111111111111'
AND mes_vencimiento = 12
AND anho_vencimiento = 2027
AND cvv = '123';
```

## Futuras Mejoras

- [ ] Soporte para cuotas en tarjetas de crédito
- [ ] Validación adicional de fecha de expiración
- [ ] Bloqueo temporal por intentos fallidos
- [ ] Notificaciones de pagos realizados
- [ ] Historial detallado por tarjeta
- [ ] Límites de transacción por seguridad
- [ ] Integración con 3D Secure para seguridad adicional

## Troubleshooting

### Error: "No se encontró tarjeta con los datos proporcionados"

**Causa**: Los datos no coinciden exactamente con ninguna tarjeta

**Solución**:
1. Verificar que la tarjeta esté registrada en el sistema
2. Comprobar que todos los datos coincidan exactamente:
   - Número completo (sin espacios ni guiones)
   - Mes y año correctos
   - CVV exacto
3. Si hay entidad, verificar que coincida

### Error: "Saldo insuficiente en cuenta"

**Causa**: Tarjeta de débito sin fondos

**Solución**:
1. Verificar saldo en cuenta asociada
2. Cliente debe fondear su cuenta bancaria
3. Alternativamente, usar tarjeta de crédito

### Error: "Límite de crédito excedido"

**Causa**: Tarjeta de crédito sin cupo disponible

**Solución**:
1. Verificar límite de crédito y saldo usado
2. Cliente debe pagar cuota o solicitar aumento de límite
3. Alternativamente, usar otro medio de pago

---

**Fecha de implementación**: Octubre 2025  
**Versión**: 1.0  
**Compatible con**: Billetera Digital, Transferencias Bancarias, Stripe
