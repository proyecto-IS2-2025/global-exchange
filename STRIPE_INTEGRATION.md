# Integración de Stripe - Guía de Uso

## 📋 Descripción

Se ha implementado exitosamente la integración con Stripe para procesar pagos con tarjeta de crédito/débito en las operaciones de compra de divisas.

## 🔑 Configuración

### 1. Claves de API

Las claves de Stripe están configuradas en `casa_de_cambios/settings.py`:

```python
STRIPE_PUBLISHABLE_KEY = "pk_test_51SCTnvFayINu5q7y2Xs9rtuAXlKXFESkR2jtUI6yrPVRkbn2mA5lJ3QOMGYcSVVn4V3BbjfJnUHuu1gYxfZspNDz00hJkOST0s"
STRIPE_SECRET_KEY = "sk_test_51SCTnvFayINu5q7yTXQJO2Old7r5bI35yOYD43Zvas0j0ZXr66aFt4cpy73ZKn61iUPcmGlNkxaZ1ib0XUVYoc8O00cfCofmn1"
```

### 2. Instalación de Dependencias

La librería de Stripe ya está incluida en `requirements.txt`:

```bash
stripe==8.0.0
```

Para instalarla:

```bash
pip install -r requirements.txt
```

### 3. Migraciones

Ejecutar las migraciones para crear la tabla de transacciones de Stripe:

```bash
python manage.py migrate stripe_payments
```

## 🚀 Cómo Funciona

### Flujo de Pago

1. **El cliente inicia una operación de compra de divisas**
   - Selecciona la divisa y el monto
   - Confirma la simulación

2. **Selección de medio de pago**
   - El cliente selecciona un medio de pago de tipo "Tarjeta de Crédito/Débito"
   - El medio debe tener el campo "Entidad" con valor "Stripe"

3. **Procesamiento automático**
   - El sistema detecta automáticamente si el medio de pago es Stripe
   - Crea un Payment Intent en Stripe
   - Procesa el pago con la información de la tarjeta
   - Registra la transacción en la base de datos

4. **Confirmación**
   - Si el pago es exitoso, se muestra el detalle de la transacción
   - Si hay un error, se muestra un mensaje descriptivo

### Criterios para Activar Stripe

El sistema procesa un pago con Stripe si se cumplen **TODAS** estas condiciones:

1. **Tipo de operación**: Compra de divisas
2. **Tipo de medio**: `tipo_medio = 'stripe'` o "Tarjeta de Crédito/Débito"
3. **Entidad**: Campo "Entidad" o "bank_name" contiene "Stripe"

## 📊 Modelo de Datos

### StripeTransaction

El modelo almacena toda la información de las transacciones:

```python
- payment_intent_id: ID único de Stripe
- charge_id: ID del cargo (cuando se completa)
- cliente: Usuario que realizó el pago
- transaction_type: Tipo de operación (compra/venta)
- amount: Monto en guaraníes
- currency: Moneda (PYG)
- divisa_code: Código de la divisa comprada (USD, EUR, etc.)
- monto_divisa: Cantidad de divisa adquirida
- tasa_cambio: Tasa de cambio aplicada
- status: Estado (pending, succeeded, failed, canceled)
- card_brand: Marca de tarjeta (visa, mastercard, etc.)
- card_last4: Últimos 4 dígitos de la tarjeta
- client_ip: IP del cliente
- metadata: Información adicional en JSON
- stripe_response: Respuesta completa de Stripe en JSON
- error_message: Mensaje de error si falló
- created_at/updated_at: Timestamps
```

## 🔍 Historial de Transacciones

### Para Clientes

URL: `/stripe/transactions/`

Muestra:
- Lista de todas las transacciones del usuario autenticado
- Filtros por estado y tipo
- Búsqueda por ID de transacción
- Paginación

### Detalle de Transacción

URL: `/stripe/transactions/<id>/`

Muestra:
- Información completa de la transacción
- Datos de la tarjeta (enmascarados)
- Estado actual
- Monto y divisa
- Fecha y hora

### Recibo

URL: `/stripe/transactions/<id>/receipt/`

Genera un recibo descargable con:
- Datos del cliente
- Información de la transacción
- Detalles del pago
- Formato para imprimir

## 🛠️ Panel de Administración

Los administradores pueden acceder a `/admin/stripe_payments/stripetransaction/` para:

- Ver todas las transacciones
- Filtrar por estado, tipo, moneda, fecha
- Buscar por ID de Stripe, cliente, email
- Ver detalles completos incluyendo respuestas de Stripe
- Exportar datos

## 📝 Logs

Todas las operaciones con Stripe se registran en el logger de Django:

```python
logger = logging.getLogger(__name__)
```

Los logs incluyen:
- Creación de Payment Intents
- Errores de tarjeta
- Errores de conexión
- Respuestas de Stripe

## 🧪 Tarjetas de Prueba

Stripe proporciona tarjetas de prueba para desarrollo:

### Tarjetas Exitosas

```
Visa: 4242 4242 4242 4242
Mastercard: 5555 5555 5555 4444
American Express: 3782 822463 10005
```

### Tarjetas con Errores

```
Tarjeta declinada: 4000 0000 0000 0002
Fondos insuficientes: 4000 0000 0000 9995
Expiracion inválida: 4000 0000 0000 0069
CVC inválido: 4000 0000 0000 0127
```

**Datos adicionales de prueba:**
- Cualquier fecha futura para expiración
- Cualquier CVC de 3 dígitos (4 para Amex)
- Cualquier nombre
- Cualquier código postal

## 🔐 Seguridad

1. **Claves API**: Las claves secretas nunca deben exponerse en el frontend
2. **PCI Compliance**: Nunca almacenamos números de tarjeta completos
3. **HTTPS**: En producción, usar siempre HTTPS
4. **Validación**: Todos los datos son validados antes de enviar a Stripe
5. **Logs**: Información sensible no se registra en logs

## 🌐 URLs Disponibles

```python
# Listar transacciones del usuario
/stripe/transactions/

# Detalle de transacción
/stripe/transactions/<id>/

# Recibo de transacción
/stripe/transactions/<id>/receipt/

# Estado de transacción (AJAX)
/stripe/transactions/<id>/status/
```

## 📱 Integración en Templates

El sistema automáticamente detecta si debe usar Stripe basado en el medio de pago seleccionado. No se requiere cambio en templates existentes.

## ⚠️ Consideraciones Importantes

1. **Moneda**: El sistema está configurado para trabajar con guaraníes (PYG)
2. **Montos**: Stripe trabaja con la unidad más pequeña (guaraníes, no hay centavos)
3. **Estados**: Las transacciones pueden tener múltiples estados durante su ciclo de vida
4. **Webhooks**: Se puede configurar webhooks de Stripe para recibir actualizaciones en tiempo real
5. **Reembolsos**: Actualmente no implementados, pero se puede agregar fácilmente

## 🔄 Próximos Pasos Sugeridos

1. Configurar webhooks para actualizaciones asíncronas
2. Implementar reembolsos
3. Agregar soporte para pagos recurrentes
4. Implementar 3D Secure para mayor seguridad
5. Agregar más métodos de pago (SEPA, Alipay, etc.)

## 📞 Soporte

Para más información sobre la API de Stripe:
- Documentación: https://stripe.com/docs/api
- Dashboard: https://dashboard.stripe.com/test/payments
- Logs: https://dashboard.stripe.com/test/logs

---

**Nota**: Esta es una implementación de prueba usando claves de test. Para producción, cambiar a claves de producción y configurar correctamente el dominio verificado en Stripe.
