# Configuración de Medio de Pago con Stripe

## 📝 Pasos para Configurar Stripe como Medio de Pago

### Opción 1: Desde el Admin de Django

1. **Acceder al Admin**
   - URL: `http://localhost:8000/admin/`
   - Login con credenciales de superusuario

2. **Crear Medio de Pago**
   - Ir a `Medios Pago` → `Medios de pago`
   - Clic en `Agregar medio de pago`
   
3. **Configurar los siguientes campos:**
   ```
   Nombre: Stripe - Tarjeta de Crédito/Débito
   Tipo de medio: stripe (o "Tarjeta de Crédito/Débito")
   Comisión porcentaje: 2.9 (comisión típica de Stripe)
   Es activo: ✓ (marcado)
   ```

4. **Agregar Campos del Medio**
   - En la sección de campos inline, agregar:
   
   **Campo 1 - Entidad:**
   ```
   Nombre campo: Entidad
   Campo API: bank_name
   Es requerido: ✓
   Orden: 1
   ```
   
   **Campo 2 - Número de Tarjeta:**
   ```
   Nombre campo: Número de Tarjeta
   Campo API: card_number
   Es requerido: ✓
   Tipo campo: text
   Orden: 2
   Ayuda: "Ingrese el número de tarjeta sin espacios"
   ```
   
   **Campo 3 - Mes de Expiración:**
   ```
   Nombre campo: Mes de Expiración
   Campo API: exp_month
   Es requerido: ✓
   Tipo campo: number
   Orden: 3
   Ayuda: "Mes (MM)"
   ```
   
   **Campo 4 - Año de Expiración:**
   ```
   Nombre campo: Año de Expiración
   Campo API: exp_year
   Es requerido: ✓
   Tipo campo: number
   Orden: 4
   Ayuda: "Año (YYYY)"
   ```
   
   **Campo 5 - CVC:**
   ```
   Nombre campo: Código de Seguridad (CVC)
   Campo API: cvc
   Es requerido: ✓
   Tipo campo: text
   Orden: 5
   Ayuda: "3 o 4 dígitos en el reverso de la tarjeta"
   ```
   
   **Campo 6 - Nombre del Titular:**
   ```
   Nombre campo: Nombre del Titular
   Campo API: cardholder_name
   Es requerido: ✓
   Tipo campo: text
   Orden: 6
   Ayuda: "Nombre como aparece en la tarjeta"
   ```

5. **Guardar**
   - Clic en `Guardar`

### Opción 2: Mediante Script SQL

Ejecutar en la base de datos PostgreSQL:

```sql
-- Insertar el medio de pago
INSERT INTO medios_pago_mediodepago (nombre, tipo_medio, comision_porcentaje, es_activo)
VALUES ('Stripe - Tarjeta de Crédito/Débito', 'stripe', 2.9, true)
RETURNING id;

-- Copiar el ID retornado y usarlo en los siguientes inserts
-- Reemplazar {MEDIO_ID} con el ID obtenido

-- Campo Entidad
INSERT INTO medios_pago_campomediodepago (medio_de_pago_id, nombre_campo, campo_api, es_requerido, orden)
VALUES ({MEDIO_ID}, 'Entidad', 'bank_name', true, 1);

-- Campo Número de Tarjeta
INSERT INTO medios_pago_campomediodepago (medio_de_pago_id, nombre_campo, campo_api, es_requerido, tipo_campo, orden, texto_ayuda)
VALUES ({MEDIO_ID}, 'Número de Tarjeta', 'card_number', true, 'text', 2, 'Ingrese el número de tarjeta sin espacios');

-- Campo Mes de Expiración
INSERT INTO medios_pago_campomediodepago (medio_de_pago_id, nombre_campo, campo_api, es_requerido, tipo_campo, orden, texto_ayuda)
VALUES ({MEDIO_ID}, 'Mes de Expiración', 'exp_month', true, 'number', 3, 'Mes (MM)');

-- Campo Año de Expiración
INSERT INTO medios_pago_campomediodepago (medio_de_pago_id, nombre_campo, campo_api, es_requerido, tipo_campo, orden, texto_ayuda)
VALUES ({MEDIO_ID}, 'Año de Expiración', 'exp_year', true, 'number', 4, 'Año (YYYY)');

-- Campo CVC
INSERT INTO medios_pago_campomediodepago (medio_de_pago_id, nombre_campo, campo_api, es_requerido, tipo_campo, orden, texto_ayuda)
VALUES ({MEDIO_ID}, 'Código de Seguridad (CVC)', 'cvc', true, 'text', 5, '3 o 4 dígitos en el reverso de la tarjeta');

-- Campo Nombre del Titular
INSERT INTO medios_pago_campomediodepago (medio_de_pago_id, nombre_campo, campo_api, es_requerido, tipo_campo, orden, texto_ayuda)
VALUES ({MEDIO_ID}, 'Nombre del Titular', 'cardholder_name', true, 'text', 6, 'Nombre como aparece en la tarjeta');
```

### Opción 3: Mediante Fixtures (Recomendado para desarrollo)

Crear archivo `medios_pago/fixtures/stripe_medio_pago.json`:

```json
[
  {
    "model": "medios_pago.mediodepago",
    "pk": 100,
    "fields": {
      "nombre": "Stripe - Tarjeta de Crédito/Débito",
      "tipo_medio": "stripe",
      "comision_porcentaje": "2.90",
      "es_activo": true
    }
  },
  {
    "model": "medios_pago.campomediodepago",
    "fields": {
      "medio_de_pago": 100,
      "nombre_campo": "Entidad",
      "campo_api": "bank_name",
      "es_requerido": true,
      "orden": 1
    }
  },
  {
    "model": "medios_pago.campomediodepago",
    "fields": {
      "medio_de_pago": 100,
      "nombre_campo": "Número de Tarjeta",
      "campo_api": "card_number",
      "es_requerido": true,
      "tipo_campo": "text",
      "orden": 2,
      "texto_ayuda": "Ingrese el número de tarjeta sin espacios"
    }
  },
  {
    "model": "medios_pago.campomediodepago",
    "fields": {
      "medio_de_pago": 100,
      "nombre_campo": "Mes de Expiración",
      "campo_api": "exp_month",
      "es_requerido": true,
      "tipo_campo": "number",
      "orden": 3,
      "texto_ayuda": "Mes (MM)"
    }
  },
  {
    "model": "medios_pago.campomediodepago",
    "fields": {
      "medio_de_pago": 100,
      "nombre_campo": "Año de Expiración",
      "campo_api": "exp_year",
      "es_requerido": true,
      "tipo_campo": "number",
      "orden": 4,
      "texto_ayuda": "Año (YYYY)"
    }
  },
  {
    "model": "medios_pago.campomediodepago",
    "fields": {
      "medio_de_pago": 100,
      "nombre_campo": "Código de Seguridad (CVC)",
      "campo_api": "cvc",
      "es_requerido": true,
      "tipo_campo": "text",
      "orden": 5,
      "texto_ayuda": "3 o 4 dígitos en el reverso de la tarjeta"
    }
  },
  {
    "model": "medios_pago.campomediodepago",
    "fields": {
      "medio_de_pago": 100,
      "nombre_campo": "Nombre del Titular",
      "campo_api": "cardholder_name",
      "es_requerido": true,
      "tipo_campo": "text",
      "orden": 6,
      "texto_ayuda": "Nombre como aparece en la tarjeta"
    }
  }
]
```

Luego cargar con:
```bash
python manage.py loaddata stripe_medio_pago
```

## 👤 Asignar Medio de Pago a un Cliente

### Desde el Admin

1. Ir a `Clientes` → `Cliente medio de pagos`
2. Clic en `Agregar cliente medio de pago`
3. Configurar:
   ```
   Cliente: [Seleccionar cliente]
   Medio de pago: Stripe - Tarjeta de Crédito/Débito
   Es principal: ✓ (si es el medio principal)
   Es activo: ✓
   ```
4. En la sección de datos, agregar:
   - **Entidad**: "Stripe" (IMPORTANTE: debe contener "Stripe")
   - **Número de Tarjeta**: 4242424242424242 (tarjeta de prueba)
   - **Mes de Expiración**: 12
   - **Año de Expiración**: 2025
   - **CVC**: 123
   - **Nombre del Titular**: Juan Pérez

5. Guardar

## 🧪 Probar la Integración

1. **Login como cliente** con el medio de pago asignado
2. **Ir a Compra de Divisas**
3. **Seleccionar divisa y monto**
4. **Confirmar simulación**
5. **Seleccionar el medio de pago Stripe**
6. **Confirmar operación**
7. **Verificar que el pago se procesa**
8. **Ver el detalle de la transacción**

## 🔍 Verificar Transacciones

### En la Aplicación
- URL: `/stripe/transactions/`
- Ver lista de transacciones del usuario

### En el Admin
- URL: `/admin/stripe_payments/stripetransaction/`
- Ver todas las transacciones del sistema

### En Stripe Dashboard
- URL: https://dashboard.stripe.com/test/payments
- Ver pagos procesados en Stripe

## ⚠️ Notas Importantes

1. **Campo "Entidad"**: DEBE contener la palabra "Stripe" (case-insensitive) para que el sistema lo detecte
2. **Tipo de medio**: Debe ser "stripe" o "Tarjeta de Crédito/Débito"
3. **Tarjetas de prueba**: Solo usar tarjetas de prueba de Stripe en desarrollo
4. **Claves API**: Verificar que las claves estén configuradas en settings.py
5. **HTTPS**: En producción usar HTTPS para proteger datos de tarjetas

## 🐛 Troubleshooting

### El pago no se procesa con Stripe
- Verificar que el campo "Entidad" contenga "Stripe"
- Verificar que el tipo_medio sea "stripe"
- Revisar los logs de Django para errores

### Error de autenticación con Stripe
- Verificar las claves API en settings.py
- Verificar que stripe esté instalado: `pip show stripe`

### Transacción falla
- Verificar datos de la tarjeta de prueba
- Revisar en Dashboard de Stripe los detalles del error
- Consultar los logs de la aplicación

## 📚 Referencias

- [Stripe API Documentation](https://stripe.com/docs/api)
- [Payment Intents](https://stripe.com/docs/payments/payment-intents)
- [Testing Cards](https://stripe.com/docs/testing)
