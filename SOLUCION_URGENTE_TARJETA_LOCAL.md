# 🚨 SOLUCIÓN URGENTE - Tarjeta Local Detectada como Stripe

## ❌ Problema Identificado

El medio de pago **"Tarjeta de Crédito/Débito Local"** está siendo procesado por Stripe cuando debería usar el sistema local de tarjetas.

### Causa Raíz

El campo `tipo_medio` del medio de pago está configurado como **`'stripe'`** en la base de datos:

```
Medio de pago: Tarjeta de Crédito/Débito Local
Tipo medio: stripe  ← PROBLEMA AQUÍ
✅ DETECTADO COMO STRIPE por tipo_medio='stripe'
```

## ✅ Solución Inmediata

### Opción 1: Desde Django Admin (Recomendado)

1. **Acceder al Admin**: `http://localhost:8000/admin/`

2. **Ir a Medios de Pago**: 
   - Navegar a `Medios de Pago` → `Medios de Pago`
   - Buscar "Tarjeta de Crédito/Débito Local"

3. **Editar el medio de pago**:
   - Buscar el campo **"Tipo medio"**
   - **Cambiar de**: `stripe`
   - **Cambiar a**: `tarjeta` (o `tarjeta_local`, `tarjeta_debito_credito`)

4. **Guardar**

### Opción 2: Desde Django Shell

```bash
python manage.py shell
```

```python
from medios_pago.models import MedioDePago

# Buscar el medio de pago
medio = MedioDePago.objects.get(id=4)
# O buscar por nombre:
# medio = MedioDePago.objects.get(nombre='Tarjeta de Crédito/Débito Local')

print(f"Medio: {medio.nombre}")
print(f"Tipo actual: {medio.tipo_medio}")

# CAMBIAR el tipo
medio.tipo_medio = 'tarjeta'  # O 'tarjeta_local'
medio.save()

print(f"✅ Tipo actualizado a: {medio.tipo_medio}")
```

### Opción 3: SQL Directo (Solo si tienes acceso)

```sql
-- Ver el tipo actual
SELECT id, nombre, tipo_medio 
FROM medios_pago_mediodepago 
WHERE nombre LIKE '%Local%';

-- Actualizar el tipo
UPDATE medios_pago_mediodepago 
SET tipo_medio = 'tarjeta' 
WHERE id = 4;

-- Verificar el cambio
SELECT id, nombre, tipo_medio 
FROM medios_pago_mediodepago 
WHERE id = 4;
```

## 🔍 Verificación

Después de aplicar la solución, verifica que funcione:

1. **Intenta realizar una compra** con la tarjeta local

2. **Verifica los logs**:
   ```
   Tipo medio: tarjeta  ← Debe decir 'tarjeta', NO 'stripe'
   [COMPRA] Procesando pago con tarjeta de débito/crédito
   ```

3. **No debe aparecer**:
   - ❌ "DETECTADO COMO STRIPE"
   - ❌ "REDIRIGIENDO A PROCESAMIENTO STRIPE"
   - ❌ "PROCESANDO PAGO CON STRIPE"

4. **Debe aparecer**:
   - ✅ "Procesando pago con tarjeta de débito/crédito"
   - ✅ "[PAGO_TARJETA] Iniciando pago..."

## 📋 Valores Correctos para tipo_medio

| Medio de Pago | tipo_medio Correcto | ❌ NO usar |
|---------------|---------------------|-----------|
| Tarjeta Local (Débito/Crédito) | `tarjeta`, `tarjeta_local`, `tarjeta_debito`, `tarjeta_credito` | `stripe` |
| Tarjeta Stripe | `stripe`, `stripe_card` | `tarjeta` |
| Billetera Digital | `billetera`, `billetera_electronica` | `stripe`, `tarjeta` |
| Cuenta Bancaria | `transferencia`, `banco`, `cuenta_bancaria` | `stripe`, `tarjeta` |

## 🔄 Lógica de Detección (Referencia)

El sistema detecta el tipo de pago en `transacciones/views.py`:

```python
tipo_medio = medio_datos.get('tipo', '').lower()

# 1. Billetera
if 'billetera' in tipo_medio:
    → realizar_pago_billetera()

# 2. Tarjeta LOCAL (NO Stripe)
elif ('tarjeta' in tipo_medio or 'crédito' in tipo_medio or 'débito' in tipo_medio) 
     and 'stripe' not in tipo_medio.lower():
    → realizar_pago_tarjeta()

# 3. Transferencia bancaria
else:
    → realizar_transferencia_bancaria()
```

**Y en** `operacion_divisas/views.py` detecta Stripe:

```python
# Verifica si es Stripe
if medio_obj.medio_de_pago.tipo_medio == 'stripe':  ← AQUÍ COMPARA
    → Procesar con Stripe
```

## 🎯 Recomendaciones

### Para Evitar Confusiones Futuras

1. **Nombres claros**:
   - ✅ "Tarjeta de Crédito/Débito Local"
   - ✅ "Tarjeta Stripe"
   - ❌ "Tarjeta de Crédito/Débito" (ambiguo)

2. **Tipos consistentes**:
   - Usa `tipo_medio = 'tarjeta'` para tarjetas locales
   - Usa `tipo_medio = 'stripe'` SOLO para Stripe
   - Documenta en fixture o README

3. **Validación en Admin**:
   Puedes agregar validación en `medios_pago/admin.py`:
   ```python
   def save_model(self, request, obj, form, change):
       # Validar que tarjetas locales no usen tipo 'stripe'
       if 'local' in obj.nombre.lower() and obj.tipo_medio == 'stripe':
           messages.warning(request, 
               "⚠️ Un medio LOCAL no debería tener tipo 'stripe'")
       super().save_model(request, obj, form, change)
   ```

## 📊 Diagnóstico Rápido

Ejecuta este script para ver todos tus medios de pago:

```python
from medios_pago.models import MedioDePago

print("=" * 60)
print("MEDIOS DE PAGO CONFIGURADOS")
print("=" * 60)

for medio in MedioDePago.objects.all():
    es_stripe = medio.tipo_medio == 'stripe'
    tiene_local = 'local' in medio.nombre.lower()
    
    icono = "⚠️" if (es_stripe and tiene_local) or (not es_stripe and not tiene_local and 'stripe' in medio.nombre.lower()) else "✅"
    
    print(f"\n{icono} ID: {medio.id}")
    print(f"   Nombre: {medio.nombre}")
    print(f"   Tipo: {medio.tipo_medio}")
    print(f"   Estado: {medio.estado}")
    
    if es_stripe and tiene_local:
        print(f"   🚨 PROBLEMA: Medio 'Local' con tipo 'stripe'")
    elif not es_stripe and 'stripe' in medio.nombre.lower():
        print(f"   🚨 PROBLEMA: Medio 'Stripe' sin tipo 'stripe'")

print("\n" + "=" * 60)
```

## 📞 Soporte

Si después de aplicar la solución sigue sin funcionar:

1. Verifica que guardaste los cambios
2. Reinicia el servidor Django
3. Limpia caché del navegador
4. Verifica los logs en consola
5. Ejecuta el script de diagnóstico

---

**Solución creada**: Octubre 2024  
**Para**: Global Exchange - Sistema de Pagos
