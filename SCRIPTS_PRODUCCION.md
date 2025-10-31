# 🚀 Scripts de Inicialización - Entorno de Producción

## 📋 Descripción

Estos scripts automatizan el inicio y detención completa del entorno de producción de **Global Exchange**, incluyendo:

- **SQL Proxy** (Factura Segura): 4 contenedores Docker
- **Global Exchange**: Aplicación Django en modo producción
- **Fixtures**: Datos iniciales y configuración del sistema

---

## 📁 Scripts Disponibles

### 1. `start_production.sh` - Iniciar Producción ✅

Levanta el entorno completo de producción en el orden correcto.

**Uso:**
```bash
bash start_production.sh
```

**¿Qué hace?**
1. ✅ Verifica dependencias (Docker, Make)
2. ✅ Inicia SQL Proxy (4 contenedores)
   - PostgreSQL (puerto 45432)
   - API Flask (puerto 5000 interno)
   - Scheduler Flask (puerto 5001 interno)
   - Nginx (puertos 40080, 40088)
3. ✅ Inicia Global Exchange (producción)
   - Web (Django + Gunicorn)
   - PostgreSQL
   - Redis
4. ✅ Carga fixtures automáticamente:
   - Roles y permisos
   - Usuarios de prueba
   - Clientes de ejemplo
   - Divisas y tasas
   - Bancos y denominaciones
   - Configuración de billeteras
5. ✅ Verifica que todo esté funcionando
6. ✅ Muestra URLs de acceso

**Salida esperada:**
```
════════════════════════════════════════════════════════════════════════════
  ✅ Sistema de Producción Iniciado Correctamente
════════════════════════════════════════════════════════════════════════════

El entorno de producción está listo para usar.

Credenciales por defecto:
  Usuario: dev
  Password: dev123

URLs del sistema:
  ➜ Global Exchange: http://localhost
  ➜ SQL Proxy API: http://localhost:40080
  ➜ SQL Proxy Scheduler: http://localhost:40088
  ➜ PostgreSQL SQL Proxy: localhost:45432
```

---

### 2. `stop_production.sh` - Detener Producción 🛑

Detiene todos los servicios de producción de forma ordenada.

**Uso:**
```bash
bash stop_production.sh
```

**¿Qué hace?**
1. ✅ Detiene Global Exchange (producción)
2. ✅ Detiene SQL Proxy (todos los contenedores)
3. ✅ Verifica que todo esté detenido
4. ✅ Libera recursos del sistema

---

## 🔧 Componentes del Sistema

### SQL Proxy (Factura Segura)
| Contenedor | Puerto | Descripción |
|------------|--------|-------------|
| `sql-proxy01-db-1` | `45432` | PostgreSQL 17 |
| `sql-proxy01-web-1` | `5000` (interno) | API Flask |
| `sql-proxy01-web-sched-1` | `5001` (interno) | Scheduler |
| `sql-proxy01-nginx-1` | `40080`, `40088` | Reverse Proxy |

### Global Exchange
| Contenedor | Puerto | Descripción |
|------------|--------|-------------|
| `global-exchange-local-prod-web-1` | `80` | Django + Gunicorn |
| `global-exchange-local-prod-db-1` | `5432` (interno) | PostgreSQL |
| `global-exchange-local-prod-redis-1` | `6379` (interno) | Redis Cache |

---

## 📊 Fixtures Cargadas Automáticamente

El script `start_production.sh` carga las siguientes fixtures:

1. **`roles_data.json`** - Roles del sistema (7 roles)
2. **`users_data.json`** - Usuarios de prueba
3. **`clientes_data.json`** - Clientes de ejemplo
4. **`divisas_data.json`** - Divisas (USD, EUR, ARS, BRL)
5. **`bancos_data.json`** - Bancos de Paraguay
6. **`denominaciones_data.json`** - Billetes y monedas
7. **`billetera_data.json`** - Configuración de billeteras

Además ejecuta:
- `sync_permissions` - Sincroniza permisos
- `setup_test_roles` - Configura 59 permisos en 7 roles
- `sync_role_status` - Sincroniza estados de roles
- `create_dev_user` - Crea usuario admin (dev/dev123)

---

## 🎯 Comandos Make Utilizados

Los scripts internamente ejecutan:

```bash
# SQL Proxy
cd ../sql-proxy01
docker compose -f docker-compose.test.yml up -d

# Global Exchange
cd global-exchange
make prod-up      # Levantar producción
make load-prod    # Cargar fixtures
make prod-down    # Detener producción
```

---

## ⚙️ Requisitos Previos

1. **Docker** instalado y corriendo
2. **Make** instalado
3. **Directorio SQL Proxy** en `../sql-proxy01/`
4. **Archivos `.env`** configurados en ambos proyectos

---

## 🧪 Verificación Manual

Después de ejecutar `start_production.sh`, puedes verificar:

```bash
# Ver todos los contenedores corriendo
docker ps

# Verificar SQL Proxy
curl http://localhost:40080/
# Debe retornar: "Hello World, fs_proxy!"

# Verificar Global Exchange
curl http://localhost/
# Debe retornar la página de inicio

# Ver logs en tiempo real
docker logs -f global-exchange-local-prod-web-1
docker logs -f sql-proxy01-web-1
```

---

## 🔍 Troubleshooting

### Error: "SQL Proxy no está corriendo"
```bash
cd ../sql-proxy01
docker compose -f docker-compose.test.yml logs
```

### Error: "Global Exchange no inició"
```bash
cd global-exchange
docker logs global-exchange-local-prod-web-1
```

### Error: "Puerto ya en uso"
```bash
# Detener todo primero
bash stop_production.sh

# Verificar puertos
sudo lsof -i :80
sudo lsof -i :40080
```

### Limpiar todo y reiniciar
```bash
# Detener todo
bash stop_production.sh

# Limpiar volúmenes (⚠️ ELIMINA DATOS)
cd ../sql-proxy01
docker compose -f docker-compose.test.yml down -v

cd ../global-exchange
make prod-down

# Reiniciar
bash start_production.sh
```

---

## 📝 Notas Importantes

- ⚠️ **Producción Local**: Estos scripts son para **entorno de producción LOCAL**, no para despliegue en servidor real.
- 🔐 **Credenciales**: Cambia las credenciales por defecto en un entorno real.
- 💾 **Persistencia**: Los datos se persisten en volúmenes de Docker.
- 🔄 **Orden**: Los scripts respetan el orden de inicialización (SQL Proxy primero, luego Django).

---

## 📞 Soporte

Si encuentras algún problema:

1. Revisa los logs de los contenedores
2. Verifica que todos los puertos estén libres
3. Asegúrate de que Docker tenga recursos suficientes
4. Consulta la documentación completa en `README.md`

---

## ✅ Checklist de Entrega

- [x] Script de inicio automatizado (`start_production.sh`)
- [x] Script de detención automatizado (`stop_production.sh`)
- [x] Carga automática de fixtures
- [x] Verificación de dependencias
- [x] Mensajes informativos con colores
- [x] Confirmación antes de ejecutar
- [x] Verificación final del estado
- [x] Documentación completa (este archivo)

---

**¡Listo para la entrega del Sprint!** 🎉
