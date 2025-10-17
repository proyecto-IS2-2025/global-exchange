# Instrucciones de Instalación y Configuración de Stripe

## 🚀 Instalación

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar migraciones
```bash
python manage.py makemigrations stripe
python manage.py migrate
```

### 3. Verificar configuración
Las claves de Stripe ya están configuradas en `settings.py`:
- STRIPE_PUBLISHABLE_KEY (para el frontend, si se necesita)
- STRIPE_SECRET_KEY (para el backend)

## 📋 Configuración del Medio de Pago

Para que una operación se procese con Stripe, el medio de pago debe cumplir:

1. **Tipo de medio**: `stripe` (Tarjeta de Crédito/Débito)
2. **Campo "Entidad"**: Debe tener el campo `bank_name` con valor "Stripe"
3. **Campos requeridos**:
   - Número de tarjeta (`card_number`)
   - Mes de vencimiento (`exp_month`)
   - Año de vencimiento (`exp_year`)
   - Código de seguridad (`cvc`)
   - Nombre en la tarjeta (`cardholder_name`) - opcional

### Crear un medio de pago Stripe desde el Admin:

1. Ir a **Admin** → **Medios de Pago** → **Medio De Pago**
2. Crear nuevo medio:
   - Nombre: "Tarjeta de Crédito - Stripe"
   - Tipo de medio: "Tarjeta de Crédito/Débito" (stripe)
   - Aplicar template: "stripe_card"
3. Asegurarse de que tenga el campo "Entidad" (`bank_name`) con valor "Stripe"

## 🔄 Flujo de Uso

### Para el Cliente:
1. Ir a **Operaciones** → **Compra de Divisa**
2. Seleccionar divisa y monto
3. Confirmar simulación
4. **Seleccionar medio de pago** con Stripe configurado
5. Confirmar operación
6. El sistema procesará el pago automáticamente con Stripe

### Resultado:
- ✅ Si el pago es exitoso: Se redirige a la página de detalle de transacción
- ❌ Si el pago falla: Se muestra el error y se puede reintentar

## 📊 Historial de Transacciones

### Ver historial:
- URL: `/stripe/transactions/`
- Muestra todas las transacciones procesadas con Stripe
- Filtros disponibles:
  - Por estado (exitosa, fallida, pendiente)
  - Por tipo (compra, venta)
  
### Ver detalle de transacción:
- URL: `/stripe/transactions/<id>/`
- Muestra información completa de la transacción
- Incluye metadatos y respuesta de Stripe

### Ver recibo:
- URL: `/stripe/transactions/<id>/receipt/`
- Genera un recibo imprimible de la transacción exitosa

## 🔍 Verificación de Funcionamiento

### 1. Crear medio de pago de prueba:
```python
python manage.py shell
```

```python
from medios_pago.models import MedioDePago, CampoMedioDePago

# Crear medio Stripe
medio = MedioDePago.objects.create(
    nombre="Tarjeta Stripe Test",
    tipo_medio="stripe",
    comision_porcentaje=2.5
)

# Aplicar template
medio.aplicar_template('stripe_card')

# Verificar que tiene el campo bank_name con "Stripe"
campo_entidad = medio.campos.filter(campo_api='bank_name').first()
print(f"Campo entidad: {campo_entidad}")
```

### 2. Asignar medio de pago a un cliente:
- Ir a perfil de cliente
- Agregar medio de pago
- Seleccionar el medio Stripe creado
- Llenar campos de tarjeta de prueba

### 3. Tarjetas de prueba de Stripe:
- **Éxito**: 4242 4242 4242 4242
- **Fallo**: 4000 0000 0000 0002
- **Requiere autenticación**: 4000 0027 6000 3184
- Fecha: Cualquier fecha futura
- CVC: Cualquier 3 dígitos
- Nombre: Cualquier nombre

## 🐛 Debugging

### Ver logs:
Los logs de Stripe se registran en el logger estándar de Django:
```python
import logging
logger = logging.getLogger(__name__)
```

### Verificar transacciones en Admin:
- Ir a **Admin** → **Stripe** → **Stripe Transactions**
- Ver todas las transacciones registradas
- Revisar respuestas de Stripe y errores

### Dashboard de Stripe:
- Ir a [https://dashboard.stripe.com/test/payments](https://dashboard.stripe.com/test/payments)
- Ver todas las transacciones procesadas en modo test

## ⚠️ Notas Importantes

1. **Modo Test**: Las claves configuradas son de TEST. Para producción necesitas cambiarlas por las claves reales.

2. **Seguridad**: Los datos de tarjeta nunca se almacenan en la base de datos, solo se envían a Stripe.

3. **Moneda**: Por defecto se usa PYG (Guaraníes paraguayos). Stripe lo soporta.

4. **Webhooks**: Si necesitas webhooks de Stripe, debes configurar:
   ```python
   STRIPE_WEBHOOK_SECRET = "whsec_..."
   ```
   Y crear una vista para recibir los eventos.

## 📝 Ejemplos de Uso

### Verificar si un medio es Stripe:
```python
from clientes.models import ClienteMedioDePago

medio = ClienteMedioDePago.objects.get(id=1)
es_stripe = medio.medio_de_pago.tipo_medio == 'stripe'

# Verificar campo entidad
for campo in medio.medio_de_pago.campos.all():
    if campo.campo_api == 'bank_name':
        valor = medio.get_dato_campo(campo.nombre_campo)
        if valor and 'stripe' in valor.lower():
            print("Es Stripe!")
```

### Obtener historial de un cliente:
```python
from stripe.services import get_transaction_history

transactions = get_transaction_history(request.user, limit=10)
for t in transactions:
    print(f"{t.payment_intent_id} - {t.status} - {t.amount}")
```

## 🎯 URLs Disponibles

- `/stripe/transactions/` - Lista de transacciones
- `/stripe/transactions/<id>/` - Detalle de transacción
- `/stripe/transactions/<id>/receipt/` - Recibo de transacción
- `/stripe/transactions/<id>/status/` - Estado de transacción (AJAX)

## ✅ Checklist de Implementación

- [x] Dependencias instaladas
- [x] Modelos creados
- [x] Migraciones ejecutadas
- [x] Servicios de procesamiento implementados
- [x] Integración en confirmación de compra
- [x] Vistas de historial creadas
- [x] Templates creados
- [x] URLs configuradas
- [x] Admin configurado
- [ ] Probar con tarjeta de prueba
- [ ] Verificar transacción en historial
- [ ] Verificar transacción en dashboard de Stripe
