# ✅ SOLUCIÓN: Pagos con Tarjeta Local en Historial del Banco

## 🎯 Problema Identificado

Los pagos automáticos con tarjetas locales se procesaban correctamente, pero **NO aparecían en el historial del banco** de la cuenta que recibía el pago (ej: cuenta empresa).

## 🔧 Cambios Realizados

### 1. Modelo `PagoTarjeta` (banco/models.py)

**Agregado nuevo campo**:
```python
cuenta_destino = models.ForeignKey(
    "Cuenta",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="pagos_recibidos_tarjeta",
    help_text="Cuenta que recibe el pago (ej: cuenta empresa para compras)"
)
```

**¿Por qué?**: Para rastrear dónde va el dinero y poder mostrar los pagos RECIBIDOS en el historial del destinatario.

### 2. Función `realizar_pago_tarjeta()` (transacciones/views.py)

**Modificado**:
```python
# Antes
pago = PagoTarjeta.objects.create(
    tarjeta_debito=tarjeta_debito,
    monto=monto_decimal
)

# Ahora
pago = PagoTarjeta.objects.create(
    tarjeta_debito=tarjeta_debito,
    monto=monto_decimal,
    cuenta_destino=cuenta_destino  # ✅ Guardar cuenta destino
)
```

**¿Por qué?**: Ahora cada pago registra la cuenta que recibe el dinero.

### 3. Vista `historial()` (banco/views.py)

**Antes**:
```python
# Solo mostraba pagos ENVIADOS por el usuario
pagos = PagoTarjeta.objects.filter(
    Q(tarjeta_debito__usuario=user) |
    Q(tarjeta_credito__usuario=user)
)
```

**Ahora**:
```python
# Pagos ENVIADOS por el usuario
pagos_enviados = PagoTarjeta.objects.filter(
    Q(tarjeta_debito__usuario=user) |
    Q(tarjeta_credito__usuario=user)
)

# ✅ Pagos con tarjeta RECIBIDOS en las cuentas del usuario
pagos_recibidos_tarjeta = PagoTarjeta.objects.filter(
    cuenta_destino__in=cuentas_usuario
).exclude(
    # Evitar duplicados
    Q(tarjeta_debito__usuario=user) | Q(tarjeta_credito__usuario=user)
)

# Unificar todos
movimientos = sorted(
    list(transferencias) + 
    list(pagos_enviados) + 
    list(pagos_recibidos_tarjeta) +  # ✅ NUEVO
    list(pagos_billetera),
    key=lambda x: x.fecha,
    reverse=True
)
```

**¿Por qué?**: Ahora el historial muestra TANTO los pagos que enviaste CON tu tarjeta, COMO los pagos que RECIBISTE en tus cuentas.

### 4. Migración de Base de Datos

✅ Creada: `banco/migrations/0003_pagotarjeta_cuenta_destino.py`
✅ Aplicada: Campo `cuenta_destino` agregado a la tabla `PagoTarjeta`

---

## 🧪 Cómo Verificar

### 1. Realizar una compra con tarjeta local

1. Inicia sesión como cliente
2. Ve a **Comprar Divisas**
3. Selecciona divisa y monto
4. Elige **"Tarjeta de Crédito/Débito Local"**
5. Completa datos de tarjeta
6. Confirma la operación

### 2. Verificar en el historial del CLIENTE

1. Ve a **Banco** → **Historial**
2. Deberías ver el pago **ENVIADO**:
   ```
   📤 Pago Débito ₲55,555 (****2222)
   Fecha: [fecha actual]
   ```

### 3. Verificar en el historial de la EMPRESA

1. Inicia sesión como usuario que tiene la cuenta empresa (000111222)
2. Ve a **Banco** → **Historial**
3. Deberías ver el pago **RECIBIDO**:
   ```
   📥 Pago Débito ₲55,555 (****2222)
   Fecha: [fecha actual]
   ```

---

## 📊 Tipos de Movimientos en el Historial

Ahora el historial del banco muestra:

| Tipo | Descripción | Icono |
|------|-------------|-------|
| **Transferencia Enviada** | Transferencia desde tu cuenta | 📤 |
| **Transferencia Recibida** | Transferencia a tu cuenta | 📥 |
| **Pago con Tarjeta Enviado** | Pago que hiciste con tu tarjeta | 💳📤 |
| **Pago con Tarjeta Recibido** | Pago que recibiste en tu cuenta | 💳📥 |
| **Pago desde Billetera Recibido** | Pago desde billetera a tu cuenta | 👛📥 |

---

## 🔍 Consultas SQL Útiles

### Ver pagos con tarjeta del día

```sql
-- Pagos con tarjeta (todos)
SELECT 
    p.id,
    p.fecha,
    p.monto,
    CASE 
        WHEN p.tarjeta_debito_id IS NOT NULL THEN 'Débito'
        ELSE 'Crédito'
    END as tipo,
    COALESCE(td.numero, tc.numero) as tarjeta,
    cd.numero_cuenta as cuenta_destino
FROM banco_pagotarjeta p
LEFT JOIN banco_tarjetadebito td ON p.tarjeta_debito_id = td.id
LEFT JOIN banco_tarjetacredito tc ON p.tarjeta_credito_id = tc.id
LEFT JOIN banco_cuenta cd ON p.cuenta_destino_id = cd.id
WHERE DATE(p.fecha) = CURRENT_DATE
ORDER BY p.fecha DESC;
```

### Ver pagos recibidos en cuenta empresa

```sql
-- Pagos recibidos en cuenta empresa (000111222)
SELECT 
    p.id,
    p.fecha,
    p.monto,
    p.comprobante,
    COALESCE(td.numero, tc.numero) as tarjeta_pagadora
FROM banco_pagotarjeta p
INNER JOIN banco_cuenta c ON p.cuenta_destino_id = c.id
LEFT JOIN banco_tarjetadebito td ON p.tarjeta_debito_id = td.id
LEFT JOIN banco_tarjetacredito tc ON p.tarjeta_credito_id = tc.id
WHERE c.numero_cuenta = '000111222'
ORDER BY p.fecha DESC
LIMIT 10;
```

### Ver todos los movimientos de una cuenta

```sql
-- Movimientos completos de cuenta 000111222
SELECT 
    'Transferencia Recibida' as tipo,
    t.fecha,
    t.monto,
    t.comprobante::text as comprobante
FROM banco_transferencia t
INNER JOIN banco_cuenta c ON t.cuenta_destino_id = c.id
WHERE c.numero_cuenta = '000111222'

UNION ALL

SELECT 
    'Pago Tarjeta Recibido' as tipo,
    p.fecha,
    p.monto,
    p.comprobante::text as comprobante
FROM banco_pagotarjeta p
INNER JOIN banco_cuenta c ON p.cuenta_destino_id = c.id
WHERE c.numero_cuenta = '000111222'

UNION ALL

SELECT 
    'Pago Billetera Recibido' as tipo,
    pb.fecha,
    pb.monto,
    pb.comprobante::text as comprobante
FROM billetera_pagobilletera pb
INNER JOIN banco_cuenta c ON pb.cuenta_destino_id = c.id
WHERE c.numero_cuenta = '000111222'

ORDER BY fecha DESC;
```

---

## 🐛 Troubleshooting

### Problema: Los pagos antiguos no tienen cuenta_destino

**Síntoma**: Pagos realizados antes de esta actualización tienen `cuenta_destino = NULL`.

**Solución**: Esto es normal. El campo es nullable. Los pagos antiguos solo aparecerán en el historial del que pagó (por su tarjeta), no del que recibió.

**Opción avanzada**: Puedes actualizar manualmente los pagos antiguos si sabes a qué cuenta fueron:
```sql
-- Actualizar pagos antiguos (CUIDADO: ajusta WHERE según necesidad)
UPDATE banco_pagotarjeta 
SET cuenta_destino_id = (
    SELECT id FROM banco_cuenta 
    WHERE numero_cuenta = '000111222' 
    LIMIT 1
)
WHERE cuenta_destino_id IS NULL
  AND fecha > '2024-01-01'  -- Solo pagos recientes
  AND billetera_id IS NULL;  -- Excluir recargas de billetera
```

### Problema: Aparecen pagos duplicados

**Síntoma**: El mismo pago aparece dos veces en el historial.

**Causa**: El usuario es tanto el que paga (con su tarjeta) como el que recibe (en su cuenta).

**Solución**: Ya implementada. El código excluye duplicados:
```python
pagos_recibidos_tarjeta = PagoTarjeta.objects.filter(
    cuenta_destino__in=cuentas_usuario
).exclude(
    # Evitar duplicados
    Q(tarjeta_debito__usuario=user) | Q(tarjeta_credito__usuario=user)
)
```

### Problema: No veo los pagos en el historial

**Verificación rápida**:
```python
from banco.models import PagoTarjeta, Cuenta

# Ver todos los pagos con tarjeta del día
pagos_hoy = PagoTarjeta.objects.filter(fecha__date=date.today())
print(f"Pagos hoy: {pagos_hoy.count()}")
for p in pagos_hoy:
    print(f"- Monto: ₲{p.monto}, Destino: {p.cuenta_destino}")

# Ver cuenta empresa
cuenta_emp = Cuenta.objects.get(numero_cuenta='000111222')
print(f"\nCuenta empresa saldo: ₲{cuenta_emp.saldo}")
print(f"Pagos recibidos: {cuenta_emp.pagos_recibidos_tarjeta.count()}")
```

---

## ✅ Checklist de Verificación

- [x] Campo `cuenta_destino` agregado a modelo `PagoTarjeta`
- [x] Migración creada y aplicada
- [x] Función `realizar_pago_tarjeta()` actualizada
- [x] Vista `historial()` actualizada para incluir pagos recibidos
- [x] Evitar duplicados en historial
- [x] Documentación actualizada

---

## 📚 Archivos Modificados

1. ✅ `banco/models.py` - Agregado campo `cuenta_destino`
2. ✅ `transacciones/views.py` - Actualizada función `realizar_pago_tarjeta()`
3. ✅ `banco/views.py` - Actualizada función `historial()`
4. ✅ `banco/migrations/0003_pagotarjeta_cuenta_destino.py` - Nueva migración

---

**Actualizado**: Octubre 2025  
**Versión**: 2.1  
**Para**: Global Exchange - Sistema de Pagos
