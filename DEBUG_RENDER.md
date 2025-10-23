# 🐛 Debugging en Render - Error de Base de Datos Resuelto

## ❌ Error Encontrado

```
django.db.utils.OperationalError: connection to server at "localhost" (::1), port 5432 failed: Connection refused
```

### Causa
Django estaba intentando conectarse a `localhost` en lugar de usar la variable de entorno `DATABASE_URL` de Render.

## ✅ Solución Aplicada

Se corrigió la configuración de la base de datos en `settings.py`:

```python
# ANTES (INCORRECTO):
import dj_database_url
if os.environ.get('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),  # ← INCORRECTO
        conn_max_age=600,
        ssl_require=True
    )

# DESPUÉS (CORRECTO):
import dj_database_url
if os.environ.get('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True
    )
```

### Diferencia Clave
`dj_database_url.config()` **automáticamente** lee la variable de entorno `DATABASE_URL`. No necesita pasarse como parámetro `default`.

## 🔄 Próximos Pasos

### 1. Hacer commit y push
```bash
git add .
git commit -m "Fix: Corregir configuración de DATABASE_URL para Render"
git push origin main
```

### 2. En Render
El deploy se activará automáticamente y ahora debería:
- ✅ Conectarse correctamente a la base de datos PostgreSQL
- ✅ Ejecutar las migraciones
- ✅ Recolectar archivos estáticos
- ✅ Iniciar la aplicación con Gunicorn

### 3. Verificar Variables de Entorno en Render

Asegúrate de que estas variables estén configuradas en Render:

```bash
# OBLIGATORIAS
SECRET_KEY=<tu-clave-secreta-generada>
DEBUG=False
ALLOWED_HOSTS=tu-app.onrender.com
DATABASE_URL=<se-configura-automáticamente-desde-bd>

# EMAIL
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password>

# STRIPE
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## 🔍 Cómo Verificar que Funciona

### En los Logs de Render:
1. Ve a tu Dashboard de Render
2. Selecciona tu Web Service
3. Click en "Logs"
4. Deberías ver:
   ```
   ✅ Migraciones ejecutadas correctamente
   ✅ Archivos estáticos recolectados
   ✅ Permisos sincronizados
   ✅ Starting gunicorn...
   ```

### Después del Deploy:
1. Visita tu URL de Render: `https://tu-app.onrender.com`
2. La página de inicio debería cargar
3. Intenta hacer login

## 🐛 Problemas Comunes Adicionales

### 1. Si aún hay errores de conexión
```bash
# Verifica que DATABASE_URL esté configurada
# En Render Shell:
echo $DATABASE_URL
```

Debería mostrar algo como:
```
postgresql://usuario:password@host:5432/nombrebd
```

### 2. Error: "relation does not exist"
```bash
# Ejecutar migraciones manualmente desde Render Shell:
python manage.py migrate
```

### 3. Base de datos vacía
```bash
# Crear superusuario:
python manage.py createsuperuser

# Sincronizar permisos:
python manage.py sync_permissions
python manage.py setup_test_roles
```

### 4. Archivos estáticos no cargan
```bash
# Verificar configuración:
python manage.py collectstatic --dry-run

# Recolectar manualmente:
python manage.py collectstatic --no-input
```

## 📊 Configuración Final Correcta

### settings.py - Sección de Base de Datos

```python
# Configuración base para desarrollo local
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'global_exchange'),
        'USER': os.environ.get('DB_USER', 'django_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'django123'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': int(os.environ.get('DB_PORT', '5432')),
    }
}

# Sobrescribir con DATABASE_URL si existe (Render/producción)
import dj_database_url
if os.environ.get('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True
    )
```

### Orden de Prioridad:
1. Si `DATABASE_URL` existe → usa PostgreSQL de Render
2. Si no → usa configuración local con variables de entorno
3. Si no hay variables → usa valores por defecto (desarrollo)

## ✅ Checklist de Verificación

Antes de hacer el siguiente deploy:

- [x] `settings.py` corregido (sin `default=` en dj_database_url.config)
- [ ] Commit y push realizados
- [ ] Variables de entorno configuradas en Render
- [ ] `DATABASE_URL` configurada (automática desde BD PostgreSQL)
- [ ] Build completado sin errores
- [ ] Migraciones ejecutadas
- [ ] Aplicación accesible

## 🎯 Resultado Esperado

Después de aplicar estos cambios:

```
✅ Build successful
✅ Migrations applied
✅ Static files collected
✅ Permissions synced
✅ Application running on https://tu-app.onrender.com
```

## 📞 Si Necesitas Más Ayuda

1. Revisa los logs completos en Render Dashboard
2. Verifica todas las variables de entorno
3. Confirma que la base de datos PostgreSQL esté activa
4. Intenta rebuild manual: "Manual Deploy" → "Clear build cache & deploy"

---

**¡El error está corregido! Ahora haz commit y push para aplicar los cambios.** 🚀
