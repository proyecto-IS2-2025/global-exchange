# ✅ CORRECCIÓN: Visualización de Pagos con Tarjeta en Historial

## 🎯 Problema Identificado

Los pagos **recibidos** con tarjeta local en la cuenta empresa se mostraban en ROJO con signo negativo (-), cuando deberían mostrarse en VERDE con signo positivo (+) porque son ingresos.

### Ejemplo del Problema

```
Cuenta Empresa - Historial
--------------------------
❌ - ₲100,000  | Pago con Débito (****1111)  [INCORRECTO - Es un ingreso!]
```

### Causa Raíz

La plantilla `banco/templates/banco/historial.html` tenía una lógica simplificada que asumía que TODOS los `PagoTarjeta` eran egresos:

```django
{% else %}
  {# PagoTarjeta o RecargaBilletera - siempre es egreso #}
  <span class="text-danger">- ₲ {{ m.monto }}</span>
{% endif %}
```

Esto funcionaba cuando solo se mostraban los pagos **enviados** con tu propia tarjeta, pero ahora que también mostramos pagos **recibidos** en tus cuentas, necesitamos diferenciarlos.

---

## ✅ Solución Implementada

### 1. Lógica de Visualización de Montos

Se actualizó la lógica para distinguir entre pagos enviados y recibidos:

```django
{% elif m.tarjeta_debito or m.tarjeta_credito %}
  {# PagoTarjeta - verificar si es enviado o recibido #}
  {% if m.tarjeta_debito and m.tarjeta_debito.usuario.id == user.id %}
    {# Pago ENVIADO con mi tarjeta de débito → Egreso #}
    <span class="text-danger">- ₲ {{ m.monto }}</span>
  {% elif m.tarjeta_credito and m.tarjeta_credito.usuario.id == user.id %}
    {# Pago ENVIADO con mi tarjeta de crédito → Egreso #}
    <span class="text-danger">- ₲ {{ m.monto }}</span>
  {% else %}
    {# Pago RECIBIDO en mi cuenta → Ingreso #}
    <span class="text-success">+ ₲ {{ m.monto }}</span>
  {% endif %}
{% endif %}
```

**Lógica**:
- Si la tarjeta pertenece al usuario actual (`m.tarjeta_debito.usuario.id == user.id`) → Es un **egreso** (rojo, -)
- Si la tarjeta NO pertenece al usuario actual → Es un **ingreso** (verde, +)

### 2. Descripción Mejorada

También se actualizó la descripción para que sea más clara:

```django
{% elif m.tarjeta_debito and not m.billetera %}
  {# PagoTarjeta con débito #}
  {% if m.tarjeta_debito.usuario.id == user.id %}
    Pago con Débito (****{{ m.tarjeta_debito.numero|slice:"-4:" }})
  {% else %}
    Pago recibido de Débito (****{{ m.tarjeta_debito.numero|slice:"-4:" }})
  {% endif %}
{% elif m.tarjeta_credito %}
  {# PagoTarjeta con crédito #}
  {% if m.tarjeta_credito.usuario.id == user.id %}
    Pago con Crédito (****{{ m.tarjeta_credito.numero|slice:"-4:" }})
  {% else %}
    Pago recibido de Crédito (****{{ m.tarjeta_credito.numero|slice:"-4:" }})
  {% endif %}
{% endif %}
```

---

## 🎨 Visualización Correcta

### Para el Cliente (que paga)

```
Tu Historial - Cuenta 000555666
--------------------------------
📤 - ₲100,000  | Pago con Débito (****1111)
```
- **Rojo** (egreso)
- **Signo negativo** (-)
- Descripción: "Pago con Débito"

### Para la Empresa (que recibe)

```
Cuenta Empresa - Cuenta 000111222
----------------------------------
📥 + ₲100,000  | Pago recibido de Débito (****1111)
```
- **Verde** (ingreso)
- **Signo positivo** (+)
- Descripción: "Pago recibido de Débito"

---

## 📊 Matriz de Visualización

| Tipo de Movimiento | Usuario que ve | Color | Signo | Descripción |
|-------------------|---------------|-------|-------|-------------|
| **Pago con tarjeta propia** | Dueño de la tarjeta | 🔴 Rojo | - | "Pago con Débito/Crédito (****1234)" |
| **Pago recibido en cuenta** | Dueño de la cuenta destino | 🟢 Verde | + | "Pago recibido de Débito/Crédito (****1234)" |
| **Transferencia enviada** | Emisor | 🔴 Rojo | - | "Transferencia a cuenta X" |
| **Transferencia recibida** | Receptor | 🟢 Verde | + | "Transferencia de cuenta X" |
| **Pago billetera recibido** | Receptor | 🟢 Verde | + | "Pago recibido desde billetera" |

---

## 🧪 Cómo Verificar

### 1. Como Cliente (que paga)

1. Inicia sesión con tu cuenta de cliente
2. Ve a **Banco** → **Historial**
3. Busca tu pago con tarjeta
4. Debe aparecer:
   - ✅ En **ROJO** con signo **negativo** (-)
   - ✅ Descripción: "Pago con Débito (****1111)"

### 2. Como Empresa (que recibe)

1. Inicia sesión con cuenta que tiene acceso a cuenta empresa
2. Ve a **Banco** → **Historial**
3. Busca el pago recibido
4. Debe aparecer:
   - ✅ En **VERDE** con signo **positivo** (+)
   - ✅ Descripción: "Pago recibido de Débito (****1111)"

---

## 🔍 Ejemplo Práctico

### Antes de la Corrección ❌

**Cliente (cuenta 000555666)**:
```
- ₲100,000  | Pago con Débito (****1111)  ✅ Correcto (es egreso)
```

**Empresa (cuenta 000111222)**:
```
- ₲100,000  | Pago con Débito (****1111)  ❌ INCORRECTO! (debería ser ingreso)
```

### Después de la Corrección ✅

**Cliente (cuenta 000555666)**:
```
- ₲100,000  | Pago con Débito (****1111)  ✅ Correcto (es egreso)
```

**Empresa (cuenta 000111222)**:
```
+ ₲100,000  | Pago recibido de Débito (****1111)  ✅ Correcto (es ingreso)
```

---

## 🐛 Casos Especiales

### Caso 1: Usuario paga a su propia cuenta

Si un usuario tiene una tarjeta y esa tarjeta hace un pago a una cuenta que también le pertenece:

- En el historial aparecerá **2 veces**:
  1. Como **egreso** (por la tarjeta): Rojo (-)
  2. Como **ingreso** (por la cuenta destino): Verde (+)

Esto es correcto porque técnicamente son dos movimientos diferentes.

### Caso 2: Cuenta empresa = Cuenta de la tarjeta

Si la tarjeta pertenece a la misma cuenta empresa (como en nuestro test inicial), el pago aparecerá como **egreso** porque el usuario es dueño de la tarjeta.

---

## 📝 Archivos Modificados

1. ✅ `banco/templates/banco/historial.html`
   - Actualizada lógica de visualización de montos
   - Actualizada descripción de pagos recibidos

---

## ✅ Checklist de Verificación

- [x] Pagos enviados (con tu tarjeta) se muestran en ROJO (-)
- [x] Pagos recibidos (en tu cuenta) se muestran en VERDE (+)
- [x] Descripción diferencia entre "Pago con" y "Pago recibido de"
- [x] Transferencias funcionan igual que antes
- [x] Pagos desde billetera funcionan igual que antes
- [x] No hay duplicados innecesarios

---

**Actualizado**: Octubre 2025  
**Versión**: 2.2  
**Para**: Global Exchange - Sistema de Pagos
