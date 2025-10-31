# Fixtures de Medios Financieros de Clientes

## mediosfinancieroscliente_data.json

Este fixture contiene los medios financieros configurados para el cliente "Cliente General" (ID: 1).

### Contenido

El fixture incluye **5 medios de pago** del Cliente General:

1. **Banco local** (ID: 1) - **PRINCIPAL**
   - Medio: Banco local (medios_pago.MedioDePago ID: 1)
   - Entidad: Banco Guaraní
   - Número de cuenta: 0003 3344 4
   - Titular: María
   - CBU/CVU: 2131-3131-3323-3112-1312-31
   - RUC: 12345678

2. **Tarjeta de Crédito Internacional** (ID: 2)
   - Medio: Tarjeta de Crédito Internacional (medios_pago.MedioDePago ID: 2)
   - Entidad: Stripe
   - Número: 4242 4242 4242 4242
   - Vencimiento: 01/2030
   - CVV: 123

3. **Billetera Electrónica** (ID: 3)
   - Medio: Billetera Electrónica (medios_pago.MedioDePago ID: 3)
   - Entidad: Billetera Digital
   - Teléfono: 0982222222
   - Titular: María
   - Documento: 12345678

4. **Tarjeta de Débito Banco Guaraní** (ID: 4)
   - Medio: Tarjeta Local (medios_pago.MedioDePago ID: 4)
   - Entidad: Banco Guaraní
   - Número: 4222 2222 2222 2222
   - Vencimiento: 06/2026
   - CVV: 456
   - Titular: Tarjeta de Débito Banco Guaraní

5. **Tarjeta de Crédito Banco Guaraní** (ID: 5)
   - Medio: Tarjeta Local (medios_pago.MedioDePago ID: 4)
   - Entidad: Banco Guaraní
   - Número: 4444 4444 4444 4444
   - Vencimiento: 05/2029
   - CVV: 321
   - Titular: Tarjeta de Crédito Banco Guaraní

### Dependencias

⚠️ **IMPORTANTE**: Este fixture requiere que los siguientes datos estén cargados previamente:

1. **Cliente "Cliente General"** (ID: 1) - de `clientes.Cliente`
2. **Medios de Pago** (IDs: 1, 2, 3, 4) - usar fixture `mediosfinancieros_data.json`
3. **Usuario creador** (IDs: 4, 11) - de `users.CustomUser`

### Orden de carga recomendado

```bash
# 1. Cargar usuarios (si no existen)
python manage.py loaddata usuarios_base  # o tu fixture de usuarios

# 2. Cargar cliente "Cliente General" (si no existe)
python manage.py loaddata clientes_base  # o tu fixture de clientes

# 3. Cargar los medios de pago disponibles
python manage.py loaddata mediosfinancieros_data

# 4. Finalmente, cargar los medios financieros del cliente
python manage.py loaddata mediosfinancieroscliente_data
```

### Uso

#### Cargar el fixture:

```bash
python manage.py loaddata mediosfinancieroscliente_data
```

#### Cargar en una app específica:

```bash
python manage.py loaddata mediosfinancieroscliente_data --app clientes
```

#### Actualizar el fixture con datos actuales:

```bash
# Obtener IDs de medios del Cliente General
python manage.py shell -c "from clientes.models import ClienteMedioDePago; print(list(ClienteMedioDePago.objects.filter(cliente_id=1).values_list('id', flat=True)))"

# Exportar usando los IDs obtenidos
python manage.py dumpdata clientes.ClienteMedioDePago --indent 2 --pks 1,2,3,4,5 > clientes/fixtures/mediosfinancieroscliente_data.json
```

### Notas importantes

- ✅ Los medios de pago mantienen su asociación con el cliente ID: 1 (Cliente General)
- ✅ El medio ID: 1 está marcado como **principal** (`es_principal: true`)
- ✅ Todos los medios están activos (`es_activo: true`)
- ⚠️ Los IDs de los registros se preservan, asegúrate de que no entren en conflicto con datos existentes
- ⚠️ Las fechas de creación y actualización se preservan del momento original
- ⚠️ Los datos sensibles (números de tarjeta, CVV) son de ejemplo/prueba

### Verificación post-carga

Para verificar que los medios se cargaron correctamente:

```bash
python manage.py shell -c "from clientes.models import ClienteMedioDePago, Cliente; c = Cliente.objects.get(id=1); print(f'Cliente: {c.nombre_completo}'); print(f'Medios de pago: {c.medios_pago.count()}'); for m in c.medios_pago.all(): print(f'  - {m}')"
```

### Estructura del modelo

El fixture mantiene la estructura completa del modelo `ClienteMedioDePago`:
- `cliente`: FK a Cliente (ID: 1)
- `medio_de_pago`: FK a MedioDePago (IDs: 1, 2, 3, 4)
- `datos_campos`: JSONField con los datos específicos de cada medio
- `es_activo`: Boolean (todos true)
- `es_principal`: Boolean (solo true para ID: 1)
- `fecha_creacion`: DateTime
- `fecha_actualizacion`: DateTime
- `creado_por`: FK a CustomUser (IDs: 4, 11)

### Casos de uso

Este fixture es útil para:
- 🔄 Restaurar la configuración de medios de pago del Cliente General
- 🧪 Crear ambientes de prueba con datos consistentes
- 📦 Desplegar en nuevos entornos con datos de ejemplo
- 🎓 Capacitación y demos con datos predefinidos
- 🔧 Testing automatizado que requiera medios de pago configurados
