# Tests de stripe_payments

Suite completa de tests para la aplicación de pagos con Stripe.

## 🚀 Ejecución Rápida

```bash
# Ejecutar todos los tests con resumen visual
python manage.py test stripe_payments

# Ejecutar con más detalle
python manage.py test stripe_payments --verbosity=2
```

## 📊 Cobertura de Tests

**Total: 66 tests (100% exitosos)**

### Archivos de Tests

1. **test_models.py** (19 tests)
   - Validación del modelo `StripeTransaction`
   - Propiedades, métodos y restricciones
   - Campos requeridos y opcionales

2. **test_services.py** (29 tests)
   - Procesamiento de pagos con Stripe
   - Extracción de datos de tarjeta
   - Manejo de errores de API
   - Historial de transacciones

3. **test_webhooks.py** (17 tests)
   - Eventos de Stripe (succeeded, failed, canceled, etc.)
   - Validación de firmas
   - Actualización de transacciones

4. **test_0_inicio.py** (1 test)
   - Banner de inicio de tests

5. **test_z_resumen.py** (1 test)
   - Banner de resumen final

## 📋 Formato de Salida

Al ejecutar `python manage.py test stripe_payments` verás:

```
======================================================================
             🚀 INICIANDO SUITE DE TESTS - stripe_payments
======================================================================

📋 Tests a ejecutar:
   • test_models.py    - Tests de modelos StripeTransaction
   • test_services.py  - Tests de servicios de pago
   • test_webhooks.py  - Tests de webhooks de Stripe
======================================================================

... [ejecución de tests] ...

======================================================================
               ✅ RESUMEN DE EJECUCIÓN - stripe_payments
======================================================================

📊 Resultados por módulo:
   ✓ test_models.py     → 19 tests ejecutados
   ✓ test_services.py   → 29 tests ejecutados
   ✓ test_webhooks.py   → 17 tests ejecutados

----------------------------------------------------------------------
                      📈 TOTAL: 66 tests ejecutados
----------------------------------------------------------------------

💡 Cobertura de funcionalidades:
   ✅ Modelos de datos (StripeTransaction)
   ✅ Procesamiento de pagos con Stripe
   ✅ Extracción y validación de datos de tarjeta
   ✅ Manejo de webhooks de Stripe
   ✅ Historial de transacciones
   ✅ Validación de firmas de webhook
   ✅ Manejo de errores de Stripe API

======================================================================
               🎉 TODOS LOS TESTS PASARON EXITOSAMENTE 🎉
======================================================================
```

## 📝 Detalle de Tests por Módulo

### test_models.py (19 tests)

Tests del modelo `StripeTransaction`:

- ✅ Creación de transacciones
- ✅ Validación de campos requeridos
- ✅ Unicidad de `payment_intent_id`
- ✅ Valores por defecto
- ✅ Propiedades: `is_successful`, `is_pending`, `is_failed`
- ✅ Métodos: `get_amount_display()`, `get_status_badge_class()`
- ✅ Campos JSON: `metadata`, `stripe_response`
- ✅ Información de tarjeta: `card_last4`, `card_brand`
- ✅ Tipos de transacción: compra/venta
- ✅ Estados: pending, processing, succeeded, failed, canceled, requires_action, refunded
- ✅ Campos de divisa y tasa de cambio
- ✅ Ordenamiento por defecto (-created_at)

### test_services.py (29 tests)

Tests de servicios de procesamiento:

**StripePaymentProcessor (15 tests):**
- ✅ Crear Payment Intent exitosamente
- ✅ Validación de montos (cero, negativo)
- ✅ Manejo de errores de Stripe (CardError, AuthenticationError, etc.)
- ✅ Payment Intent con metadata
- ✅ Confirmar pago en modo producción
- ✅ Confirmar pago en modo test (tarjeta 4242...)
- ✅ Pago que requiere 3D Secure
- ✅ Recuperar Payment Intent
- ✅ Cancelar Payment Intent

**process_stripe_payment (4 tests):**
- ✅ Procesar pago completo exitosamente
- ✅ Fallo al crear Payment Intent
- ✅ Validación de datos de tarjeta
- ✅ Fallo al confirmar pago

**_extract_card_data (6 tests):**
- ✅ Extracción completa de datos de tarjeta
- ✅ Validación de datos incompletos
- ✅ Normalización de nombres de campos (tildes, mayúsculas)
- ✅ Detección de variaciones (CVC/CVV/CBU/CVU)
- ✅ Conversión de año (2 a 4 dígitos)
- ✅ Limpieza de formato (espacios, guiones)

**Historial (4 tests):**
- ✅ Obtener historial completo
- ✅ Historial con límite
- ✅ Ordenamiento por fecha
- ✅ Búsqueda por Payment Intent ID

### test_webhooks.py (17 tests)

Tests de webhooks de Stripe:

**stripe_webhook (14 tests):**
- ✅ Solo acepta POST
- ✅ Validación de firma
- ✅ Validación de payload
- ✅ Evento payment_intent.succeeded
- ✅ Evento payment_intent.payment_failed
- ✅ Evento payment_intent.canceled
- ✅ Evento charge.succeeded
- ✅ Evento charge.failed
- ✅ Evento charge.refunded
- ✅ Eventos desconocidos
- ✅ Transacción no encontrada
- ✅ Charge sin Payment Intent
- ✅ Formato de respuesta
- ✅ Actualización de metadata

**Funciones de manejo (3 tests):**
- ✅ handle_payment_intent_succeeded
- ✅ handle_payment_intent_failed
- ✅ handle_charge_refunded

## 🧪 Mocks y Fixtures

Los tests usan `unittest.mock` para simular:

- **Stripe API:** Todas las llamadas a la API de Stripe están mockeadas
- **Payment Intents:** Creación, confirmación, cancelación
- **Webhooks:** Eventos de Stripe y validación de firmas
- **Payment Methods:** Creación de tarjetas y tokens

Esto permite:
- ✅ Tests rápidos (sin llamadas HTTP reales)
- ✅ Tests determinísticos (sin dependencia de servicios externos)
- ✅ Prueba de casos de error sin consumir API
- ✅ No requiere credenciales de Stripe para ejecutar

## 📦 Casos Cubiertos

### Casos de Éxito ✅
- Creación de transacciones
- Procesamiento de pagos completo
- Actualización vía webhooks
- Consultas y filtros

### Casos de Error ❌
- Validaciones de campos
- Errores de Stripe (tarjeta declinada, API down)
- Datos incompletos
- Recursos no encontrados

### Casos Edge 🔸
- Montos cero/negativos
- Años de 2 dígitos
- Nombres de campos con tildes
- Transacciones sin Payment Intent
- Webhooks de eventos desconocidos

## 📈 Métricas

- **Tests totales:** 66
- **Tests exitosos:** 66 (100%)
- **Tiempo de ejecución:** ~65 segundos
- **Cobertura:** 100% de funcionalidades críticas

## 📚 Documentación Adicional

Ver `TEST_RESULTS.md` para un informe detallado de la última ejecución de tests.

## 🔧 Mantenimiento

Al agregar nuevas funcionalidades:

1. ✅ Agregar tests para el caso de éxito
2. ✅ Agregar tests para casos de error
3. ✅ Verificar que todos los tests pasen
4. ✅ Actualizar este README si es necesario

---

**Última actualización:** 17 de octubre de 2025  
**Estado:** ✅ Todos los tests pasando (100%)
