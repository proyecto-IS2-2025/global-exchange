# Fixtures de Medios de Pago

## mediosfinancieros_data.json

Este fixture contiene los medios financieros configurados actualmente en el sistema.

### Contenido

El fixture incluye:

1. **Medios de Pago (MedioDePago)**:
   - Banco local
   - Tarjeta de Crédito Internacional (Stripe)
   - Billetera Electrónica

2. **Campos de Medios de Pago (CampoMedioDePago)**:
   - Todos los campos asociados a cada medio de pago
   - Configuración de tipos de datos, requeridos, etc.

### Uso

#### Cargar el fixture en una nueva base de datos:

```bash
python manage.py loaddata mediosfinancieros_data
```

#### Cargar el fixture en una app específica:

```bash
python manage.py loaddata mediosfinancieros_data --app medios_pago
```

#### Actualizar el fixture con nuevos datos:

```bash
python manage.py dumpdata medios_pago.MedioDePago medios_pago.CampoMedioDePago --indent 2 > medios_pago/fixtures/mediosfinancieros_data.json
```

### Notas

- El fixture preserva las primary keys (IDs) de los registros originales
- Los campos de texto pueden tener caracteres especiales debido a la codificación
- Al cargar el fixture, los registros con IDs existentes serán actualizados
- Si hay foreign keys a otros modelos, asegúrate de cargar primero sus fixtures

### Medios incluidos

1. **Banco local** (ID: 1)
   - Template: bank_local_ar
   - Comisión: 3.0%
   - Campos: account_number, bank_name, account_holder, cbu_cvu, ruc

2. **Tarjeta de Crédito Internacional** (ID: 2)
   - Template: stripe_card
   - Comisión: 2.9%
   - Campos: card_number, exp_month, exp_year, cvc, bank_name

3. **Billetera Electrónica** (ID: 3)
   - Template: billetera_electronica_py
   - Comisión: 5.0%
   - Campos: wallet_phone, bank_name, account_holder, document_number

### Dependencias

Este fixture depende de:
- Migraciones de medios_pago aplicadas
- No tiene dependencias de otros fixtures (es standalone)
