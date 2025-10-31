# Fixture: Medios Financieros del Cliente General

## ✅ Fixture Creado Exitosamente

**Archivo:** `clientes/fixtures/mediosfinancieroscliente_data.json`

### 📊 Contenido del Fixture

El fixture contiene **5 medios de pago** del cliente "Cliente General" (ID: 1):

| # | Tipo de Medio | ID | Principal | Estado | Entidad |
|---|---------------|----|-----------| -------|---------|
| 1 | Banco local | 1 | ⭐ Sí | ✓ Activo | Banco Guaraní |
| 2 | Tarjeta Internacional (Stripe) | 2 | No | ✓ Activo | Stripe |
| 3 | Billetera Electrónica | 3 | No | ✓ Activo | Billetera Digital |
| 4 | Tarjeta Local (Débito) | 4 | No | ✓ Activo | Banco Guaraní |
| 5 | Tarjeta Local (Crédito) | 5 | No | ✓ Activo | Banco Guaraní |

### 🔗 Dependencias

Este fixture requiere que estén cargados previamente:

1. **Cliente "Cliente General"** (ID: 1)
2. **Medios de Pago base** (IDs: 1, 2, 3, 4) - Fixture: `mediosfinancieros_data.json`
3. **Usuarios** (IDs: 4, 11) - Opcional, pero recomendado

### 📦 Uso

#### Opción 1: Comando directo de Django

```bash
python manage.py loaddata mediosfinancieroscliente_data
```

#### Opción 2: Script de ayuda (Recomendado)

El script verifica dependencias y muestra el estado antes/después:

```bash
# Solo verificar sin cargar
python scripts/load_medios_cliente_general.py --verificar-solo

# Cargar el fixture
python scripts/load_medios_cliente_general.py
```

### 🔍 Verificación

Para verificar que el fixture se cargó correctamente:

```bash
# Usando el script de resumen
python scripts/mostrar_resumen_medios_cliente.py

# O con Django shell
python manage.py shell -c "from clientes.models import Cliente; c = Cliente.objects.get(id=1); print(f'Medios: {c.medios_pago.count()}')"
```

### 📝 Scripts Disponibles

| Script | Descripción | Uso |
|--------|-------------|-----|
| `load_medios_cliente_general.py` | Carga el fixture con verificación de dependencias | `python scripts/load_medios_cliente_general.py` |
| `mostrar_resumen_medios_cliente.py` | Muestra un resumen detallado del contenido | `python scripts/mostrar_resumen_medios_cliente.py` |

### 📋 Orden de Carga Completo

Para configurar el sistema desde cero:

```bash
# 1. Usuarios (si es necesario)
python manage.py loaddata usuarios_base

# 2. Clientes
python manage.py loaddata clientes_data

# 3. Medios de pago disponibles
python manage.py loaddata mediosfinancieros_data

# 4. Medios del Cliente General
python manage.py loaddata mediosfinancieroscliente_data
```

### 🔄 Actualizar el Fixture

Si modificas los medios del Cliente General:

```bash
# 1. Ver IDs actuales
python manage.py shell -c "from clientes.models import ClienteMedioDePago; print(list(ClienteMedioDePago.objects.filter(cliente_id=1).values_list('id', flat=True)))"

# 2. Exportar con los IDs obtenidos
python manage.py dumpdata clientes.ClienteMedioDePago --indent 2 --pks 1,2,3,4,5 > clientes/fixtures/mediosfinancieroscliente_data.json
```

### 📚 Documentación Adicional

- **Detalles completos:** `clientes/fixtures/README_MEDIOS_CLIENTE.md`
- **General de fixtures:** `clientes/fixtures/README.md`
- **Medios de pago base:** `medios_pago/fixtures/README.md`

### ⚠️ Notas Importantes

- ✅ Los medios mantienen su asociación con el Cliente General (ID: 1)
- ✅ Los IDs de los registros se preservan (1, 2, 3, 4, 5)
- ✅ El medio ID: 1 está marcado como **principal**
- ⚠️ Los números de tarjeta y CVV son de ejemplo/prueba
- ⚠️ Al cargar, los registros existentes con los mismos IDs serán actualizados

### 🎯 Casos de Uso

Este fixture es ideal para:

- 🔄 **Restauración:** Recuperar la configuración de medios del Cliente General
- 🧪 **Testing:** Crear ambientes de prueba con datos consistentes
- 📦 **Deploy:** Configurar nuevos entornos rápidamente
- 🎓 **Demos:** Capacitación con datos predefinidos
- 🔧 **Desarrollo:** Tests automatizados con medios preconfigurados

### ✅ Estado de Verificación

```
✅ Fixture creado: mediosfinancieroscliente_data.json
✅ 5 medios de pago exportados
✅ Dependencias verificadas
✅ Scripts de ayuda creados
✅ Documentación completa
✅ Probado exitosamente
```

---

**Creado:** 31 de octubre de 2025  
**Última actualización:** 31 de octubre de 2025
