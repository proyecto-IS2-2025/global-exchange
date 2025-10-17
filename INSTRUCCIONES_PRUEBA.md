# 🎯 INSTRUCCIONES DE PRUEBA - Pago con Billetera Digital

## 📋 Preparación

### 1. Cargar Fixtures (si no están cargados)

```bash
# Cargar datos de billetera
python manage.py loaddata billetera/fixtures/billetera_data.json

# Cargar datos de banco (si es necesario)
python manage.py loaddata banco/fixtures/banco_data.json
```

### 2. Verificar Datos Existentes

```bash
python manage.py shell
```

```python
from billetera.models import UsuarioBilletera, Billetera
from banco.models import Cuenta, EntidadBancaria

# Verificar usuarios de billetera
usuarios = UsuarioBilletera.objects.all()
for u in usuarios:
    print(f"Usuario: {u.nombre} {u.apellido}, Tel: {u.numero_celular}")

# Verificar billeteras
billeteras = Billetera.objects.filter(activa=True)
for b in billeteras:
    print(f"Billetera {b.id}: {b.usuario.numero_celular}, Saldo: ₲{b.saldo}")

# Verificar cuenta empresa
cuenta_emp = Cuenta.objects.filter(numero_cuenta='000111222').first()
if cuenta_emp:
    print(f"Cuenta empresa: {cuenta_emp.numero_cuenta}, Saldo: ₲{cuenta_emp.saldo}")
```

## 🧪 Opción 1: Ejecutar Script de Tests Automáticos

### Paso 1: Ejecutar Tests

```bash
python manage.py shell < scripts/test_pago_billetera.py
```

### Paso 2: Verificar Resultados

El script ejecutará 5 tests:
1. ✅ Verificación de configuración básica
2. ✅ Pago exitoso
3. ✅ Pago con saldo insuficiente (error esperado)
4. ✅ Pago con billetera inexistente (error esperado)
5. ✅ Pago con datos incompletos (error esperado)

**Resultado esperado**: `5/5 tests exitosos 🎉`

## 🧪 Opción 2: Prueba Manual desde el Shell

### Paso 1: Abrir Shell de Django

```bash
python manage.py shell
```

### Paso 2: Importar Funciones

```python
from decimal import Decimal
from transacciones.views import realizar_pago_billetera
from billetera.models import Billetera
from banco.models import Cuenta
```

### Paso 3: Verificar Saldos Iniciales

```python
# Saldo billetera
billetera = Billetera.objects.get(usuario__numero_celular='0981111111', activa=True)
print(f"Saldo billetera: ₲{billetera.saldo:,.0f}")

# Saldo empresa
cuenta_emp = Cuenta.objects.get(numero_cuenta='000111222')
print(f"Saldo empresa: ₲{cuenta_emp.saldo:,.0f}")
```

### Paso 4: Ejecutar Pago de Prueba

```python
# Configurar datos del medio
medio_datos = {
    'tipo': 'Billetera Electrónica',
    'datos_campos': {
        'Teléfono de billetera': '0981111111',
        'Entidad': 'Banco Py'
    }
}

# Monto a pagar
monto = Decimal('50000.00')  # ₲50,000

# Ejecutar pago
resultado = realizar_pago_billetera(
    medio_datos=medio_datos,
    monto=monto,
    referencia='TEST-MANUAL-001'
)

# Ver resultado
print(f"\nResultado:")
print(f"  OK: {resultado['ok']}")
print(f"  Código: {resultado['code']}")
print(f"  Mensaje: {resultado['message']}")
if resultado['ok']:
    print(f"  Comprobante: {resultado['comprobante']}")
```

### Paso 5: Verificar Saldos Después

```python
# Refrescar datos
billetera.refresh_from_db()
cuenta_emp.refresh_from_db()

print(f"\nSaldo billetera después: ₲{billetera.saldo:,.0f}")
print(f"Saldo empresa después: ₲{cuenta_emp.saldo:,.0f}")
```

### Paso 6: Verificar Registro de Pago

```python
from billetera.models import PagoBilletera

pago = PagoBilletera.objects.filter(
    comprobante=resultado['comprobante']
).first()

if pago:
    print(f"\nPago registrado:")
    print(f"  ID: {pago.id}")
    print(f"  Monto: ₲{pago.monto:,.0f}")
    print(f"  Exitoso: {pago.exitoso}")
    print(f"  Fecha: {pago.fecha}")
```

## 🌐 Opción 3: Prueba desde la Interfaz Web

### Paso 1: Crear Medio de Pago (Admin)

1. Ir a: `http://localhost:8000/admin/`
2. Login como superusuario
3. Navegar a: **Medios de Pago > Medios de Pago**
4. Click en **Agregar Medio de Pago**
5. Completar:
   ```
   Nombre: Billetera Digital Test
   Tipo de Medio: Billetera Electrónica
   Comisión: 0
   Activo: ✓
   ```
6. Guardar

### Paso 2: Agregar Campos al Medio

1. En el mismo formulario, sección **Campos**
2. Agregar campo 1:
   ```
   Campo API: wallet_phone
   Requerido: ✓
   ```
3. Agregar campo 2:
   ```
   Campo API: bank_name
   Requerido: ✓
   ```
4. Guardar

### Paso 3: Asignar Medio a Cliente

1. Navegar a: **Clientes > Cliente Medio de Pago**
2. Click en **Agregar Cliente Medio de Pago**
3. Completar:
   ```
   Cliente: [Seleccionar un cliente existente]
   Medio de pago: Billetera Digital Test
   Es activo: ✓
   Datos campos:
   {
     "Teléfono de billetera": "0981111111",
     "Entidad": "Banco Py"
   }
   ```
4. Guardar

### Paso 4: Realizar Compra desde la Web

1. Login como cliente (o usar sesión de cajero)
2. Ir a: **Comprar Divisas**
3. Seleccionar:
   - Divisa: USD
   - Monto: 100 USD
4. Confirmar
5. En **Seleccionar Medio de Pago**:
   - Elegir: "Billetera Digital Test"
6. Click en **Confirmar Operación**

### Paso 5: Verificar Resultado

Deberías ver un mensaje:
```
✓ Pago exitoso desde billetera
  Comprobante: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  Transacción: TRX-YYYYMMDD-XXX (pagada)
```

## 🔍 Verificación de Resultados

### Verificar en Base de Datos

```sql
-- Ver últimos pagos de billetera
SELECT * FROM billetera_pagobilletera 
ORDER BY fecha DESC 
LIMIT 5;

-- Ver movimientos de billetera
SELECT * FROM billetera_movimientobilletera 
WHERE tipo = 'PAGO' 
ORDER BY fecha DESC 
LIMIT 5;

-- Ver transacciones pagadas
SELECT numero_transaccion, estado, monto_origen 
FROM transacciones_transaccion 
WHERE estado = 'pagada' 
ORDER BY fecha_creacion DESC 
LIMIT 5;
```

### Verificar en Admin

1. **Pagos de Billetera**: `/admin/billetera/pagobilletera/`
2. **Movimientos**: `/admin/billetera/movimientobilletera/`
3. **Transacciones**: `/admin/transacciones/transaccion/`

## 📊 Casos de Prueba Sugeridos

### ✅ Casos Exitosos

| # | Descripción | Teléfono | Monto | Resultado Esperado |
|---|-------------|----------|-------|-------------------|
| 1 | Pago normal | 0981111111 | ₲50,000 | Éxito |
| 2 | Pago mínimo | 0981111111 | ₲1,000 | Éxito |
| 3 | Pago grande | 0981111111 | ₲500,000 | Éxito (si hay saldo) |

### ❌ Casos de Error

| # | Descripción | Teléfono | Monto | Error Esperado |
|---|-------------|----------|-------|----------------|
| 1 | Saldo insuficiente | 0981111111 | ₲10,000,000 | Código 51 |
| 2 | Billetera no existe | 0999999999 | ₲50,000 | Código 14 |
| 3 | Sin teléfono | (vacío) | ₲50,000 | Código 12 |
| 4 | Billetera inactiva | 0982222222* | ₲50,000 | Código 14 |

*Si la billetera está marcada como `activa=False`

## 🐛 Solución de Problemas

### Error: "Módulo de billetera no disponible"

**Causa**: No se pueden importar los modelos de billetera

**Solución**:
```bash
# Verificar que la app está instalada
python manage.py shell -c "from billetera.models import Billetera"
```

### Error: "No se encontró número de teléfono"

**Causa**: El campo no está en `datos_campos` o tiene nombre diferente

**Solución**:
```python
# Verificar datos del medio
from clientes.models import ClienteMedioDePago
medio = ClienteMedioDePago.objects.get(id=X)
print(medio.datos_campos)
# Debe contener: "Teléfono de billetera" o "wallet_phone"
```

### Error: "Cuenta destino no encontrada"

**Causa**: No existe la cuenta empresa configurada

**Solución**:
```python
from banco.models import Cuenta, EntidadBancaria

# Verificar cuenta
cuenta = Cuenta.objects.filter(numero_cuenta='000111222').first()
if not cuenta:
    # Crear cuenta empresa
    entidad = EntidadBancaria.objects.get(codigo='BPY')
    # ... crear cuenta
```

## 📝 Logs para Debugging

### Ver Logs en Consola

Si ejecutas el servidor con:
```bash
python manage.py runserver
```

Los logs de pago aparecerán con el prefijo `[PAGO_BILLETERA]`:

```
[PAGO_BILLETERA] Iniciando pago desde billetera por monto=50000.00
[PAGO_BILLETERA] Número de teléfono encontrado: 0981111111
[PAGO_BILLETERA] Usuario billetera encontrado: Juan Pérez
[PAGO_BILLETERA] Billetera encontrada: Billetera 0981111111 - Banco Py
[PAGO_BILLETERA] Ejecutando pago: billetera=... -> cuenta=000111222 por ₲50,000.00
[PAGO_BILLETERA] Pago exitoso. Comprobante: abc123-...
```

### Filtrar Logs

```bash
# En desarrollo (si tienes logs en archivo)
grep "PAGO_BILLETERA" logs/debug.log

# En producción
tail -f logs/app.log | grep "PAGO_BILLETERA"
```

## ✅ Checklist de Verificación

Antes de probar, asegúrate de que:

- [ ] Fixtures de billetera cargados
- [ ] Existe UsuarioBilletera con tel: 0981111111
- [ ] Existe Billetera activa con saldo > ₲100,000
- [ ] Existe EntidadBancaria "Banco Py" (código BPY)
- [ ] Existe Cuenta empresa número 000111222
- [ ] Medio de pago tipo "billetera_electronica" creado
- [ ] Campos wallet_phone y bank_name configurados
- [ ] Medio asignado a cliente con datos completos

## 🎉 Resultado Esperado

Si todo está configurado correctamente:

1. ✅ Tests automáticos: `5/5 exitosos`
2. ✅ Prueba manual: Pago procesado, comprobante generado
3. ✅ Saldos actualizados correctamente
4. ✅ Registro en PagoBilletera creado
5. ✅ Movimiento en historial de billetera
6. ✅ Transacción marcada como "pagada"

---

**¡Listo para probar!** 🚀

Si tienes algún problema, revisa la documentación en:
- `docs/BILLETERA_DIGITAL_README.md`
- `docs/PAGO_BILLETERA_DIGITAL.md`
- `docs/CONFIGURACION_BILLETERA_DIGITAL.md`
