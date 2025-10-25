# 🔔 Configuración de Webhooks de Stripe

## ¿Qué son los Webhooks?

Los webhooks de Stripe son notificaciones automáticas que Stripe envía a tu servidor cuando ocurren eventos importantes (pagos exitosos, fallos, reembolsos, etc.). Esto permite mantener tu base de datos sincronizada con el estado real en Stripe.

---

## 🔑 Tu Webhook Secret

Tu `STRIPE_WEBHOOK_SECRET` ya está configurado:

```
whsec_32b4e065fe19a60910470282b157b2536e644e0d6fdf5a01cebcdbee92334f8d
```

Esta clave se usa para verificar que las notificaciones realmente vienen de Stripe y no son falsificadas.

---

## 🚀 Configuración en Stripe Dashboard

### Paso 1: Acceder al Dashboard

1. Ir a: https://dashboard.stripe.com/test/webhooks
2. Login con tu cuenta de Stripe

### Paso 2: Crear el Endpoint

1. Click en **"Add endpoint"** o **"+ Agregar endpoint"**
2. En **"Endpoint URL"** poner:
   ```
   https://tudominio.com/stripe/webhook/
   ```
   
   ⚠️ **Para desarrollo local**, necesitas usar Stripe CLI (ver sección más abajo)

### Paso 3: Seleccionar Eventos

Selecciona estos eventos para recibir notificaciones:

**Payment Intents:**
- ✅ `payment_intent.succeeded` - Pago exitoso
- ✅ `payment_intent.payment_failed` - Pago fallido
- ✅ `payment_intent.canceled` - Pago cancelado

**Charges:**
- ✅ `charge.succeeded` - Cargo exitoso
- ✅ `charge.failed` - Cargo fallido
- ✅ `charge.refunded` - Cargo reembolsado

### Paso 4: Guardar

1. Click en **"Add endpoint"**
2. Stripe mostrará el **Signing secret** - este es tu `STRIPE_WEBHOOK_SECRET`
3. Ya lo tienes configurado en `settings.py` ✅

---

## 💻 Testing con Stripe CLI (Desarrollo Local)

Para probar webhooks en tu máquina local, usa Stripe CLI:

### Instalar Stripe CLI

**Windows (con Scoop):**
```powershell
scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git
scoop install stripe
```

**Windows (Descarga directa):**
1. Ir a: https://github.com/stripe/stripe-cli/releases/latest
2. Descargar `stripe_X.X.X_windows_x86_64.zip`
3. Extraer y agregar al PATH

**Mac:**
```bash
brew install stripe/stripe-cli/stripe
```

**Linux:**
```bash
# Debian/Ubuntu
wget -qO- https://github.com/stripe/stripe-cli/releases/latest/download/stripe_linux_x86_64.tar.gz | tar xz
sudo mv stripe /usr/local/bin/
```

### Autenticarse

```bash
stripe login
```

Esto abrirá tu navegador para autorizar el CLI.

### Iniciar el Forward de Webhooks

```bash
stripe listen --forward-to localhost:8000/stripe/webhook/
```

Esto:
1. Crea un webhook temporal
2. Te da un nuevo `webhook secret` (empieza con `whsec_...`)
3. Reenvía todos los eventos a tu servidor local

**⚠️ Importante:** Actualiza temporalmente el `STRIPE_WEBHOOK_SECRET` en `settings.py` con el que te da el CLI mientras desarrollas.

### Enviar un Evento de Prueba

En otra terminal:

```bash
stripe trigger payment_intent.succeeded
```

Deberías ver el evento en tu terminal y en los logs de Django.

---

## 🎯 Eventos Manejados

### payment_intent.succeeded
- **Cuándo:** Un pago se completa exitosamente
- **Acción:** Actualiza el estado a 'succeeded', guarda información del cargo y tarjeta

### payment_intent.payment_failed
- **Cuándo:** Un pago falla
- **Acción:** Actualiza el estado a 'failed', guarda mensaje de error

### payment_intent.canceled
- **Cuándo:** Un pago es cancelado
- **Acción:** Actualiza el estado a 'canceled', guarda razón de cancelación

### charge.succeeded
- **Cuándo:** Un cargo es exitoso (después del payment intent)
- **Acción:** Guarda el ID del cargo y detalles de la tarjeta

### charge.failed
- **Cuándo:** Un cargo falla
- **Acción:** Actualiza estado y guarda código de error

### charge.refunded
- **Cuándo:** Se hace un reembolso
- **Acción:** Cambia estado a 'refunded', guarda detalles del reembolso

---

## 🔍 Verificar que Funciona

### En tu Aplicación

1. Crear una transacción de prueba
2. Ver en logs de Django que se reciben webhooks
3. Verificar que el estado se actualiza en `/admin/stripe_payments/stripetransaction/`

### En Stripe Dashboard

1. Ir a: https://dashboard.stripe.com/test/webhooks
2. Click en tu endpoint
3. Ver sección **"Recent deliveries"**
4. Verificar que muestra status 200 (exitoso)

### Logs de Django

Los webhooks registran información en los logs:

```python
# Webhook recibido exitosamente
INFO: Webhook recibido: payment_intent.succeeded - ID: evt_xxx
INFO: ✓ Payment Intent pi_xxx actualizado a succeeded

# Errores
ERROR: Webhook payload inválido
ERROR: Webhook firma inválida
WARNING: Transaction no encontrada para Payment Intent: pi_xxx
```

---

## 🛠️ Troubleshooting

### Error: "Webhook firma inválida"

**Problema:** El `STRIPE_WEBHOOK_SECRET` no coincide.

**Solución:**
1. Verificar que el secret en `settings.py` sea correcto
2. Si usas Stripe CLI, usar el secret que te da `stripe listen`
3. Si usas Dashboard, copiar el secret del endpoint

### Error: "Transaction no encontrada"

**Problema:** El webhook llegó pero no hay transacción en la BD.

**Solución:**
- Verificar que la transacción se creó correctamente en el pago
- Ver que el `payment_intent_id` coincida

### Webhook no llega

**Problema:** No se reciben notificaciones.

**Solución:**
1. Verificar que el endpoint esté creado en Stripe Dashboard
2. Si es local, usar Stripe CLI con `stripe listen`
3. Verificar que la URL sea accesible desde internet (en producción)
4. Revisar firewall y configuración de red

### Status 500 en webhooks

**Problema:** El endpoint responde con error.

**Solución:**
1. Revisar logs de Django para el error específico
2. Verificar que el modelo `StripeTransaction` esté migrado
3. Verificar permisos de base de datos

---

## 📊 Monitorear Webhooks

### Stripe Dashboard

- **URL:** https://dashboard.stripe.com/test/webhooks
- Ver todos los webhooks enviados
- Ver respuestas de tu servidor
- Reenviar webhooks manualmente

### Logs de tu Aplicación

```bash
# Ver logs en tiempo real
tail -f logs/django.log

# Buscar webhooks específicos
grep "Webhook recibido" logs/django.log
```

### Base de Datos

```sql
-- Ver transacciones actualizadas por webhook
SELECT 
    payment_intent_id, 
    status, 
    metadata->>'last_webhook' as ultimo_webhook,
    updated_at
FROM stripe_payments_stripetransaction
WHERE metadata->>'webhook_updated' = 'true'
ORDER BY updated_at DESC;
```

---

## 🔐 Seguridad

### Validación de Firma

El webhook **siempre** verifica la firma de Stripe usando `STRIPE_WEBHOOK_SECRET`. Esto previene:
- Webhooks falsificados
- Ataques de replay
- Modificación de datos

### CSRF Exempt

El endpoint está marcado con `@csrf_exempt` porque Stripe no puede enviar tokens CSRF. La seguridad viene de la validación de firma.

### Solo POST

El endpoint solo acepta método POST (`@require_POST`).

---

## 🚀 Producción

### Requisitos

1. **Dominio público:** Tu servidor debe ser accesible desde internet
2. **HTTPS:** Stripe requiere HTTPS para webhooks en producción
3. **Secret de producción:** Cambiar a las claves de producción

### Pasos

1. Ir a: https://dashboard.stripe.com/webhooks (sin `/test/`)
2. Crear endpoint con tu URL de producción
3. Seleccionar los mismos eventos
4. Copiar el nuevo `STRIPE_WEBHOOK_SECRET` de producción
5. Actualizar en tu servidor con la clave de producción

---

## 📝 Testing Manual

### Probar un Webhook Localmente

```bash
# Terminal 1: Iniciar servidor Django
python manage.py runserver

# Terminal 2: Iniciar Stripe CLI
stripe listen --forward-to localhost:8000/stripe/webhook/

# Terminal 3: Enviar evento de prueba
stripe trigger payment_intent.succeeded
```

### Probar en Producción

1. Ir a Dashboard de Stripe
2. Click en tu endpoint
3. Click en "Send test webhook"
4. Seleccionar un evento
5. Click en "Send test webhook"

---

## 📚 Referencias

- **Webhooks Overview:** https://stripe.com/docs/webhooks
- **Testing Webhooks:** https://stripe.com/docs/webhooks/test
- **Stripe CLI:** https://stripe.com/docs/stripe-cli
- **Webhook Events:** https://stripe.com/docs/api/events/types

---

## ✅ Checklist de Configuración

- [x] `STRIPE_WEBHOOK_SECRET` configurado en `settings.py`
- [x] Endpoint `/stripe/webhook/` creado
- [x] Handler de webhooks implementado
- [ ] Endpoint creado en Stripe Dashboard (o usando Stripe CLI)
- [ ] Eventos seleccionados
- [ ] Webhooks probados
- [ ] Logs monitoreados

---

**Tu Webhook URL:** `https://tudominio.com/stripe/webhook/`  
**Para local:** Usar Stripe CLI con `stripe listen`

🎉 **Los webhooks están listos para usar!**
