# Fixtures del Módulo Clientes

Este directorio contiene los fixtures (datos iniciales/de prueba) para el módulo de clientes.

## Fixtures Disponibles

### 📋 clientes_data.json
Contiene los datos base de clientes del sistema.

**Uso:**
```bash
python manage.py loaddata clientes_data
```

---

### 💳 mediosfinancieroscliente_data.json
Contiene los 5 medios de pago configurados para el "Cliente General" (ID: 1).

**Contenido:**
- 1 Banco local (Principal)
- 1 Tarjeta de Crédito Internacional (Stripe)
- 1 Billetera Electrónica
- 2 Tarjetas Locales (Banco Guaraní - Débito y Crédito)

**Dependencias requeridas:**
1. Cliente "Cliente General" (ID: 1) debe existir
2. Medios de Pago (IDs: 1, 2, 3, 4) - usar `mediosfinancieros_data.json`
3. Usuarios (IDs: 4, 11)

**Uso rápido:**
```bash
# Opción 1: Usar el comando directo
python manage.py loaddata mediosfinancieroscliente_data

# Opción 2: Usar el script de ayuda (recomendado)
python scripts/load_medios_cliente_general.py

# Verificar dependencias sin cargar
python scripts/load_medios_cliente_general.py --verificar-solo
```

**Documentación detallada:** Ver [README_MEDIOS_CLIENTE.md](./README_MEDIOS_CLIENTE.md)

---

## Orden de Carga Recomendado

Para cargar todos los fixtures relacionados en el orden correcto:

```bash
# 1. Usuarios base (si no existen)
python manage.py loaddata usuarios_base

# 2. Clientes
python manage.py loaddata clientes_data

# 3. Medios de Pago disponibles
python manage.py loaddata mediosfinancieros_data

# 4. Medios financieros del Cliente General
python manage.py loaddata mediosfinancieroscliente_data
```

## Scripts de Ayuda

### load_medios_cliente_general.py

Script ubicado en `scripts/load_medios_cliente_general.py` que facilita la carga del fixture de medios financieros del cliente.

**Características:**
- ✅ Verifica automáticamente todas las dependencias
- ✅ Muestra el estado actual antes y después de la carga
- ✅ Permite verificación sin cargar datos (`--verificar-solo`)
- ✅ Confirma antes de sobrescribir datos existentes

**Uso:**
```bash
# Solo verificar dependencias
python scripts/load_medios_cliente_general.py --verificar-solo

# Cargar el fixture (con confirmación)
python scripts/load_medios_cliente_general.py
```

## Actualizar Fixtures

### Actualizar mediosfinancieroscliente_data.json

Si modificas los medios del Cliente General y quieres actualizar el fixture:

```bash
# 1. Obtener IDs actuales
python manage.py shell -c "from clientes.models import ClienteMedioDePago; print(list(ClienteMedioDePago.objects.filter(cliente_id=1).values_list('id', flat=True)))"

# 2. Exportar con los IDs obtenidos (ejemplo con IDs 1,2,3,4,5)
python manage.py dumpdata clientes.ClienteMedioDePago --indent 2 --pks 1,2,3,4,5 > clientes/fixtures/mediosfinancieroscliente_data.json
```

## Notas Importantes

⚠️ **Dependencias entre Fixtures:**
- Los fixtures de clientes pueden tener dependencias con:
  - `users` (usuarios del sistema)
  - `medios_pago` (medios de pago disponibles)
  - `divisas` (monedas del sistema)

⚠️ **IDs Fijos:**
- Los fixtures preservan los IDs originales
- Asegúrate de que no haya conflictos con datos existentes
- En producción, considera usar IDs altos o UUIDs

⚠️ **Datos Sensibles:**
- Los números de tarjeta y códigos CVV son de prueba
- No usar estos datos en producción con APIs reales
- Los números de tarjeta de ejemplo (4242...) son válidos solo en modo test de Stripe

## Verificación Post-Carga

Para verificar que los fixtures se cargaron correctamente:

```bash
# Verificar Cliente General y sus medios
python manage.py shell -c "from clientes.models import ClienteMedioDePago, Cliente; c = Cliente.objects.get(id=1); print(f'Cliente: {c.nombre_completo}'); print(f'Medios configurados: {c.medios_pago.count()}'); for m in c.medios_pago.all(): print(f'  - {m}')"
```

## Soporte

Para más información sobre fixtures específicos, consulta:
- [README_MEDIOS_CLIENTE.md](./README_MEDIOS_CLIENTE.md) - Detalles del fixture de medios financieros
- `medios_pago/fixtures/README.md` - Detalles de medios de pago disponibles
