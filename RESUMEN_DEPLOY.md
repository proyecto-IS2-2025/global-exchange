# ✅ RESUMEN: Preparación para Despliegue en Render

## 📦 Archivos Creados/Modificados

### ✅ Archivos Creados:
1. **`build.sh`** - Script de build para Render
2. **`render.yaml`** - Configuración de servicios (opcional)
3. **`.env.example`** - Plantilla de variables de entorno
4. **`DEPLOY_RENDER.md`** - Guía completa de despliegue

### ✅ Archivos Modificados:
1. **`casa_de_cambios/settings.py`** - Limpiado y optimizado para producción

## 🔧 Configuración Actual

### ✅ YA TIENES:
- ✅ `Procfile` con comando de Gunicorn
- ✅ `requirements.txt` con todas las dependencias
- ✅ WhiteNoise para archivos estáticos
- ✅ dj-database-url para PostgreSQL
- ✅ Configuración de seguridad para producción
- ✅ Middleware correctamente ordenado
- ✅ `.gitignore` protegiendo archivos sensibles

### ✅ CONFIGURACIONES IMPORTANTES:

#### 1. Base de Datos
```python
# Usa DATABASE_URL automáticamente en Render
if os.environ.get('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(...)
```

#### 2. Archivos Estáticos
```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

#### 3. Seguridad en Producción
```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

#### 4. Variables de Entorno
Todas las configuraciones sensibles usan `os.environ.get()`:
- SECRET_KEY
- DEBUG
- ALLOWED_HOSTS
- DATABASE_URL
- EMAIL_HOST_USER
- EMAIL_HOST_PASSWORD
- STRIPE_*

## 📋 PASOS PARA DESPLEGAR

### 1. En GitHub (si aún no lo hiciste)
```bash
git add .
git commit -m "Preparación para despliegue en Render"
git push origin main
```

### 2. En Render - Crear Base de Datos
- New → PostgreSQL
- Name: `global-exchange-db`
- Plan: Free
- **Copiar Internal Database URL**

### 3. En Render - Crear Web Service
- New → Web Service
- Conectar repositorio GitHub
- Build Command: `./build.sh`
- Start Command: `gunicorn casa_de_cambios.wsgi:application`

### 4. Configurar Variables de Entorno
En Render Dashboard → Environment:

```bash
SECRET_KEY=<generar-nueva-clave-segura>
DEBUG=False
ALLOWED_HOSTS=tu-app.onrender.com
DATABASE_URL=<url-de-bd-copiada>
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password>
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 5. Deploy!
Click en "Create Web Service" y espera que complete el build.

## ⚠️ IMPORTANTE ANTES DE DESPLEGAR

### Variables de Entorno Necesarias:
1. **SECRET_KEY** - Genera una nueva:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **EMAIL_HOST_PASSWORD** - Genera App Password de Gmail:
   - https://myaccount.google.com/security
   - Activa verificación en 2 pasos
   - Genera contraseña de aplicación

3. **ALLOWED_HOSTS** - Actualiza con tu dominio de Render:
   ```
   tu-app.onrender.com,localhost
   ```

## 🔍 Verificaciones Post-Despliegue

Después del primer deploy:

1. **Crear Superusuario**
   ```bash
   # En Render Shell
   python manage.py createsuperuser
   ```

2. **Cargar Datos Iniciales** (opcional)
   ```bash
   python manage.py loaddata roles/fixtures/roles_data.json
   python manage.py loaddata users/fixtures/users_data.json
   ```

3. **Verificar Permisos**
   ```bash
   python manage.py sync_permissions
   python manage.py setup_test_roles
   ```

## 📊 Build Process

El script `build.sh` ejecuta automáticamente:
1. ✅ Instala dependencias (`pip install -r requirements.txt`)
2. ✅ Recolecta estáticos (`collectstatic`)
3. ✅ Ejecuta migraciones (`migrate`)
4. ✅ Sincroniza permisos (`sync_permissions`)

## 🆘 Solución de Problemas Comunes

### Error: "Application failed to start"
- Revisa logs en Render Dashboard
- Verifica todas las variables de entorno

### Error: "No module named X"
- Actualiza `requirements.txt`
- Rebuild desde Render

### Estáticos no cargan
- Verifica que `build.sh` completó
- Ejecuta manualmente `collectstatic`

### Base de datos vacía
- Ejecuta migraciones desde Render Shell
- Crea superusuario manualmente

## 📚 Documentación Adicional

- **Guía completa**: Ver `DEPLOY_RENDER.md`
- **Variables de entorno**: Ver `.env.example`
- **Render Docs**: https://render.com/docs
- **Django Deployment**: https://docs.djangoproject.com/en/5.2/howto/deployment/

## ✅ Checklist Final

- [ ] `build.sh` tiene permisos de ejecución
- [ ] Todas las variables de entorno configuradas
- [ ] `SECRET_KEY` generada (nueva, no usar la de desarrollo)
- [ ] `DEBUG=False` en producción
- [ ] `ALLOWED_HOSTS` con dominio de Render
- [ ] Base de datos PostgreSQL creada
- [ ] Repositorio en GitHub actualizado
- [ ] `.env` NO está en el repositorio (verificar `.gitignore`)

## 🚀 ¡Listo para Desplegar!

El proyecto está **completamente configurado** para desplegarse en Render.

Sigue la guía en `DEPLOY_RENDER.md` para los pasos detallados.

**¡Éxito con tu despliegue! 🎉**
