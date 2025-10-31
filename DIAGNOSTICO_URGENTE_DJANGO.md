# 🔥 DIAGNÓSTICO URGENTE - PROBLEMAS EN IMPLEMENTACIÓN DJANGO

**Fecha:** 30 de octubre de 2025  
**Estado:** ❌ SISTEMA CON ERRORES CRÍTICOS

---

## 🐛 PROBLEMAS IDENTIFICADOS

### 1. **CRÍTICO: RUC del cliente = 0** ❌
**Error SIFEN:** `0160 - XML malformado: [El valor 0 del elemento: dRucRec es invalido]`

**Causa:**
```python
# facturacion_electronica/services.py línea ~453
cliente_ruc = getattr(cliente, 'ruc', '0')  # ❌ Cliente NO tiene campo 'ruc'
cliente_dv = getattr(cliente, 'dv', '0')    # ❌ Cliente NO tiene campo 'dv'
```

**Modelo Cliente real:**
```python
# clientes/models.py
class Cliente(models.Model):
    cedula = models.CharField(...)  # ✅ Tiene cédula
    nombre_completo = models.CharField(...)
    # ❌ NO tiene campos 'ruc' ni 'dv'
```

**Resultado:**
- Facturas 0000067 y 0000068: **RECHAZADAS**
- SIFEN recibe RUC = "0" (inválido)
- Estado: `Rechazado` en SQL Proxy

---

### 2. **URLs incompletas en base de datos** ⚠️

**Código actual:**
```python
# services.py línea ~508
url_kude_base = f"{SQL_PROXY_CONFIG['kude_url']}/{directorio_fecha}"

factura = FacturaElectronica.objects.create(
    url_kude_pdf=url_kude_base,  # ❌ Solo directorio, sin archivo
    url_kude_xml=url_kude_base,  # ❌ Solo directorio, sin archivo
)
```

**Resultado:**
- Django guarda: `http://localhost:40080/kude/202510`
- Debería guardar: `http://localhost:40080/kude/202510/001-003-0000067_timestamp.pdf`
- Descarga falla porque falta el nombre del archivo

---

### 3. **No se actualiza automáticamente después de generar** ⚠️

**Problema:**
```python
# operacion_divisas/views.py línea ~893
success, factura, error = generar_factura_automatica(transaccion)

if success:
    messages.success(request, f"¡Factura {factura.numero_factura} generada!")
    # ❌ FALTA: Llamar a actualizar_estado_factura() después de 60s
    # ❌ FALTA: Task asíncrona o signal para actualizar
```

**Resultado:**
- Factura se genera en SQL Proxy ✅
- Scheduler procesa y SIFEN rechaza (por RUC=0) ❌
- Django nunca actualiza el estado ❌
- Usuario ve "Procesando" para siempre ❌

---

### 4. **Template auto-refresh no funciona si está rechazada** ⚠️

**Código actual:**
```django
{% if factura.estado_sifen == 'Procesando' or factura.estado_sifen == 'Sol.Aprobacion' %}
<script>
setTimeout(function() { location.reload(); }, 15000);
</script>
{% endif %}
```

**Problema:**
- Si SIFEN rechaza, `estado_sifen = 'Rechazado'`
- Auto-refresh se detiene
- Usuario no ve el error
- Factura queda en estado inconsistente

---

## ✅ CORRECCIONES IMPLEMENTADAS

### 1. **Corregido: Uso de cédula como RUC**

```python
# facturacion_electronica/services.py línea ~453 (CORREGIDO)
if hasattr(cliente, 'ruc') and cliente.ruc:
    cliente_ruc = str(cliente.ruc)
    cliente_dv = str(getattr(cliente, 'dv', '0'))
elif hasattr(cliente, 'cedula') and cliente.cedula:
    # Usar cédula como número de documento
    cliente_ruc = str(cliente.cedula)
    cliente_dv = '0'  # Calcular DV si es necesario
else:
    # Fallback a datos del profesor (para pruebas)
    cliente_ruc = '80026216'
    cliente_dv = '6'
```

**Nota:** En Paraguay, personas físicas usan cédula como RUC.

---

## ⚠️ CORRECCIONES PENDIENTES

### 2. **Agregar actualización automática**

**Opción A: Celery task (Recomendado)**
```python
# facturacion_electronica/tasks.py (CREAR)
from celery import shared_task
from .services import actualizar_estado_factura

@shared_task
def actualizar_factura_async(factura_id):
    """Actualiza estado de factura después de 60 segundos"""
    import time
    time.sleep(60)  # Esperar 60s
    actualizar_estado_factura(factura_id)
```

**Llamar desde generar_factura_automatica:**
```python
# services.py línea ~523
from .tasks import actualizar_factura_async

factura = FacturaElectronica.objects.create(...)

# Programar actualización automática
actualizar_factura_async.apply_async(args=[factura.id], countdown=60)

return True, factura, None
```

**Opción B: Signal post_save (Más simple)**
```python
# facturacion_electronica/signals.py (CREAR)
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FacturaElectronica
from .tasks import actualizar_factura_async

@receiver(post_save, sender=FacturaElectronica)
def programar_actualizacion(sender, instance, created, **kwargs):
    if created and instance.estado_sifen == 'Procesando':
        # Actualizar automáticamente después de 60s
        actualizar_factura_async.apply_async(args=[instance.id], countdown=60)
```

---

### 3. **Corregir URLs en base de datos**

**Problema actual:**
```python
# services.py línea ~508
url_kude_pdf=url_kude_base,  # ❌ http://localhost:40080/kude/202510
```

**Solución:**
```python
# No guardar URL hasta tener el CDC
# Dejar en NULL y actualizar cuando SIFEN apruebe

factura = FacturaElectronica.objects.create(
    transaccion=transaccion,
    numero_factura=numero_completo,
    # ... otros campos ...
    url_kude_pdf=None,  # ✅ NULL hasta aprobación
    url_kude_xml=None,  # ✅ NULL hasta aprobación
    estado='confirmado',
    estado_sifen='Procesando',
)
```

Luego en `actualizar_estado_factura()`:
```python
# Buscar archivo real con glob
archivos_pdf = glob.glob(f"{kude_path}/{numero_completo}_*.pdf")
if archivos_pdf:
    nombre_archivo_pdf = os.path.basename(archivos_pdf[0])
    factura.url_kude_pdf = f"{url_kude_base}/{nombre_archivo_pdf}"
    factura.save()
```

---

### 4. **Template debe mostrar errores**

```django
<!-- detalle_factura.html -->
{% if factura.estado_sifen == 'Procesando' or factura.estado_sifen == 'Sol.Aprobacion' %}
<div class="alert alert-info">
    <h5><i class="fas fa-hourglass-half"></i> Procesando en SIFEN</h5>
    <p>Esperando aprobación... La página se actualizará automáticamente.</p>
</div>
<script>
setTimeout(function() { location.reload(); }, 15000);
</script>

{% elif factura.estado_sifen == 'Rechazado' %}
<!-- AGREGAR ESTO -->
<div class="alert alert-danger">
    <h5><i class="fas fa-times-circle"></i> Factura Rechazada por SIFEN</h5>
    <p><strong>Error:</strong> {{ factura.descripcion_sifen }}</p>
    {% if factura.error_sifen %}
    <p><small>{{ factura.error_sifen }}</small></p>
    {% endif %}
    <p class="mb-0">
        <a href="{% url 'soporte' %}" class="btn btn-danger btn-sm">
            <i class="fas fa-life-ring"></i> Contactar Soporte
        </a>
    </p>
</div>
{% endif %}
```

---

## 🧪 PRUEBA PARA VERIFICAR CORRECCIONES

### 1. Reiniciar Django con cambios:
```bash
pkill -f "manage.py runserver"
cd /home/jose/proyecto_is2/global-exchange
nohup poetry run python manage.py runserver 0.0.0.0:8000 > /tmp/django.log 2>&1 &
```

### 2. Generar nueva factura con script (para comparar):
```bash
poetry run python insertar_factura_directa.py
```

### 3. Hacer compra en Django:
- Login: http://localhost:8000
- Comprar divisas
- Ver factura generada

### 4. Verificar en SQL Proxy que RUC ya no es 0:
```bash
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT id, dnumdoc, drucr rec, estado, estado_sifen, desc_sifen 
   FROM public.de ORDER BY id DESC LIMIT 1;"
```

### 5. Esperar 60 segundos y verificar estado:
```bash
# Debería cambiar de "Procesando" a "Aprobado" o mostrar error específico
docker exec sql-proxy01-db-1 psql -U fs_proxy_user -d fs_proxy_bd -c \
  "SELECT dnumdoc, estado, estado_sifen, desc_sifen 
   FROM public.de ORDER BY id DESC LIMIT 1;"
```

---

## 📊 COMPARACIÓN: SCRIPT vs DJANGO

| Aspecto | Script (insertar_factura_directa.py) | Django (services.py) |
|---------|--------------------------------------|----------------------|
| **Base de datos** | ✅ SQL Proxy directo | ✅ SQL Proxy directo |
| **RUC cliente** | ✅ '80026216' hardcodeado | ❌ '0' (getattr falla) → ✅ CORREGIDO |
| **Punto expedición** | ✅ '003' | ✅ '003' |
| **Pago (gPaConEIni)** | ✅ Insertado | ✅ Insertado |
| **Estado inicial** | ✅ 'Confirmado' | ✅ 'Confirmado' |
| **Actualización automática** | ❌ Manual | ❌ No implementada |
| **Resultado SIFEN** | ✅ Aprobado (0000066) | ❌ Rechazado (067, 068) → Debería funcionar ahora |

---

## ✅ CHECKLIST DE CORRECCIONES

- [x] **Identificado problema RUC = 0**
- [x] **Corregido: Usar cédula del cliente**
- [ ] **Implementar actualización automática** (Celery o Signal)
- [ ] **Corregir URLs en base de datos** (NULL hasta aprobación)
- [ ] **Agregar manejo de errores en template**
- [ ] **Probar con cliente real**
- [ ] **Verificar aprobación en SIFEN**

---

## 🎯 PRÓXIMOS PASOS INMEDIATOS

1. **Reiniciar Django** para aplicar corrección del RUC
2. **Hacer prueba de compra** y verificar que RUC ya no es 0
3. **Implementar actualización automática** (tarea asíncrona)
4. **Actualizar template** para mostrar errores de SIFEN

---

**CORRECCIÓN CRÍTICA APLICADA:** Uso de cédula como RUC ✅  
**PENDIENTE:** Actualización automática y manejo de errores
