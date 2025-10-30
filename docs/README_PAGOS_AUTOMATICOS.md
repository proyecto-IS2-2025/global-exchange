# 💳 Pagos Automáticos - Billetera Digital y Tarjetas

## 📖 Índice
- [Introducción](#introducción)
- [Métodos de pago implementados](#métodos-de-pago-implementados)
- [Inicio rápido](#inicio-rápido)
- [Documentación detallada](#documentación-detallada)
- [Scripts de prueba](#scripts-de-prueba)
- [Comparación de métodos](#comparación-de-métodos)
- [FAQ](#faq)

---

## 🎯 Introducción

Este documento describe la implementación de **pagos automáticos** para la compra de divisas en Global Exchange. El sistema soporta tres métodos de pago que se procesan automáticamente al confirmar una operación:

1. **Billetera Digital** - Pago desde billetera electrónica por número de teléfono
2. **Tarjeta de Débito/Crédito** - Pago con tarjetas del banco local (excluye Stripe)
3. **Cuenta Bancaria** - Transferencia bancaria tradicional

---

## 💰 Métodos de Pago Implementados

### 1️⃣ Billetera Digital

**¿Cómo funciona?**
- Cliente selecciona "Billetera Digital" como medio de pago
- Ingresa su número de teléfono asociado a la billetera
- El sistema identifica la billetera automáticamente
- Se valida el saldo disponible
- Se ejecuta el pago a la cuenta de la empresa
- Se genera comprobante único

**Ventajas**:
- ✅ Identificación rápida por teléfono
- ✅ Pago inmediato
- ✅ No requiere datos bancarios
- ✅ Ideal para clientes móviles

**Casos de uso**:
- Pagos rápidos desde móvil
- Clientes sin cuenta bancaria
- Microtransacciones

📚 **Documentación**: [BILLETERA_DIGITAL_README.md](BILLETERA_DIGITAL_README.md)

---

### 2️⃣ Tarjeta de Débito/Crédito

**¿Cómo funciona?**
- Cliente selecciona "Tarjeta de Débito" o "Tarjeta de Crédito"
- Ingresa: número de tarjeta, vencimiento, CVV, entidad bancaria
- El sistema identifica la tarjeta en la base de datos
- Se valida saldo (débito) o crédito disponible (crédito)
- Se ejecuta el cargo a la tarjeta
- Se acredita a la cuenta de la empresa
- Se genera comprobante único

**Ventajas**:
- ✅ Soporta débito y crédito
- ✅ Diferencia automáticamente el tipo
- ✅ Excluye Stripe (procesamiento local)
- ✅ Validaciones específicas por tipo

**Casos de uso**:
- Compras con tarjeta de crédito (a financiar)
- Pagos con débito inmediato
- Clientes con tarjetas locales

**⚠️ Importante**: Este método solo procesa tarjetas registradas localmente. Si la entidad es "Stripe", se usa el procesador Stripe existente.

📚 **Documentación**: [PAGO_TARJETA_DEBITO_CREDITO.md](PAGO_TARJETA_DEBITO_CREDITO.md)

---

### 3️⃣ Cuenta Bancaria (Existente)

**¿Cómo funciona?**
- Cliente selecciona cuenta bancaria
- Ingresa datos de cuenta
- Se realiza transferencia tradicional

Este método ya existía y sigue funcionando normalmente.

---

## 🚀 Inicio Rápido

### Para Desarrolladores

#### 1. Revisar cambios en código

Archivo principal modificado: **`transacciones/views.py`**

```python
# Nuevas funciones agregadas:
- realizar_pago_tarjeta()      # Línea ~300
- realizar_pago_billetera()    # Línea ~432
- Modificado: crear_transaccion_desde_compra()  # Línea ~1100
```

#### 2. Ejecutar tests

```bash
# Test de billetera
python manage.py shell < scripts/test_pago_billetera.py

# Test de tarjeta
python manage.py shell < scripts/test_pago_tarjeta.py
```

#### 3. Configurar en Admin

**Billetera Digital**:
1. Admin → Medios de Pago → Agregar
2. Nombre: "Billetera Digital"
3. Tipo: "billetera_electronica"
4. Campos: Teléfono de billetera, Entidad

**Tarjeta de Débito**:
1. Admin → Medios de Pago → Agregar
2. Nombre: "Tarjeta de Débito"
3. Tipo: "tarjeta"
4. Campos: Número, Vencimiento, CVV, Entidad

**Tarjeta de Crédito**:
1. Admin → Medios de Pago → Agregar
2. Nombre: "Tarjeta de Crédito"
3. Tipo: "tarjeta"
4. Campos: card_number, exp_month, exp_year, cvc, Entidad

### Para Usuarios

#### Pagar con Billetera
1. Seleccionar "Billetera Digital" en medio de pago
2. Ingresar número de teléfono de la billetera
3. Seleccionar entidad bancaria
4. Confirmar operación
5. ✅ Pago procesado automáticamente

#### Pagar con Tarjeta
1. Seleccionar "Tarjeta de Débito" o "Tarjeta de Crédito"
2. Ingresar datos de la tarjeta:
   - Número de tarjeta (16 dígitos)
   - Mes de vencimiento (MM)
   - Año de vencimiento (YYYY)
   - CVV (3 dígitos)
   - Entidad bancaria
3. Confirmar operación
4. ✅ Pago procesado automáticamente

---

## 📚 Documentación Detallada

### Billetera Digital

| Documento | Descripción |
|-----------|-------------|
| [BILLETERA_DIGITAL_README.md](BILLETERA_DIGITAL_README.md) | Resumen ejecutivo y guía rápida |
| [PAGO_BILLETERA_DIGITAL.md](PAGO_BILLETERA_DIGITAL.md) | Documentación técnica completa |
| [CONFIGURACION_BILLETERA_DIGITAL.md](CONFIGURACION_BILLETERA_DIGITAL.md) | Guía de configuración paso a paso |
| [DIAGRAMA_FLUJO_BILLETERA.md](DIAGRAMA_FLUJO_BILLETERA.md) | Diagramas visuales del flujo |

### Tarjeta Débito/Crédito

| Documento | Descripción |
|-----------|-------------|
| [PAGO_TARJETA_DEBITO_CREDITO.md](PAGO_TARJETA_DEBITO_CREDITO.md) | Documentación técnica completa |
| [CONFIGURACION_TARJETA.md](CONFIGURACION_TARJETA.md) | Guía de configuración paso a paso |

### General

| Documento | Descripción |
|-----------|-------------|
| [CAMBIOS_IMPLEMENTADOS.md](../CAMBIOS_IMPLEMENTADOS.md) | Resumen de todos los cambios |
| [INSTRUCCIONES_PRUEBA.md](../INSTRUCCIONES_PRUEBA.md) | Instrucciones de testing para billetera |

---

## 🧪 Scripts de Prueba

### Test de Billetera Digital

```bash
python manage.py shell < scripts/test_pago_billetera.py
```

**Tests incluidos**:
- ✅ Configuración básica
- ✅ Pago exitoso
- ✅ Saldo insuficiente
- ✅ Billetera no encontrada
- ✅ Datos incompletos

### Test de Tarjeta

```bash
python manage.py shell < scripts/test_pago_tarjeta.py
```

**Tests incluidos**:
- ✅ Configuración básica
- ✅ Pago con débito exitoso
- ✅ Pago con crédito exitoso
- ✅ Tarjeta no encontrada
- ✅ Datos incompletos

---

## 📊 Comparación de Métodos

### Por Velocidad

| Método | Velocidad | Motivo |
|--------|-----------|--------|
| Billetera Digital | ⚡⚡⚡ Instantáneo | Solo requiere teléfono |
| Tarjeta | ⚡⚡ Muy rápido | Validación completa de datos |
| Cuenta Bancaria | ⚡ Normal | Requiere más datos |

### Por Facilidad de Uso

| Método | Facilidad | Datos requeridos |
|--------|-----------|------------------|
| Billetera Digital | ⭐⭐⭐ Muy fácil | Teléfono + Entidad |
| Tarjeta | ⭐⭐ Fácil | 5 campos (número, mes, año, CVV, entidad) |
| Cuenta Bancaria | ⭐ Normal | Múltiples datos bancarios |

### Por Tipo de Cliente

| Tipo de Cliente | Método Recomendado |
|-----------------|-------------------|
| Cliente móvil | Billetera Digital |
| Cliente con tarjeta | Tarjeta Débito/Crédito |
| Cliente corporativo | Cuenta Bancaria |
| Sin cuenta bancaria | Billetera Digital |

### Por Monto de Transacción

| Monto | Método Recomendado |
|-------|-------------------|
| Pequeño (< ₲100,000) | Billetera Digital |
| Medio (₲100,000 - ₲1,000,000) | Tarjeta Débito/Crédito |
| Grande (> ₲1,000,000) | Cuenta Bancaria |

---

## ❓ FAQ

### General

**P: ¿Cuántos métodos de pago están disponibles?**  
R: Tres métodos: Billetera Digital, Tarjeta de Débito/Crédito, y Cuenta Bancaria.

**P: ¿Los pagos son automáticos?**  
R: Sí, todos los métodos procesan el pago automáticamente al confirmar la operación.

**P: ¿Se genera comprobante?**  
R: Sí, todos los métodos generan un comprobante único (UUID).

### Billetera Digital

**P: ¿Cómo se identifica la billetera?**  
R: Por el número de teléfono asociado.

**P: ¿Qué pasa si no tengo saldo?**  
R: El sistema rechaza el pago y muestra el mensaje "Saldo insuficiente" (código 51).

**P: ¿Puedo usar cualquier billetera?**  
R: Solo billeteras registradas en el sistema y activas.

### Tarjeta de Débito/Crédito

**P: ¿Funciona con Stripe?**  
R: No, si la entidad es "Stripe" se usa el procesador Stripe existente. Este método es para tarjetas del banco local.

**P: ¿Cuál es la diferencia entre débito y crédito?**  
R: 
- **Débito**: Valida saldo en la cuenta asociada
- **Crédito**: Valida crédito disponible (límite - saldo usado)

**P: ¿Qué datos necesito de la tarjeta?**  
R: Número completo, mes/año de vencimiento, CVV y entidad bancaria.

**P: ¿La tarjeta debe estar registrada?**  
R: Sí, la tarjeta debe estar registrada en el módulo `banco`.

**P: ¿Qué pasa si pongo datos incorrectos?**  
R: El sistema responde "Tarjeta no encontrada" (código 14).

### Cuenta Bancaria

**P: ¿Sigue funcionando el método anterior?**  
R: Sí, el método de cuenta bancaria sigue funcionando normalmente.

**P: ¿Cuándo se usa este método?**  
R: Cuando el tipo de medio no es ni billetera ni tarjeta.

### Errores Comunes

**P: Error "Datos incompletos" (código 12)**  
R: Verifica que todos los campos requeridos estén completos:
- Billetera: teléfono
- Tarjeta: número, mes, año, CVV, entidad

**P: Error "No encontrado" (código 14)**  
R: 
- Billetera: El teléfono no está registrado
- Tarjeta: Los datos no coinciden con ninguna tarjeta registrada

**P: Error "Saldo insuficiente" (código 51)**  
R:
- Billetera: No hay suficiente saldo
- Débito: La cuenta no tiene fondos
- Crédito: Crédito disponible insuficiente

**P: Error "Cuenta empresa no encontrada" (código 96)**  
R: La cuenta de la empresa (BPY / 000111222) no existe. Debe crearla en Admin.

### Seguridad

**P: ¿Los datos de la tarjeta son seguros?**  
R: El sistema solo muestra los últimos 4 dígitos en logs. Los datos completos están en la base de datos.

**P: ¿Hay validación de montos?**  
R: Sí, siempre se valida que haya saldo/crédito suficiente antes de procesar.

**P: ¿Qué pasa si falla el pago?**  
R: Las transacciones son atómicas - si falla, se hace rollback automático.

---

## 🛠️ Soporte Técnico

### Logs

Filtrar logs por tipo:

```bash
# Billetera
grep "[PAGO_BILLETERA]" logs/debug.log

# Tarjeta
grep "[PAGO_TARJETA]" logs/debug.log
```

### Verificar Configuración

```python
# Django shell
python manage.py shell

# Verificar cuenta empresa
from banco.models import Cuenta
cuenta = Cuenta.objects.filter(numero_cuenta='000111222').first()
print(f"Saldo: ₲{cuenta.saldo:,.0f}")

# Verificar billeteras
from billetera.models import Billetera
billeteras = Billetera.objects.filter(estado='activa')
print(f"Billeteras activas: {billeteras.count()}")

# Verificar tarjetas
from banco.models import TarjetaDebito, TarjetaCredito
print(f"Tarjetas débito: {TarjetaDebito.objects.count()}")
print(f"Tarjetas crédito: {TarjetaCredito.objects.count()}")
```

### Contacto

Para soporte adicional:
- Revisar archivos en `docs/`
- Ejecutar scripts de test
- Verificar logs del sistema

---

## 📌 Resumen Técnico

| Aspecto | Detalle |
|---------|---------|
| **Archivo principal** | `transacciones/views.py` |
| **Funciones nuevas** | `realizar_pago_tarjeta()`, `realizar_pago_billetera()` |
| **Modificaciones** | `crear_transaccion_desde_compra()` |
| **Modelos usados** | `Billetera`, `PagoBilletera`, `TarjetaDebito`, `TarjetaCredito`, `PagoTarjeta`, `Cuenta` |
| **Códigos de error** | 00 (éxito), 12 (incompleto), 14 (no encontrado), 51 (sin fondos), 96 (error sistema) |
| **Logs** | `[PAGO_BILLETERA]`, `[PAGO_TARJETA]` |
| **Tests** | `scripts/test_pago_billetera.py`, `scripts/test_pago_tarjeta.py` |
| **Documentos** | 7 archivos en `docs/` |

---

**Versión**: 2.0  
**Última actualización**: Diciembre 2024  
**Desarrollado para**: Global Exchange
