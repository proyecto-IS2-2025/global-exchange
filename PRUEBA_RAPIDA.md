# 🚀 Prueba Rápida - Entorno de Producción
## (5 Minutos)

## ✅ Paso 1: SQL Proxy Ya Está Corriendo

```bash
docker ps | grep sql-proxy
```

**Debes ver 4 contenedores:**
- sql-proxy01-db-1
- sql-proxy01-web-1  
- sql-proxy01-web-sched-1
- sql-proxy01-nginx-1

✅ **SQL Proxy OK**

---

## ✅ Paso 2: Levantar Global Exchange

```bash
cd ~/proyecto_is2/global-exchange
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml up --build -d
```

**Esperar 1-2 minutos...**

**Verificar:**
```bash
docker ps | grep global-exchange
```

---

## ✅ Paso 3: Cargar Fixtures

```bash
cd ~/proyecto_is2/global-exchange

# Ejecutar cada comando y verificar que no haya errores
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py loaddata roles_data.json
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py loaddata users_data.json
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py loaddata clientes_data.json
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py loaddata divisas_data.json
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py loaddata bancos_data.json
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py loaddata denominaciones_data.json
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py loaddata billetera_data.json

# Configurar permisos
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py sync_permissions
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py setup_test_roles --verbose
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py sync_role_status

# Crear usuario admin
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml exec web python manage.py create_dev_user
```

---

## ✅ Paso 4: Acceder al Sistema

**Abrir en navegador:** `http://localhost`

**Login:**
- Usuario: `dev`
- Password: `dev123`

**✅ Verificar:**
- [ ] Login exitoso
- [ ] Dashboard carga
- [ ] Menú lateral visible
- [ ] Opción "Facturación Electrónica" presente

---

## ✅ Paso 5: Probar Facturación

1. **Ir a:** Divisas → Compra de Divisas
2. **Completar:**
   - Divisa: USD
   - Monto: 100
   - Cliente: Cliente Empresarial
3. **Pagar** con tarjeta: `4242424242424242`
4. **Confirmar**

**✅ Verificar:**
- [ ] Transacción exitosa
- [ ] Factura generada automáticamente

5. **Ir a:** Facturación Electrónica → Mis Facturas
6. **Click en la última factura**
7. **Click:** 🔄 "Actualizar Estado"

**✅ Verificar:**
- [ ] Estado cambia a "aprobado"
- [ ] Aparece CDC
- [ ] Botón "Descargar PDF" visible

8. **Click:** "Descargar PDF"

**✅ Verificar:**
- [ ] PDF se descarga
- [ ] Contiene todos los datos
- [ ] Tiene QR Code

---

## 🛑 Detener Todo

```bash
cd ~/proyecto_is2/global-exchange
docker compose -p global-exchange-local-prod -f docker-compose.prod.yml down

cd ~/proyecto_is2/sql-proxy01
docker compose -f docker-compose.test.yml down
```

---

## ✅ ¡LISTO PARA ENTREGAR!

Si todo funciona → Sistema 100% operativo 🎉
