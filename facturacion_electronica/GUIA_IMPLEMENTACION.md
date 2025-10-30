# Guía de Implementación: Facturación Electrónica - Equipo 7

## 📋 Información del Equipo

- **Email ESI:** `glex.globalexchange@gmail.com`
- **RUC Emisor:** `2595733-3` (del profesor)
- **Rango de Facturas:** 51-100 (documentos 0000051 a 0000100)
- **Establecimiento:** 001
- **Punto de Expedición:** 003
- **Timbrado:** 02595733
- **Fecha Inicio Timbrado:** 2025-03-27
- **Ambiente:** TEST

## 🎯 Resumen de la Implementación

Hemos implementado la facturación electrónica usando **SQL Proxy** (la opción recomendada por el profesor) que es más sencilla que usar la API directamente. El SQL Proxy se encarga de toda la comunicación con el SIFEN, nosotros solo debemos insertar datos en una base de datos PostgreSQL.

## 📁 Estructura Creada

```
global-exchange/
└── facturacion_electronica/
    ├── __init__.py
    ├── apps.py
    ├── admin.py
    ├── models.py              # Modelo FacturaElectronica
    ├── config.py              # Configuración (datos del equipo)
    ├── services.py            # Servicio para interactuar con SQL Proxy
    ├── utils.py               # Utilidades para generar facturas
    ├── inicializar_esi.py     # Script para configurar ESI (ejecutar 1 vez)
    └── ejemplo_uso.py         # Ejemplo de cómo usar el servicio
```

## 🚀 Pasos para Implementar

### 1️⃣ Instalar Dependencias

```bash
cd /home/jose/proyecto_is2/global-exchange
pip install psycopg2-binary
```

### 2️⃣ Levantar el SQL Proxy

```bash
cd /home/jose/proyecto_is2/sql-proxy01

# Construir los contenedores
docker compose -f docker-compose.test.yml build

# Levantar los contenedores
docker compose -f docker-compose.test.yml up -d

# Ver los logs para verificar que todo esté funcionando
docker compose -f docker-compose.test.yml logs -f
```

**Verificar que los contenedores estén corriendo:**
```bash
docker ps
```

Deberías ver 4 contenedores:
- `nginx` (puerto 40080)
- `web` (aplicación Flask)
- `web-sched` (scheduler)
- `db` (PostgreSQL en puerto 45432)

### 3️⃣ Configurar Django

Agregar la app a `INSTALLED_APPS` en `casa_de_cambios/settings.py`:

```python
INSTALLED_APPS = [
    # ... otras apps
    'facturacion_electronica',
]
```

### 4️⃣ Crear las Migraciones

```bash
cd /home/jose/proyecto_is2/global-exchange
python manage.py makemigrations facturacion_electronica
python manage.py migrate
```

### 5️⃣ Inicializar el ESI (Solo una vez)

**IMPORTANTE:** Antes de ejecutar este script, asegúrate de completar la contraseña del ESI en `facturacion_electronica/config.py`:

```python
ESI_CONFIG = {
    'email': 'glex.globalexchange@gmail.com',
    'password': 'TU_CONTRASEÑA_AQUI',  # <-- Completar aquí
    # ...
}
```

Luego ejecutar:

```bash
cd /home/jose/proyecto_is2/global-exchange
python facturacion_electronica/inicializar_esi.py
```

Este script configurará la tabla ESI en el SQL Proxy con los datos correctos del equipo.

### 6️⃣ Probar la Generación de Facturas

```bash
python facturacion_electronica/ejemplo_uso.py
```

Este script generará una factura de prueba. Si todo funciona correctamente, verás:

```
✓ Conectado al SQL Proxy de Factura Segura
✓ ESI ya está configurado
✓ Factura 001-003-0000051 generada correctamente
```

### 7️⃣ Ver las Facturas Generadas (KuDE)

Abre en tu navegador:

```
http://localhost:40080/kude/
```

**Credenciales:**
- Usuario: `sqlproxy`
- Contraseña: `kude1234`

Aquí encontrarás los PDF y XML de todas las facturas generadas.

## 🔄 Integración con Transacciones

### Generar Factura desde una Transacción

```python
from facturacion_electronica.utils import generar_factura_desde_transaccion
from transacciones.models import Transaccion

# Obtener una transacción completada
transaccion = Transaccion.objects.get(numero_transaccion='TRX-2025-0001')

# Generar la factura
try:
    factura = generar_factura_desde_transaccion(transaccion)
    print(f"Factura generada: {factura.numero_factura}")
except Exception as e:
    print(f"Error: {e}")
```

### Generar Facturas Automáticamente

Puedes agregar esto a tu vista o señal de transacciones para que se generen automáticamente cuando una transacción se completa:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from transacciones.models import Transaccion
from facturacion_electronica.utils import generar_factura_desde_transaccion

@receiver(post_save, sender=Transaccion)
def generar_factura_automatica(sender, instance, **kwargs):
    """
    Genera factura automáticamente cuando una transacción se completa
    """
    if instance.estado == 'completado' and not hasattr(instance, 'factura_electronica'):
        try:
            generar_factura_desde_transaccion(instance)
        except Exception as e:
            print(f"Error al generar factura: {e}")
```

### Consultar Estado de una Factura

```python
from facturacion_electronica.utils import actualizar_estado_factura
from facturacion_electronica.models import FacturaElectronica

factura = FacturaElectronica.objects.get(numero_factura='001-003-0000051')
estado = actualizar_estado_factura(factura)

if factura.esta_aprobada():
    print(f"Factura aprobada con CDC: {factura.cdc}")
else:
    print(f"Estado: {factura.estado}")
    if factura.error_sifen:
        print(f"Error: {factura.error_sifen}")
```

## 🔍 Verificar Estado en la Base de Datos

Puedes conectarte directamente a la base de datos del SQL Proxy para ver el estado de las facturas:

```bash
psql -h localhost -p 45432 -U fs_proxy_user -d fs_proxy_bd
```

**Contraseña:** `p123456`

Luego ejecutar:

```sql
SELECT id, dnumdoc, estado, estado_sifen, desc_sifen, error_sifen, fch_sifen, cdc
FROM public.de
WHERE dnumdoc='0000051'
ORDER BY id DESC
LIMIT 1;
```

## 📊 Datos Importantes del XML de Referencia

El profesor compartió un XML de ejemplo con los datos correctos:

### Timbrado
- **Número:** 02595733
- **Fecha Inicio:** 2025-03-27
- **Establecimiento:** 001
- **Punto Expedición:** 001 (nosotros usamos 003)

### Actividades Económicas (Usar estas exactamente)
1. **62010** - Actividades de programación informática
2. **74909** - Otras actividades profesionales, científicas y técnicas n.c.p.

### Datos del Emisor
- **RUC:** 2595733
- **DV:** 3
- **Nombre:** DE generado en ambiente de prueba - sin valor comercial ni fiscal
- **Dirección:** YVAPOVO C/ TOBATI
- **Número Casa:** 1543
- **Departamento:** 1 (CAPITAL)
- **Ciudad:** 1 (ASUNCION (DISTRITO))
- **Teléfono:** (0961)988439
- **Email:** ggonzar@gmail.com

## ⚠️ Errores Comunes y Soluciones

### 1. Error: "host not found in upstream 'web:8000'"

**Causa:** El contenedor `glx-nginx` está intentando iniciarse antes que el contenedor `web`.

**Solución:**
```bash
docker compose -f docker-compose.test.yml down
docker compose -f docker-compose.test.yml up -d
```

### 2. Error: "Max retries exceeded... Name or service not known"

**Causa:** El contenedor no puede conectarse a internet para comunicarse con SIFEN.

**Solución:**
- Verificar conexión a internet
- Reiniciar Docker
- Verificar firewall

### 3. Error: "No se pudo conectar al SQL Proxy"

**Causa:** Los contenedores no están levantados o el puerto 45432 no está disponible.

**Solución:**
```bash
# Verificar que los contenedores estén corriendo
docker ps

# Si no están, levantarlos
cd /home/jose/proyecto_is2/sql-proxy01
docker compose -f docker-compose.test.yml up -d
```

### 4. Factura Rechazada por SIFEN

**Causa:** Datos incorrectos (timbrado, actividades económicas, etc.)

**Solución:**
- Consultar el error exacto en la base de datos del SQL Proxy
- Verificar que los datos en `config.py` coincidan con el XML de ejemplo
- Usar las actividades económicas exactas del XML

## 🔄 Flujo Completo

1. Cliente realiza una transacción en Global Exchange
2. La transacción se marca como "completada"
3. Se genera automáticamente una factura electrónica (o manualmente con `generar_factura_desde_transaccion()`)
4. Los datos se insertan en la base de datos del SQL Proxy (estado: "Confirmado")
5. El SQL Proxy automáticamente:
   - Firma el documento electrónicamente
   - Lo envía al SIFEN
   - Genera el KuDE (PDF y XML)
6. Puedes consultar el estado con `actualizar_estado_factura()`
7. Cuando es aprobado, se obtiene el CDC y se puede descargar el PDF/XML

## 📝 Comandos Útiles

```bash
# Ver logs del SQL Proxy
docker compose -f docker-compose.test.yml logs -f

# Detener SQL Proxy
docker compose -f docker-compose.test.yml stop

# Levantar SQL Proxy
docker compose -f docker-compose.test.yml up -d

# Conectar a la base de datos
psql -h localhost -p 45432 -U fs_proxy_user -d fs_proxy_bd

# Generar facturas pendientes (desde Django shell)
python manage.py shell
>>> from facturacion_electronica.utils import generar_facturas_pendientes
>>> resultados = generar_facturas_pendientes()
>>> print(resultados)
```

## 🎓 Referencias

- **SQL Proxy:** https://gitlab.com/ggonza732/sql-proxy01
- **API de Factura Segura:** Documento PDF proporcionado por el profesor
- **Ambiente de Prueba:** https://apitest.facturasegura.com.py
- **Portal:** https://test.facturasegura.com.py

## 📞 Soporte

Si tienes problemas:
1. Revisar los logs del SQL Proxy
2. Verificar el estado en la base de datos del SQL Proxy
3. Consultar el XML de ejemplo del profesor
4. Contactar a: soporte@facturasegura.com.py

---

**¡Todo listo para generar facturas electrónicas! 🎉**
