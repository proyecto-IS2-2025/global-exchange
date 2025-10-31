# 🧾 Facturación Automática Post-MFA - IMPLEMENTADO

## 📋 Descripción General

Se ha implementado la **generación automática de facturas electrónicas** que se activa **después de la verificación MFA exitosa** en las compras de divisas.

---

## 🎯 Flujo Implementado

### Caso 1: Compra CON MFA Activado
```
Usuario completa compra → Se envía código OTP por email → 
Usuario ingresa código → MFA verifica código → 
✅ Código válido → Se crea transacción → Se procesa pago → 
🧾 SE GENERA FACTURA AUTOMÁTICAMENTE
```

### Caso 2: Compra SIN MFA (Desactivado por Admin)
```
Usuario completa compra → Se crea transacción directamente → 
Se procesa pago → 🧾 SE GENERA FACTURA AUTOMÁTICAMENTE
```

---

## 🔧 Archivos Modificados

### 1. `/facturacion_electronica/services.py`
**Función agregada:** `generar_factura_automatica(transaccion)`

**Funcionalidad:**
- Conecta al SQL Proxy de Factura Segura
- Obtiene el próximo número de factura disponible
- Crea el documento electrónico en la tabla `de`
- Inserta actividades económicas en `gActEco`
- Crea items de la factura en `gCamItem`
- Marca el documento como "Confirmado" para envío a SIFEN
- Crea registro en Django `FacturaElectronica`
- Retorna: `(success: bool, factura: FacturaElectronica, error_msg: str)`

**Datos de la factura:**
```python
{
    'cliente_ruc': '...',
    'cliente_dv': '...',
    'cliente_nombre': '...',
    'cliente_email': '...',
    'items': [{
        'descripcion': 'Compra de 500.00 USD',
        'cantidad': 1,
        'precio_unitario': 3750000.00,  # En PYG
        'tasa_iva': '10'
    }]
}
```

---

### 2. `/operacion_divisas/views.py`
**Vista modificada:** `compra_mfa_verify_view(request)`

#### Integración en línea ~870 (MFA Activo):
```python
# Después de verificar código OTP exitosamente
response = crear_transaccion_desde_compra(request)

# NUEVO: Generar factura automáticamente
if response.status_code == 302 and 'confirmacion' in response.url:
    numero_transaccion = response.url.split('/')[-2]
    transaccion = Transaccion.objects.get(numero_transaccion=numero_transaccion)
    
    if transaccion.estado == 'pagada':
        success, factura, error = generar_factura_automatica(transaccion)
        if success:
            messages.success(request, f"¡Factura {factura.numero_factura} generada!")
        else:
            messages.warning(request, "Compra exitosa pero hubo problema con factura")
```

#### Integración en línea ~833 (MFA Desactivado):
```python
# Cuando admin desactiva MFA durante el proceso
response = crear_transaccion_desde_compra(request)

# NUEVO: Generar factura automáticamente
if response.status_code == 302 and 'confirmacion' in response.url:
    numero_transaccion = response.url.split('/')[-2]
    transaccion = Transaccion.objects.get(numero_transaccion=numero_transaccion)
    
    if transaccion.estado == 'pagada':
        success, factura, error = generar_factura_automatica(transaccion)
        # ... (mismo manejo de errores)
```

---

## 🔐 Condiciones para Generar Factura

La factura se genera SOLO SI:
1. ✅ La transacción fue creada exitosamente
2. ✅ El estado de la transacción es `'pagada'` (pago procesado)
3. ✅ La transacción NO tiene factura previa (`hasattr(transaccion, 'factura_electronica')`)

---

## 🛡️ Manejo de Errores

El sistema implementa **try/except robusto**:

```python
try:
    success, factura, error = generar_factura_automatica(transaccion)
    if success:
        logger.info(f"✅ Factura generada: {factura.numero_factura}")
        messages.success(request, f"¡Factura {factura.numero_factura} generada!")
    else:
        logger.warning(f"⚠️ Error: {error}")
        messages.warning(request, "Compra exitosa pero problema al generar factura")
except Exception as e:
    logger.error(f"Error facturación: {e}", exc_info=True)
    # LA TRANSACCIÓN NO SE AFECTA - Solo se registra el error
```

**Importante:** Si la facturación falla, **la transacción sigue completándose** y el usuario puede continuar. Se muestra un mensaje de advertencia pero NO se bloquea la operación.

---

## 📊 Datos Registrados en FacturaElectronica

```python
FacturaElectronica.objects.create(
    transaccion=transaccion,
    numero_factura='001-003-0000058',  # Formato completo
    establecimiento='001',
    punto_expedicion='003',
    numero_documento='0000058',
    de_id=12345,  # ID en SQL Proxy
    estado='confirmado',
    estado_sifen='Procesando',
    descripcion_sifen='Factura enviada al SIFEN para procesamiento',
    url_kude_pdf='http://localhost:40080/kude/0000058.pdf',
    url_kude_xml='http://localhost:40080/kude/0000058.xml',
    datos_factura={...}  # JSON con todos los datos
)
```

---

## 🧪 Cómo Probar

### Paso 1: Asegurar que SQL Proxy esté corriendo
```bash
cd /home/jose/proyecto_is2/sql-proxy01
sudo chmod -R 777 ./volumes/  # Solo primera vez
./start-full-proxy.sh
docker ps  # Verificar que db, web, web-sched, nginx estén UP
```

### Paso 2: Activar MFA para Compra
```python
# Desde Django admin o shell
from mfa.models import MFAConfig
config = MFAConfig.get_config()
config.mfa_compra_enabled = True
config.save()
```

### Paso 3: Realizar Compra de Prueba
1. Iniciar sesión como cliente
2. Ir a "Comprar Divisas"
3. Seleccionar divisa (ej: USD), monto, medio de pago
4. Confirmar compra
5. **Verificar:** Se envía email con código OTP
6. Ingresar código de 6 dígitos
7. **Verificar:** Mensaje "Código verificado. Procesando tu compra..."
8. **Verificar:** Transacción creada con estado `pagada`
9. **Verificar:** Mensaje "¡Factura 001-003-XXXXXXX generada exitosamente!"
10. **Verificar:** En "Mis Facturas" aparece la nueva factura
11. **Verificar:** Botón "Descargar PDF" apunta a `http://localhost:40080/kude/XXXXXXX.pdf`

### Paso 4: Verificar PDF Real
```bash
# Abrir navegador
http://localhost:40080/kude/0000058.pdf  # Ajustar número
```

Debe mostrar el PDF de SIFEN con:
- Logo Global Exchange
- RUC Emisor: 2595733-3
- Cliente: (datos del cliente)
- Items: "Compra de XXX USD"
- Monto total en PYG
- CDC (Código de Control) si SIFEN ya procesó

---

## 📝 Logs para Debugging

Los logs se generan en:
- **Django:** `global-exchange/logs/`
- **SQL Proxy:** `sql-proxy01/volumes/web/logs/`, `sql-proxy01/volumes/nginx/logs/`

### Ver logs en tiempo real:
```bash
# Django
tail -f global-exchange/logs/django.log

# SQL Proxy
cd sql-proxy01
docker compose logs -f web
docker compose logs -f web-sched
```

### Buscar logs de facturación:
```bash
grep -i "factura" global-exchange/logs/django.log
grep -i "generar_factura_automatica" global-exchange/logs/django.log
```

---

## 🎨 Experiencia de Usuario

### Mensajes que verá el cliente:

**Caso exitoso:**
1. "Código verificado. Procesando tu compra..." (azul)
2. "Transferencia recibida: operación pagada." (verde)
3. "Transacción TXN-20251030... creada exitosamente." (verde)
4. **"¡Factura 001-003-0000058 generada exitosamente!"** (verde) ← NUEVO

**Caso fallo facturación:**
1. "Código verificado. Procesando tu compra..." (azul)
2. "Transferencia recibida: operación pagada." (verde)
3. "Transacción TXN-20251030... creada exitosamente." (verde)
4. **"La compra fue exitosa pero hubo un problema al generar la factura. Contacte a soporte."** (amarillo) ← NUEVO

---

## 🔄 Próximos Pasos (Opcionales)

### 1. Sincronización de Estado SIFEN
Crear tarea asíncrona (Celery) que consulte estado de facturas cada 5 minutos:
```python
# facturacion_electronica/tasks.py
@shared_task
def actualizar_estados_facturas():
    service = SQLProxyService()
    service.conectar()
    
    facturas = FacturaElectronica.objects.filter(estado='confirmado')
    for factura in facturas:
        estado = service.consultar_estado_factura(factura.numero_documento)
        if estado and estado.get('estado_sifen') == 'Aprobado':
            factura.estado = 'aprobado'
            factura.cdc = estado.get('cdc')
            factura.save()
```

### 2. Notificación por Email
Enviar email al cliente con link de descarga del PDF:
```python
from django.core.mail import send_mail

def notificar_factura_generada(factura):
    send_mail(
        subject=f'Factura {factura.numero_factura} - Global Exchange',
        message=f'Tu factura está lista. Descarga: {factura.url_kude_pdf}',
        from_email='noreply@globalexchange.com',
        recipient_list=[factura.transaccion.cliente.email],
    )
```

### 3. Re-intento Automático
Si falla la generación, intentar nuevamente después de X minutos.

---

## ✅ Estado del Proyecto

- [x] Función `generar_factura_automatica()` implementada
- [x] Integración en flujo MFA (código verificado)
- [x] Integración en flujo sin MFA
- [x] Manejo de errores robusto
- [x] Logs de debugging
- [x] Mensajes al usuario
- [ ] **PENDIENTE:** Prueba end-to-end con SQL Proxy corriendo
- [ ] **PENDIENTE:** Verificación de PDF real generado por SIFEN

---

## 📞 Soporte

Si hay problemas:
1. Verificar que SQL Proxy esté corriendo: `docker ps`
2. Revisar logs: `docker compose logs web`
3. Verificar permisos: `ls -la ./volumes/web/logs/`
4. Reiniciar servicios: `docker compose restart`
5. Consultar configuración ESI: Ejecutar `inicializar_esi_sqlproxy.py`

---

**Implementado el:** 30 de octubre de 2025  
**Equipo:** Global Exchange - Equipo 7  
**Feature:** GLEX-26 - Facturación Electrónica
