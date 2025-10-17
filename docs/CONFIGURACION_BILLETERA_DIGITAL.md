# Guía de Configuración: Medio de Pago Billetera Digital

## 1. Crear Medio de Pago Base (Admin)

### Paso 1: Crear el Medio de Pago en Medios de Pago

1. Ir a **Admin > Medios de Pago > Medios de Pago**
2. Click en **Agregar Medio de Pago**
3. Configurar:
   - **Nombre**: "Billetera Digital Banco Py"
   - **Tipo de Medio**: "Billetera Electrónica"
   - **Comisión**: 0% (o según política)
   - **Activo**: ✓

### Paso 2: Agregar Campos del Medio

Después de crear el medio, agregar los siguientes campos:

#### Campo 1: Teléfono de Billetera
- **Campo API**: `wallet_phone`
- **Nombre del campo**: "Teléfono de billetera" (se autocompleta)
- **Tipo de dato**: "Teléfono" (se autocompleta)
- **Requerido**: ✓
- **Descripción**: "Número de teléfono asociado a la billetera"

#### Campo 2: Entidad Bancaria
- **Campo API**: `bank_name`
- **Nombre del campo**: "Entidad" (se autocompleta)
- **Tipo de dato**: "Texto" (se autocompleta)
- **Requerido**: ✓
- **Descripción**: "Nombre de la entidad financiera"

#### Campo 3: Titular (Opcional)
- **Campo API**: `account_holder`
- **Nombre del campo**: "Titular de la cuenta" (se autocompleta)
- **Tipo de dato**: "Texto" (se autocompleta)
- **Requerido**: No
- **Descripción**: "Nombre del titular de la cuenta"

## 2. Asignar Medio de Pago a Cliente

### Opción A: Desde el Admin

1. Ir a **Admin > Clientes > Cliente Medio de Pago**
2. Click en **Agregar Cliente Medio de Pago**
3. Configurar:
   - **Cliente**: Seleccionar cliente
   - **Medio de pago**: "Billetera Digital Banco Py"
   - **Es activo**: ✓
   - **Es principal**: (según preferencia)
   - **Datos campos**:
     ```json
     {
       "Teléfono de billetera": "0981111111",
       "Entidad": "Banco Py",
       "Titular de la cuenta": "Juan Pérez"
     }
     ```

### Opción B: Desde Fixture (JSON)

Crear archivo `cliente_billetera_fixture.json`:

```json
[
  {
    "model": "clientes.clientemediopago",
    "pk": 1,
    "fields": {
      "cliente": 1,
      "medio_de_pago": 1,
      "datos_campos": {
        "Teléfono de billetera": "0981111111",
        "Entidad": "Banco Py",
        "Titular de la cuenta": "Juan Pérez"
      },
      "es_activo": true,
      "es_principal": true,
      "fecha_creacion": "2025-01-15T10:00:00Z"
    }
  }
]
```

Cargar fixture:
```bash
python manage.py loaddata cliente_billetera_fixture.json
```

## 3. Datos Necesarios en el Sistema

### 3.1. Usuario de Billetera

Debe existir un `UsuarioBilletera` con el número de teléfono:

```json
{
  "model": "billetera.usuariobilletera",
  "pk": 1,
  "fields": {
    "numero_celular": "0981111111",
    "password": "1234",
    "nombre": "Juan",
    "apellido": "Pérez"
  }
}
```

### 3.2. Billetera Activa

Debe existir una `Billetera` activa asociada al usuario:

```json
{
  "model": "billetera.billetera",
  "pk": 1,
  "fields": {
    "usuario": 1,
    "entidad": 1,
    "saldo": "1500000.00",
    "activa": true
  }
}
```

### 3.3. Cuenta Empresa (Destino)

Debe estar configurada la cuenta bancaria de la empresa:

```python
# En transacciones/views.py
EMPRESA_BANCO_NOMBRE = "Banco Py"
EMPRESA_BANCO_CODIGO = "BPY"
EMPRESA_NUMERO_CUENTA = "000111222"
```

## 4. Verificación de Configuración

### Checklist de Configuración

- [ ] Medio de pago creado con tipo "Billetera Electrónica"
- [ ] Campo `wallet_phone` agregado y marcado como requerido
- [ ] Campo `bank_name` agregado
- [ ] Medio asignado al cliente con datos completos
- [ ] Número de teléfono existe en `UsuarioBilletera`
- [ ] Billetera activa con saldo suficiente
- [ ] Cuenta empresa configurada correctamente

### Comando de Verificación

Ejecutar en el shell de Django:

```python
python manage.py shell
```

```python
from clientes.models import ClienteMedioDePago
from billetera.models import UsuarioBilletera, Billetera

# Verificar medio de pago del cliente
medio = ClienteMedioDePago.objects.get(id=1)
print(f"Medio: {medio.medio_de_pago.nombre}")
print(f"Tipo: {medio.medio_de_pago.tipo_medio}")
print(f"Datos: {medio.datos_campos}")

# Verificar billetera
telefono = medio.datos_campos.get('Teléfono de billetera')
usuario = UsuarioBilletera.objects.get(numero_celular=telefono)
billetera = Billetera.objects.get(usuario=usuario, activa=True)
print(f"Billetera: {billetera}")
print(f"Saldo: ₲{billetera.saldo}")
```

## 5. Ejemplo de Uso en Compra

### Flujo Completo

1. **Cliente inicia compra**:
   - Selecciona divisa: USD
   - Monto: 100 USD
   - Sistema calcula: ₲750,000

2. **Selección de medio de pago**:
   - Cliente selecciona: "Billetera Digital Banco Py"
   - Sistema muestra datos:
     ```
     Nombre: Billetera Digital Banco Py
     Tipo: Billetera Electrónica
     Teléfono: 0981111111
     Entidad: Banco Py
     ```

3. **Confirmación**:
   - Cliente confirma operación
   - Sistema procesa pago automático:
     - Identifica billetera por teléfono 0981111111
     - Verifica saldo: ₲1,500,000 ✓
     - Debita ₲750,000 de billetera
     - Acredita ₲750,000 a cuenta empresa
     - Genera comprobante

4. **Resultado**:
   ```
   ✓ Pago exitoso desde billetera
   Comprobante: abc123-def4-5678-90ab-cdef12345678
   Transacción: TRX-20250115-001 (pagada)
   ```

## 6. Campos Alternativos Soportados

El sistema busca el número de teléfono en cualquiera de estos campos:

- `wallet_phone` ✓ (recomendado)
- `Teléfono de billetera`
- `phone`
- `telefono`
- `celular`
- `movil`

El sistema busca la entidad en cualquiera de estos campos:

- `bank_name` ✓ (recomendado)
- `Entidad`
- `banco`
- `bank`

### Ejemplo con Nombres Alternativos:

```json
{
  "datos_campos": {
    "phone": "0981111111",
    "banco": "Banco Py"
  }
}
```

También funcionará correctamente.

## 7. Solución de Problemas

### Error: "No se encontró número de teléfono"

**Causa**: Campo de teléfono no configurado o con nombre incorrecto

**Solución**:
1. Verificar que `datos_campos` contenga el número
2. Usar uno de los nombres soportados (preferiblemente `wallet_phone`)
3. Verificar que el valor no esté vacío

### Error: "No se encontró billetera con teléfono X"

**Causa**: No existe usuario de billetera con ese número

**Solución**:
1. Crear `UsuarioBilletera` con el número correcto
2. Verificar que el número no tenga espacios o caracteres extra
3. Crear la billetera asociada al usuario

### Error: "Saldo insuficiente en billetera"

**Causa**: La billetera no tiene fondos suficientes

**Solución**:
1. Recargar la billetera desde el módulo de billetera
2. Verificar el saldo antes de realizar la compra
3. El cliente debe fondear su billetera

### Error: "Cuenta destino no encontrada"

**Causa**: Cuenta empresa no configurada

**Solución**:
1. Verificar constantes en `transacciones/views.py`
2. Crear cuenta bancaria de empresa si no existe
3. Verificar que la entidad "Banco Py" exista

## 8. Migración de Datos Existentes

Si tienes clientes con medios de pago tipo "transferencia bancaria local" y quieres migrarlos a billetera:

```python
from clientes.models import ClienteMedioDePago
from medios_pago.models import MedioDePago

# Obtener medio de billetera
medio_billetera = MedioDePago.objects.get(
    nombre="Billetera Digital Banco Py"
)

# Actualizar medios existentes
for cliente_medio in ClienteMedioDePago.objects.filter(
    medio_de_pago__tipo_medio='bank_local'
):
    # Si tiene número de teléfono en los datos
    if 'phone' in cliente_medio.datos_campos:
        cliente_medio.medio_de_pago = medio_billetera
        cliente_medio.save()
        print(f"Migrado: {cliente_medio.cliente.nombre_completo}")
```

## 9. Testing

### Script de Prueba

```python
from decimal import Decimal
from transacciones.views import realizar_pago_billetera

# Datos de prueba
medio_datos = {
    'tipo': 'Billetera Electrónica',
    'datos_campos': {
        'Teléfono de billetera': '0981111111',
        'Entidad': 'Banco Py'
    }
}

monto = Decimal('750000.00')
referencia = 'TEST-001'

# Ejecutar pago
resultado = realizar_pago_billetera(medio_datos, monto, referencia)

# Verificar resultado
if resultado['ok']:
    print(f"✓ Pago exitoso")
    print(f"Comprobante: {resultado['comprobante']}")
else:
    print(f"✗ Error: {resultado['message']}")
    print(f"Código: {resultado['code']}")
```

## 10. Seguridad y Mejores Prácticas

1. **Validar número de teléfono**: Asegurar formato correcto (10 dígitos)
2. **Verificar saldo antes**: Mostrar saldo disponible al cliente
3. **Límites de transacción**: Implementar límites diarios/mensuales
4. **Auditoría**: Revisar logs regularmente
5. **Notificaciones**: Enviar SMS/email al procesar pagos
6. **Timeout**: Establecer timeout para pagos pendientes
7. **Rollback**: Asegurar atomicidad en caso de error

## 11. Monitoreo

### Queries Útiles

```sql
-- Pagos de billetera del día
SELECT * FROM billetera_pagobilletera 
WHERE DATE(fecha) = CURRENT_DATE
ORDER BY fecha DESC;

-- Transacciones pagadas con billetera
SELECT t.numero_transaccion, t.monto_origen, t.estado, p.comprobante
FROM transacciones_transaccion t
JOIN billetera_pagobilletera p ON t.medio_pago_datos->>'tipo' = 'Billetera Electrónica'
WHERE t.estado = 'pagada'
AND DATE(t.fecha_creacion) = CURRENT_DATE;

-- Saldo total en billeteras
SELECT SUM(saldo) as saldo_total
FROM billetera_billetera
WHERE activa = true;
```

### Métricas Recomendadas

- Total de pagos con billetera por día/mes
- Monto promedio de transacciones
- Tasa de éxito vs error
- Tiempo promedio de procesamiento
- Billeteras con saldo bajo
