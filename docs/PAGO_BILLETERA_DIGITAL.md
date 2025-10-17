# Pago Automático con Billetera Digital

## Descripción General

Este documento describe la funcionalidad de pago automático con billetera digital para la compra de divisas, que funciona de manera similar al pago con cuenta bancaria local.

## Flujo de Operación

### 1. Selección de Medio de Pago

Cuando un cliente realiza una compra de divisas:

1. El cliente ingresa el monto y la divisa que desea comprar
2. El sistema calcula el total en guaraníes (PYG)
3. El cliente selecciona su medio de pago
4. Si el medio de pago es una **Billetera Digital**, el sistema identifica automáticamente el número de teléfono asociado

### 2. Confirmación de Operación

Al confirmar la operación:

1. El sistema verifica que el medio de pago sea de tipo "Billetera Electrónica"
2. Extrae el número de teléfono de la billetera desde los datos del medio de pago
3. Busca la billetera correspondiente en el sistema

### 3. Procesamiento del Pago

El pago se realiza automáticamente:

1. **Verificación de billetera**: Se busca el usuario de billetera por número de teléfono
2. **Validación de saldo**: Se verifica que la billetera tenga saldo suficiente
3. **Obtención de cuenta empresa**: Se obtiene la cuenta bancaria de destino (Global Exchange)
4. **Creación del pago**: Se crea un registro de `PagoBilletera` que automáticamente:
   - Debita el saldo de la billetera del cliente
   - Acredita el monto a la cuenta bancaria de la empresa
   - Crea un movimiento en el historial de la billetera
5. **Actualización de transacción**: La transacción se marca como "pagada"

## Implementación Técnica

### Modelos Involucrados

#### `billetera.Billetera`
- Almacena la información de la billetera digital
- Relacionada con `UsuarioBilletera` (identificado por número de teléfono)
- Relacionada con `EntidadBancaria` (el proveedor de la billetera)
- Campo `saldo`: monto disponible en la billetera

#### `billetera.PagoBilletera`
- Registra pagos desde billetera a cuentas bancarias
- Campos principales:
  - `billetera`: Billetera origen
  - `cuenta_destino`: Cuenta bancaria destino
  - `monto`: Monto del pago
  - `comprobante`: UUID único para identificar el pago
  - `exitoso`: Indica si el pago fue exitoso

#### `clientes.ClienteMedioDePago`
- Almacena la configuración del medio de pago del cliente
- Campo `datos_campos`: JSON con información como:
  - Número de teléfono de la billetera
  - Entidad bancaria (opcional)
  - Otros datos según configuración

### Función Principal

**`realizar_pago_billetera(medio_datos, monto, referencia)`**

Ubicación: `transacciones/views.py`

**Parámetros:**
- `medio_datos`: Diccionario con información del medio de pago
- `monto`: Monto a pagar en guaraníes
- `referencia`: Referencia de la transacción (opcional)

**Retorno:**
```python
{
    'ok': bool,           # Indica si el pago fue exitoso
    'code': str,          # Código de respuesta ('00' = éxito)
    'message': str,       # Mensaje descriptivo
    'comprobante': str    # UUID del comprobante (si exitoso)
}
```

**Proceso:**
1. Extrae el número de teléfono de `medio_datos['datos_campos']`
2. Busca el usuario de billetera por número de teléfono
3. Obtiene la billetera activa del usuario
4. Valida saldo suficiente
5. Obtiene la cuenta bancaria de la empresa
6. Crea el `PagoBilletera` (que ejecuta la transferencia automáticamente)
7. Retorna el resultado con el comprobante

### Integración en el Flujo de Compra

La integración se realiza en `crear_transaccion_desde_compra()`:

```python
# Después de crear la transacción
medio_datos = transaccion.get_medio_pago_info() or {}
tipo_medio = medio_datos.get('tipo', '').lower()

# Verificar si es billetera electrónica
if 'billetera' in tipo_medio or tipo_medio == 'billetera electrónica':
    resultado = realizar_pago_billetera(
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

Para que un medio de pago funcione como billetera digital:

1. **Tipo de medio**: Debe ser `billetera_electronica`
2. **Campos requeridos** en `datos_campos`:
   - `wallet_phone` o `Teléfono de billetera`: Número de teléfono asociado
   - `bank_name` o `Entidad` (opcional): Nombre de la entidad proveedora

### Ejemplo de configuración:

```json
{
  "datos_campos": {
    "Teléfono de billetera": "0981111111",
    "Entidad": "Banco Py",
    "Titular de la cuenta": "Juan Pérez"
  }
}
```

## Mensajes al Usuario

### Pago Exitoso
```
Pago exitoso desde billetera. Comprobante: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Errores Posibles

| Código | Mensaje | Causa |
|--------|---------|-------|
| 12 | Datos de billetera incompletos | Falta número de teléfono |
| 14 | No se encontró billetera con teléfono X | Usuario no existe o no tiene billetera |
| 51 | Saldo insuficiente en billetera | La billetera no tiene fondos suficientes |
| 96 | Error al procesar pago desde billetera | Error interno del sistema |

## Ventajas del Sistema

1. **Automatización**: El pago se procesa automáticamente sin intervención manual
2. **Consistencia**: Usa el mismo flujo que las transferencias bancarias
3. **Trazabilidad**: Cada pago genera un comprobante único
4. **Historial**: Los movimientos se registran en el historial de la billetera
5. **Validaciones**: Verifica saldo, cuenta destino y datos completos

## Ejemplo de Uso Completo

### Escenario: Cliente compra USD 100

1. **Cliente**: Juan Pérez (billetera 0981111111)
2. **Operación**: Comprar USD 100
3. **Cálculo**: USD 100 = ₲750,000 (según tasa del día)
4. **Medio de pago**: Billetera Digital Banco Py
5. **Proceso**:
   - Sistema identifica billetera por teléfono 0981111111
   - Verifica saldo: ₲1,500,000 disponibles ✓
   - Crea PagoBilletera:
     - Debita ₲750,000 de billetera de Juan
     - Acredita ₲750,000 a cuenta empresa
   - Genera comprobante: `abc123-def4-5678-90ab-cdef12345678`
   - Marca transacción como "pagada"
6. **Resultado**: 
   - Saldo billetera Juan: ₲750,000
   - Transacción completada exitosamente

## Consideraciones de Seguridad

1. **Atomicidad**: Toda la operación se ejecuta en una transacción de base de datos
2. **Validación de saldo**: Se verifica antes de procesar el pago
3. **Bloqueo de registros**: Uso de `select_for_update()` en operaciones críticas
4. **Logs detallados**: Cada paso del proceso se registra para auditoría
5. **Comprobantes únicos**: Cada pago genera un UUID único

## Mantenimiento y Soporte

### Logs
Los logs se generan con el prefijo `[PAGO_BILLETERA]` para facilitar el diagnóstico:

```python
logger.info(f"[PAGO_BILLETERA] Iniciando pago desde billetera por monto={monto}")
logger.debug(f"[PAGO_BILLETERA] Número de teléfono encontrado: {numero_telefono}")
logger.error(f"[PAGO_BILLETERA] Error al procesar pago: {e}")
```

### Debugging
Para depurar problemas:
1. Verificar que el medio de pago tenga `tipo_medio='billetera_electronica'`
2. Confirmar que `datos_campos` contenga el número de teléfono
3. Validar que exista el usuario de billetera y tenga billetera activa
4. Verificar saldo suficiente en la billetera
5. Confirmar que la cuenta empresa esté configurada correctamente

## Futuras Mejoras

- [ ] Soporte para múltiples billeteras por usuario
- [ ] Notificaciones push al realizar pagos
- [ ] Historial de pagos en la aplicación de billetera
- [ ] Límites de transacción por seguridad
- [ ] Autenticación adicional para montos altos
- [ ] Soporte para pagos parciales o diferidos
