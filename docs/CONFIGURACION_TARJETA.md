# Guía de Configuración - Pagos con Tarjeta de Débito/Crédito

## 📋 Tabla de Contenidos
- [Requisitos previos](#requisitos-previos)
- [Configuración paso a paso](#configuración-paso-a-paso)
- [Verificación de la instalación](#verificación-de-la-instalación)
- [Resolución de problemas](#resolución-de-problemas)

---

## ✅ Requisitos Previos

Antes de configurar los pagos con tarjeta, asegúrate de tener:

1. **Django** instalado y configurado
2. **Módulo `banco`** con los modelos:
   - `EntidadBancaria`
   - `Cuenta`
   - `TarjetaDebito`
   - `TarjetaCredito`
   - `PagoTarjeta`
3. **Módulo `medios_pago`** configurado
4. **Base de datos** con migraciones aplicadas

---

## 📝 Configuración Paso a Paso

### Paso 1: Configurar la Cuenta Empresa

La cuenta de la empresa debe existir para recibir los pagos:

```python
from banco.models import EntidadBancaria, Cuenta

# 1. Crear/verificar la entidad bancaria
entidad_empresa, _ = EntidadBancaria.objects.get_or_create(
    codigo='BPY',
    defaults={
        'nombre': 'Banco Paraguayo',
        'tipo': 'banco'
    }
)

# 2. Crear/verificar la cuenta de la empresa
cuenta_empresa, _ = Cuenta.objects.get_or_create(
    numero_cuenta='000111222',
    entidad=entidad_empresa,
    defaults={
        'tipo_cuenta': 'ahorros',
        'saldo': Decimal('0.00'),
        'moneda': 'PYG'
    }
)

print(f"✓ Cuenta empresa configurada: {cuenta_empresa.numero_cuenta}")
print(f"  Saldo actual: ₲{cuenta_empresa.saldo:,.0f}")
```

### Paso 2: Crear Medio de Pago en el Admin

1. **Acceder al Django Admin**: `/admin/`

2. **Ir a Medios de Pago** → **Agregar medio de pago**

3. **Configurar para Tarjeta de Débito**:
   ```
   Nombre: Tarjeta de Débito
   Tipo: Tarjeta
   Estado: Activo
   Requiere validación: Sí (opcional)
   
   Campos dinámicos:
   - Número de tarjeta (tipo: text, obligatorio)
   - Mes de vencimiento (tipo: number, obligatorio)
   - Año de vencimiento (tipo: number, obligatorio)
   - Código de seguridad (tipo: password, obligatorio)
   - Entidad (tipo: select, obligatorio)
   ```

4. **Configurar para Tarjeta de Crédito**:
   ```
   Nombre: Tarjeta de Crédito
   Tipo: Tarjeta
   Estado: Activo
   Requiere validación: Sí (opcional)
   
   Campos dinámicos:
   - card_number (tipo: text, obligatorio)
   - exp_month (tipo: number, obligatorio)
   - exp_year (tipo: number, obligatorio)
   - cvc (tipo: password, obligatorio)
   - Entidad (tipo: select, obligatorio)
   ```

   > 💡 **Nota**: Los nombres de campos pueden variar. El sistema busca:
   > - Número: `numero`, `number`, `card_number`, `tarjeta`
   > - Mes: `mes`, `month`, `exp_month`
   > - Año: `año`, `anho`, `year`, `exp_year`
   > - CVV: `cvv`, `cvc`, `codigo`, `seguridad`

### Paso 3: Registrar Tarjetas en el Banco

#### A. Tarjetas de Débito

```python
from banco.models import TarjetaDebito, Cuenta, EntidadBancaria
from decimal import Decimal

# 1. Obtener/crear entidad bancaria
entidad, _ = EntidadBancaria.objects.get_or_create(
    codigo='ITAU',
    defaults={'nombre': 'Banco Itaú', 'tipo': 'banco'}
)

# 2. Crear cuenta asociada
cuenta = Cuenta.objects.create(
    numero_cuenta='001234567',
    entidad=entidad,
    tipo_cuenta='corriente',
    saldo=Decimal('500000.00'),  # ₲500,000
    moneda='PYG'
)

# 3. Crear tarjeta de débito
tarjeta_debito = TarjetaDebito.objects.create(
    numero='4111111111111111',
    mes_vencimiento=12,
    anho_vencimiento=2027,
    cvv='123',
    entidad=entidad,
    cuenta=cuenta,
    tipo='visa'
)

print(f"✓ Tarjeta de débito creada: ****{tarjeta_debito.numero[-4:]}")
```

#### B. Tarjetas de Crédito

```python
from banco.models import TarjetaCredito

# Crear tarjeta de crédito
tarjeta_credito = TarjetaCredito.objects.create(
    numero='5500000000000004',
    mes_vencimiento=6,
    anho_vencimiento=2028,
    cvv='456',
    entidad=entidad,
    tipo='mastercard',
    limite_credito=Decimal('1000000.00'),  # ₲1,000,000
    saldo_usado=Decimal('0.00')
)

print(f"✓ Tarjeta de crédito creada: ****{tarjeta_credito.numero[-4:]}")
print(f"  Crédito disponible: ₲{tarjeta_credito.disponible():,.0f}")
```

### Paso 4: Asignar Medio de Pago a Clientes

```python
from clientes.models import Cliente, ClienteMedioDePago
from medios_pago.models import MedioDePago

# 1. Obtener cliente
cliente = Cliente.objects.get(id=1)  # Ajustar según tu sistema

# 2. Obtener medio de pago
medio_debito = MedioDePago.objects.get(nombre='Tarjeta de Débito')

# 3. Asignar al cliente
cliente_medio, created = ClienteMedioDePago.objects.get_or_create(
    cliente=cliente,
    medio=medio_debito,
    defaults={
        'estado': 'activo',
        'es_preferido': False
    }
)

if created:
    print(f"✓ Medio asignado al cliente: {cliente.email}")
else:
    print(f"✓ Cliente ya tiene el medio asignado")
```

### Paso 5: Cargar Datos de Prueba (Opcional)

Si tienes fixtures preparados:

```bash
# Cargar datos del banco (incluye tarjetas)
python manage.py loaddata banco/fixtures/banco_data.json

# Cargar medios de pago
python manage.py loaddata medios_pago/fixtures/medios_pago.json
```

---

## 🧪 Verificación de la Instalación

### Opción 1: Script de Prueba Automático

```bash
python manage.py shell < scripts/test_pago_tarjeta.py
```

Esto ejecutará 5 tests:
1. ✅ Verificación de configuración básica
2. ✅ Pago con tarjeta de débito
3. ✅ Pago con tarjeta de crédito
4. ✅ Tarjeta no encontrada
5. ✅ Datos incompletos

### Opción 2: Prueba Manual en el Shell

```python
python manage.py shell

# Importar función
from transacciones.views import realizar_pago_tarjeta
from decimal import Decimal

# Preparar datos
medio_datos = {
    'tipo': 'Tarjeta de Débito',
    'datos_campos': {
        'Número de tarjeta': '4111111111111111',
        'Mes de vencimiento': '12',
        'Año de vencimiento': '2027',
        'Código de seguridad': '123',
        'Entidad': 'Banco Itaú'
    }
}

# Ejecutar pago de prueba
resultado = realizar_pago_tarjeta(
    medio_datos=medio_datos,
    monto=Decimal('10000.00'),
    referencia='PRUEBA-001'
)

# Ver resultado
print(f"OK: {resultado.get('ok')}")
print(f"Mensaje: {resultado.get('message')}")
if resultado.get('ok'):
    print(f"Comprobante: {resultado.get('comprobante')}")
```

### Opción 3: Verificación en la Interfaz

1. Iniciar sesión como cliente
2. Ir a **Comprar Divisas**
3. Seleccionar divisa y monto
4. En **Medio de Pago**, seleccionar **Tarjeta de Débito** o **Tarjeta de Crédito**
5. Completar datos de la tarjeta
6. Presionar **Confirmar Operación**
7. Verificar mensaje de éxito

---

## 🔧 Resolución de Problemas

### Error: "Cuenta empresa no encontrada"

**Síntoma**: `{'ok': False, 'code': '96', 'message': 'Cuenta empresa no encontrada'}`

**Solución**:
```python
from banco.models import EntidadBancaria, Cuenta
from decimal import Decimal

entidad = EntidadBancaria.objects.get(codigo='BPY')
Cuenta.objects.create(
    numero_cuenta='000111222',
    entidad=entidad,
    tipo_cuenta='ahorros',
    saldo=Decimal('0.00')
)
```

### Error: "Tarjeta no encontrada"

**Síntoma**: `{'ok': False, 'code': '14', 'message': 'Tarjeta de débito/crédito no encontrada'}`

**Posibles causas**:
1. La tarjeta no está registrada en la base de datos
2. Los datos no coinciden exactamente (número, mes, año, CVV)
3. La entidad bancaria es diferente

**Verificación**:
```python
from banco.models import TarjetaDebito

# Buscar por número
tarjeta = TarjetaDebito.objects.filter(numero='4111111111111111').first()
if tarjeta:
    print(f"Vencimiento: {tarjeta.mes_vencimiento}/{tarjeta.anho_vencimiento}")
    print(f"CVV: {tarjeta.cvv}")
    print(f"Entidad: {tarjeta.entidad.nombre}")
else:
    print("Tarjeta no encontrada - debe registrarse")
```

### Error: "Saldo insuficiente en cuenta"

**Síntoma**: `{'ok': False, 'code': '51', 'message': 'Saldo insuficiente en cuenta'}`

**Solución**: Agregar saldo a la cuenta:
```python
from banco.models import Cuenta

cuenta = Cuenta.objects.get(numero_cuenta='001234567')
cuenta.saldo += Decimal('100000.00')  # Agregar ₲100,000
cuenta.save()
print(f"Nuevo saldo: ₲{cuenta.saldo:,.0f}")
```

### Error: "Crédito insuficiente"

**Síntoma**: `{'ok': False, 'code': '51', 'message': 'Crédito insuficiente'}`

**Solución**: Aumentar límite o reducir saldo usado:
```python
from banco.models import TarjetaCredito

tarjeta = TarjetaCredito.objects.get(numero='5500000000000004')

# Opción 1: Aumentar límite
tarjeta.limite_credito = Decimal('2000000.00')
tarjeta.save()

# Opción 2: Pagar deuda (reducir saldo usado)
tarjeta.saldo_usado -= Decimal('500000.00')
tarjeta.save()

print(f"Disponible: ₲{tarjeta.disponible():,.0f}")
```

### Error: "Datos de tarjeta incompletos"

**Síntoma**: `{'ok': False, 'code': '12', 'message': 'Datos de tarjeta incompletos'}`

**Solución**: Verificar que todos los campos estén presentes:
- Número de tarjeta
- Mes de vencimiento
- Año de vencimiento
- CVV/CVC

### Error: Stripe procesa el pago en vez del sistema local

**Síntoma**: El pago se procesa con Stripe cuando debería ser local

**Causa**: La entidad del medio de pago es "Stripe"

**Solución**: Asegurarse de que la entidad NO sea Stripe:
```python
# Verificar entidad del medio de pago
medio_datos = {
    'datos_campos': {
        'Entidad': 'Banco Itaú'  # ✅ Correcto
        # 'Entidad': 'Stripe'    # ❌ Esto usará Stripe
    }
}
```

### No se ve el medio de pago en el formulario

**Verificar**:
1. El medio está creado en Admin
2. El medio está activo
3. El medio está asignado al cliente
4. Los campos dinámicos están configurados

```python
from medios_pago.models import MedioDePago
from clientes.models import ClienteMedioDePago

# Verificar medio
medio = MedioDePago.objects.filter(nombre__icontains='tarjeta').first()
print(f"Medio: {medio}")
print(f"Estado: {medio.estado if medio else 'N/A'}")

# Verificar asignación
cliente_id = 1
asignaciones = ClienteMedioDePago.objects.filter(
    cliente_id=cliente_id,
    medio__nombre__icontains='tarjeta'
)
print(f"Medios asignados: {asignaciones.count()}")
```

---

## 📊 Verificación de Transacciones

### Ver últimos pagos con tarjeta:

```python
from banco.models import PagoTarjeta

pagos = PagoTarjeta.objects.all().order_by('-fecha')[:10]
for pago in pagos:
    tipo = 'Débito' if pago.tarjeta_debito else 'Crédito'
    tarjeta = pago.tarjeta_debito or pago.tarjeta_credito
    print(f"{pago.fecha} | {tipo} | ****{tarjeta.numero[-4:]} | ₲{pago.monto:,.0f} | {pago.comprobante}")
```

### Ver saldo de cuenta empresa:

```python
from banco.models import Cuenta

cuenta = Cuenta.objects.get(numero_cuenta='000111222')
print(f"Saldo empresa: ₲{cuenta.saldo:,.0f}")
```

---

## 📚 Recursos Adicionales

- [Documentación Técnica](PAGO_TARJETA_DEBITO_CREDITO.md)
- [Script de Prueba](../scripts/test_pago_tarjeta.py)
- [Comparación con Otros Métodos](PAGO_TARJETA_DEBITO_CREDITO.md#comparación-con-otros-métodos-de-pago)

---

## ✅ Checklist de Configuración

- [ ] Cuenta empresa creada (BPY / 000111222)
- [ ] Medios de pago creados en Admin
- [ ] Campos dinámicos configurados
- [ ] Tarjetas registradas en módulo banco
- [ ] Medios asignados a clientes
- [ ] Tests ejecutados exitosamente
- [ ] Logs verificados sin errores

---

**Última actualización**: Diciembre 2024
