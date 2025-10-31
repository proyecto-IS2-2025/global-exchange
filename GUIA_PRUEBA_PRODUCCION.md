# 🧪 Guía de Prueba - Entorno de Producción

## 📋 Objetivo
Probar que el entorno de producción completo funciona correctamente antes de la entrega.

---

## ✅ Checklist de Prueba

### **Parte 1: SQL Proxy (Factura Segura)**

#### 1. Levantar SQL Proxy
```bash
cd ~/proyecto_is2/sql-proxy01
docker compose -f docker-compose.test.yml up -d
```

**Verificar:**
```bash
docker ps | grep sql-proxy
```

**Debe mostrar 4 contenedores:**
- ✅ `sql-proxy01-db-1`
- ✅ `sql-proxy01-web-1`
- ✅ `sql-proxy01-web-sched-1`
- ✅ `sql-proxy01-nginx-1`

#### 2. Verificar Conectividad SQL Proxy
```bash
# API Web (debe retornar: "Hello World, fs_proxy!")
curl http://localhost:40080/

# Scheduler (debe retornar: "El task es...")
curl http://localhost:40088/

# Base de datos
PGPASSWORD=p123456 psql -h localhost -p 45432 -U fs_proxy_user -d fs_proxy_bd -c "\dt"
```

**✅ Resultado esperado:**
- API responde correctamente
- Scheduler responde correctamente
- Base de datos muestra tablas (`de`, `de_detalle`, etc.)

---

### **Parte 2: Global Exchange (Django Producción)**

#### 3. Levantar Global Exchange
```bash
cd ~/proyecto_is2/global-exchange
make prod-up
```

**Esperar 1-2 minutos** mientras construye las imágenes.

**Verificar:**
```bash
docker ps | grep global-exchange-local-prod
```

**Debe mostrar 3 contenedores:**
- ✅ `global-exchange-local-prod-web-1`
- ✅ `global-exchange-local-prod-db-1`
- ✅ `global-exchange-local-prod-redis-1`

#### 4. Verificar Logs (sin errores)
```bash
docker logs global-exchange-local-prod-web-1 --tail 20
```

**✅ Debe mostrar:**
```
Listening at: http://0.0.0.0:8000 (1)
```

---

### **Parte 3: Cargar Fixtures**

#### 5. Cargar Datos Iniciales
```bash
cd ~/proyecto_is2/global-exchange
make load-prod
```

**Esto ejecuta:**
- ✅ Carga roles_data.json
- ✅ Carga users_data.json
- ✅ Carga clientes_data.json
- ✅ Carga divisas_data.json
- ✅ Carga bancos_data.json
- ✅ Carga denominaciones_data.json
- ✅ Carga billetera_data.json
- ✅ Sincroniza permisos (59 permisos)
- ✅ Configura roles (7 roles)
- ✅ Crea usuario dev (dev/dev123)

**Verificar fixtures cargadas:**
```bash
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py shell -c "
from django.contrib.auth.models import User
from clientes.models import Cliente
from divisas.models import Divisa

print(f'Usuarios: {User.objects.count()}')
print(f'Clientes: {Cliente.objects.count()}')
print(f'Divisas: {Divisa.objects.count()}')
"
```

**✅ Debe mostrar:**
```
Usuarios: 7 (aprox)
Clientes: 10+ (aprox)
Divisas: 4 (USD, EUR, ARS, BRL)
```

---

### **Parte 4: Pruebas Funcionales**

#### 6. Acceder al Sistema Web
```bash
# Abrir navegador
xdg-open http://localhost
```

**O manualmente:** `http://localhost`

**✅ Verificar:**
- [x] Página de login carga correctamente
- [x] Login con usuario `dev` / password `dev123`
- [x] Dashboard aparece sin errores
- [x] Menú lateral muestra todas las opciones

#### 7. Probar Módulo de Facturación

**Navegación:**
1. Login como `dev`
2. Click en **"Facturación Electrónica"** (menú lateral)
3. Click en **"Mis Facturas"**

**✅ Verificar:**
- [x] Lista de facturas carga correctamente
- [x] Filtros funcionan (por cliente, estado)
- [x] Búsqueda funciona
- [x] Puede ver detalle de una factura

#### 8. Generar una Factura de Prueba

**Pasos:**
1. Ir a **"Divisas"** → **"Compra de Divisas"**
2. Seleccionar:
   - Divisa: **USD**
   - Monto: **100**
   - Cliente: **Cliente Empresarial**
3. Completar pago (usar tarjeta de prueba: `4242424242424242`)
4. Confirmar transacción

**✅ Verificar:**
- [x] Transacción se crea exitosamente
- [x] Factura se genera automáticamente
- [x] Factura aparece en "Mis Facturas"
- [x] Estado inicial: **"pendiente"**

**Esperar 30-60 segundos** para que SIFEN apruebe.

#### 9. Sincronizar Estado con SIFEN

**En el detalle de la factura:**
1. Click en botón **"🔄 Actualizar Estado"**

**✅ Verificar:**
- [x] Estado cambia a **"aprobado"**
- [x] CDC aparece (44 caracteres)
- [x] Botones de descarga aparecen:
  - **"📄 Descargar PDF"**
  - **"📄 Descargar XML"**

#### 10. Descargar Documentos

**Click en "Descargar PDF"**

**✅ Verificar:**
- [x] PDF se descarga correctamente
- [x] PDF contiene:
  - Logo y datos de Global Exchange
  - Datos del cliente
  - Detalle de items
  - Totales correctos
  - CDC visible
  - QR Code

---

### **Parte 5: Pruebas de Permisos**

#### 11. Probar con Usuario Cliente

**Logout y login con:**
- Usuario: `cliente1`
- Password: `password123`

**✅ Verificar:**
- [x] Solo ve **"Mis Facturas"** (propias)
- [x] NO ve botón "Generar Factura Manual"
- [x] NO ve botón "Sincronizar SIFEN"
- [x] NO ve todas las facturas del sistema

#### 12. Probar con Usuario Observador

**Logout y login con:**
- Usuario: `observador1`
- Password: `password123`

**✅ Verificar:**
- [x] Ve todas las facturas (solo lectura)
- [x] NO ve botones de acción (exportar, generar, cancelar)
- [x] Puede descargar PDF
- [x] NO puede modificar nada

---

### **Parte 6: Pruebas de Integración**

#### 13. Verificar Conexión Django → SQL Proxy

```bash
# Desde contenedor de Django
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py shell -c "
from facturacion_electronica.services import SQLProxyService

service = SQLProxyService()
conectado = service.conectar()
print(f'✅ Conexión SQL Proxy: {\"OK\" if conectado else \"ERROR\"}')

if conectado:
    result = service.consultar_proximo_numero('003')
    print(f'✅ Próximo número factura: {result}')
    service.desconectar()
"
```

**✅ Debe mostrar:**
```
✅ Conexión SQL Proxy: OK
✅ Próximo número factura: 0000XXX
```

#### 14. Verificar Archivos PDF Generados

```bash
ls -lh ~/proyecto_is2/sql-proxy01/volumes/web/kude/202510/ | tail -10
```

**✅ Debe mostrar:**
- Archivos PDF con formato: `001-003-XXXXXXX_YYYYMMDD_HHMMSS_NNNNNN.pdf`
- Archivos XML correspondientes

---

## 🛑 Detener Todo

Cuando termines las pruebas:

```bash
# Opción 1: Usar el script
cd ~/proyecto_is2/global-exchange
bash stop_production.sh

# Opción 2: Manual
cd ~/proyecto_is2/global-exchange
make prod-down

cd ~/proyecto_is2/sql-proxy01
docker compose -f docker-compose.test.yml down
```

---

## 📊 Resumen de Verificación

### ✅ Checklist Completo:

- [ ] SQL Proxy levantado (4 contenedores)
- [ ] Global Exchange levantado (3 contenedores)
- [ ] Fixtures cargadas correctamente
- [ ] Login funciona (dev/dev123)
- [ ] Módulo de facturación accesible
- [ ] Se puede generar factura automática
- [ ] SIFEN aprueba la factura
- [ ] PDF se descarga correctamente
- [ ] Permisos funcionan correctamente
- [ ] Conexión Django → SQL Proxy OK

---

## 🚨 Troubleshooting

### Problema: "SQL Proxy no responde"
```bash
# Ver logs
docker logs sql-proxy01-web-1 --tail 50

# Reiniciar
cd ~/proyecto_is2/sql-proxy01
docker compose -f docker-compose.test.yml restart web
```

### Problema: "Global Exchange no levanta"
```bash
# Ver logs
docker logs global-exchange-local-prod-web-1 --tail 50

# Reconstruir
cd ~/proyecto_is2/global-exchange
make prod-down
make prod-up
```

### Problema: "Fixtures no cargan"
```bash
# Verificar que el contenedor esté corriendo
docker ps | grep global-exchange-local-prod-web

# Intentar cargar individualmente
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py loaddata roles_data.json
```

### Problema: "Factura no se genera"
```bash
# Ver logs de Django
docker logs global-exchange-local-prod-web-1 -f

# Verificar conexión SQL Proxy
curl http://localhost:40080/
```

---

## 🎯 Para la Entrega

**Demostración en vivo (5 minutos):**

1. **Inicio (30 seg):**
   ```bash
   bash start_production.sh
   ```
   
2. **Login (10 seg):**
   - Usuario: `dev`
   - Password: `dev123`

3. **Generar Factura (2 min):**
   - Compra de USD
   - Mostrar generación automática
   - Mostrar en lista de facturas

4. **Sincronizar (1 min):**
   - Click "Actualizar Estado"
   - Mostrar cambio a "aprobado"
   - Mostrar CDC

5. **Descargar PDF (30 seg):**
   - Mostrar PDF con todos los datos
   - Mostrar QR Code

6. **Permisos (30 seg):**
   - Login como observador
   - Mostrar restricciones

7. **Detener (30 seg):**
   ```bash
   bash stop_production.sh
   ```

---

**✅ Sistema listo para entrega del Sprint** 🎉
