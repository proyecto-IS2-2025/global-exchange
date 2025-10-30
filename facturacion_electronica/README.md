# 🧾 Facturación Electrónica - Global Exchange (Equipo 7)

Implementación de facturación electrónica usando **SQL Proxy** de Factura Segura para el proyecto de casa de cambios.

## 📌 Información del Equipo

- **Email:** glex.globalexchange@gmail.com
- **Rango de Facturas:** 51-100
- **Establecimiento-Punto:** 001-003
- **RUC Emisor:** 2595733-3 (del profesor)
- **Ambiente:** TEST

## 🚀 Inicio Rápido

### 1. Instalar dependencias
```bash
pip install psycopg2-binary
```

### 2. Levantar SQL Proxy
```bash
cd /home/jose/proyecto_is2/sql-proxy01
docker compose -f docker-compose.test.yml up -d
```

### 3. Agregar app a Django
En `casa_de_cambios/settings.py`:
```python
INSTALLED_APPS = [
    # ...
    'facturacion_electronica',
]
```

### 4. Migrar base de datos
```bash
python manage.py migrate
```

### 5. Inicializar ESI (solo una vez)
```bash
# Primero completar la contraseña en facturacion_electronica/config.py
python facturacion_electronica/inicializar_esi.py
```

### 6. Probar conexión
```bash
python facturacion_electronica/test_conexion.py
```

### 7. Generar factura de prueba
```bash
python facturacion_electronica/ejemplo_uso.py
```

## 💡 Uso desde Django

### Generar factura desde una transacción
```python
from facturacion_electronica.utils import generar_factura_desde_transaccion
from transacciones.models import Transaccion

transaccion = Transaccion.objects.get(numero_transaccion='TRX-2025-0001')
factura = generar_factura_desde_transaccion(transaccion)
print(f"Factura generada: {factura.numero_factura}")
```

### Consultar estado de factura
```python
from facturacion_electronica.utils import actualizar_estado_factura
from facturacion_electronica.models import FacturaElectronica

factura = FacturaElectronica.objects.get(numero_factura='001-003-0000051')
estado = actualizar_estado_factura(factura)

if factura.esta_aprobada():
    print(f"CDC: {factura.cdc}")
```

## 📁 Archivos Importantes

- `config.py` - Configuración del equipo (RUC, email, token, etc.)
- `services.py` - Servicio para comunicarse con SQL Proxy
- `utils.py` - Funciones para generar facturas desde transacciones
- `models.py` - Modelo FacturaElectronica
- `inicializar_esi.py` - Script para configurar ESI (ejecutar 1 vez)
- `test_conexion.py` - Verificar conexión al SQL Proxy
- `ejemplo_uso.py` - Ejemplo completo de uso

## 🔍 Ver Facturas Generadas

Abrir en el navegador: http://localhost:40080/kude/
- **Usuario:** sqlproxy
- **Contraseña:** kude1234

## 📖 Documentación Completa

Ver `GUIA_IMPLEMENTACION.md` para la guía completa paso a paso.

## ⚠️ Antes de Empezar

1. ✅ Completar la contraseña del ESI en `config.py`
2. ✅ Verificar que Docker esté ejecutándose
3. ✅ Levantar los contenedores del SQL Proxy
4. ✅ Ejecutar `inicializar_esi.py` una sola vez

## 🐛 Problemas Comunes

**No se puede conectar al SQL Proxy:**
```bash
docker ps  # Verificar que los contenedores estén corriendo
docker compose -f docker-compose.test.yml logs -f  # Ver logs
```

**Factura rechazada por SIFEN:**
```bash
# Conectar a la BD del SQL Proxy
psql -h localhost -p 45432 -U fs_proxy_user -d fs_proxy_bd
# Ver error
SELECT error_sifen FROM public.de WHERE dnumdoc='0000051';
```

## 📞 Contacto

- Profesor: Guillermo González
- Soporte Factura Segura: soporte@facturasegura.com.py

---

**¡Implementación lista para usar! 🎉**
