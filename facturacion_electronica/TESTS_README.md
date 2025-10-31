# Tests de Facturación Electrónica

## Descripción

Suite de tests para validar la integración con SIFEN (Sistema Integrado de Facturación Electrónica Nacional) a través del SQL Proxy de Factura Segura.

## Tests Implementados

### Test 1: Conexión SQL Proxy
**Propósito:** Verifica que se puede establecer conexión con la base de datos del SQL Proxy.

**Qué prueba:**
- Conexión al PostgreSQL del SQL Proxy
- Creación de cursor para ejecutar consultas
- Gestión correcta de la conexión

### Test 2: Credenciales ESI
**Propósito:** Valida que las credenciales del Emisor Electrónico (ESI) están correctamente configuradas.

**Qué prueba:**
- Existencia de configuración ESI en la base de datos
- RUC correcto (2595733)
- Estado activo del ESI
- URL correcta del ambiente TEST (apitest.facturasegura.com.py)

### Test 3: Facturas Generadas
**Propósito:** Verifica que existen facturas electrónicas generadas en el sistema.

**Qué prueba:**
- Consulta de facturas en el rango asignado (51-100)
- Cantidad de facturas generadas
- Acceso correcto a la tabla `de` del SQL Proxy

### Test 4: Próximo Número
**Propósito:** Valida el sistema de numeración secuencial de facturas.

**Qué prueba:**
- Obtención del próximo número disponible
- Verificación de rango (51-100)
- Manejo de casos cuando el rango está completo

### Test 5: Generar Factura de Prueba ⭐
**Propósito:** Genera una factura electrónica real en el SQL Proxy.

**Qué prueba:**
- Inserción en tabla `de` (Documento Electrónico)
- Inserción de actividad económica en `gActEco`
- Inserción de item en `gCamItem`
- Inserción de pago en `gPaConEIni`
- Commit de transacción
- Verificación de factura insertada

## Cómo Ejecutar

### Todos los tests
```bash
poetry run python manage.py test facturacion_electronica.tests
```

### Con verbosidad (ver detalles)
```bash
poetry run python manage.py test facturacion_electronica.tests --verbosity=2
```

### Test individual
```bash
poetry run python manage.py test facturacion_electronica.tests.SQLProxyConnectionTest
```

## Resultados Esperados

```
✓ Test 1: Conexión SQL Proxy exitosa
✓ Test 2: Credenciales ESI correctas
✓ Test 3: 34 facturas encontradas en SQL Proxy
✓ Test 4: Próximo número disponible: 0000082
✓ Test 5: Factura 0000082 generada exitosamente (ID: 45)

Ran 5 tests in 0.308s

OK
```

## Notas Importantes

- **Ambiente:** Todos los tests se ejecutan contra el ambiente de prueba de SIFEN
- **Base de datos:** Se crea una base de datos temporal para los tests de Django
- **SQL Proxy:** Los tests se conectan al SQL Proxy real (no se mockea)
- **Test 5 genera facturas:** El Test 5 SÍ genera una factura real en SQL Proxy (consume 1 número del rango)
- **Idempotencia:** Los tests 1-4 se pueden ejecutar múltiples veces sin efectos secundarios
- **Test 5:** Cada ejecución consume 1 factura del rango disponible (51-100)

## Configuración Requerida

Los tests requieren que el SQL Proxy esté configurado y corriendo:
- Host: localhost
- Puerto: 45432
- Base de datos: fs_proxy_bd

## Troubleshooting

### Error de conexión
Si falla el Test 1, verificar que el SQL Proxy esté corriendo:
```bash
# Verificar si el proxy está activo
netstat -tulpn | grep 45432
```

### ESI no encontrado
Si falla el Test 2, ejecutar la inicialización:
```bash
poetry run python manage.py shell
>>> from facturacion_electronica.services import SQLProxyService
>>> service = SQLProxyService()
>>> service.conectar()
>>> service.inicializar_esi()
```

---

**Equipo 7 - Global Exchange**  
**Ingeniería de Software II - 2025**
