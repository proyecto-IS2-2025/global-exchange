# 🚀 Guía de Despliegue en Render

Esta guía te ayudará a desplegar el proyecto Global Exchange en Render.

## 📋 Pre-requisitos

- Cuenta en [Render](https://render.com)
- Repositorio en GitHub con el código
- Variables de entorno configuradas

## 🔧 Pasos para el Despliegue

### 1. Preparar el Proyecto

El proyecto ya tiene los archivos necesarios:
- ✅ `Procfile` - Comando de inicio para Gunicorn
- ✅ `build.sh` - Script de build automático
- ✅ `requirements.txt` - Dependencias Python
- ✅ `render.yaml` - Configuración de Render (opcional)
- ✅ `settings.py` - Configurado para producción

### 2. Crear Base de Datos PostgreSQL

1. Ve a tu [Dashboard de Render](https://dashboard.render.com/)
2. Click en **"New +"** → **"PostgreSQL"**
3. Configura:
   - **Name**: `global-exchange-db`
   - **Database**: `global_exchange`
   - **User**: (generado automáticamente)
   - **Region**: Oregon (o el más cercano)
   - **Plan**: Free
4. Click en **"Create Database"**
5. **Importante**: Copia el **Internal Database URL** (lo necesitarás después)

### 3. Crear Web Service

1. En el Dashboard, click en **"New +"** → **"Web Service"**
2. Conecta tu repositorio de GitHub
3. Configura:

#### Configuración Básica
- **Name**: `global-exchange`
- **Region**: Oregon (mismo que la BD)
- **Branch**: `main` o `devel0p`
- **Root Directory**: (dejar vacío)
- **Runtime**: Python 3
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn casa_de_cambios.wsgi:application`

#### Plan
- Selecciona el plan (Free tier disponible)

### 4. Configurar Variables de Entorno

En la sección **"Environment"**, agrega las siguientes variables:

#### Variables Obligatorias

```bash
# Django
SECRET_KEY=<genera-una-clave-segura>
DEBUG=False
ALLOWED_HOSTS=tu-app.onrender.com,localhost

# Base de Datos
DATABASE_URL=<internal-database-url-copiada-del-paso-2>

# Email (Gmail)
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=<tu-app-password-de-gmail>

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

#### Cómo generar SECRET_KEY

```bash
# Opción 1: Python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Opción 2: Online
# https://djecrety.ir/
```

#### Cómo obtener App Password de Gmail

1. Ve a https://myaccount.google.com/security
2. Activa "Verificación en 2 pasos"
3. En "Contraseñas de aplicaciones", genera una nueva
4. Usa esa contraseña en `EMAIL_HOST_PASSWORD`

### 5. Desplegar

1. Click en **"Create Web Service"**
2. Render iniciará el build automáticamente
3. El proceso incluye:
   - Instalación de dependencias
   - Recolección de archivos estáticos
   - Migraciones de base de datos
   - Sincronización de permisos

### 6. Verificar el Despliegue

Una vez completado:
1. Tu app estará disponible en: `https://tu-app.onrender.com`
2. Verifica que la página carga correctamente
3. Prueba el login y funcionalidades básicas

## 🔍 Solución de Problemas

### Error: "Application failed to start"
- Revisa los logs en Render Dashboard
- Verifica que todas las variables de entorno estén configuradas
- Confirma que `DATABASE_URL` es correcta

### Error: "ModuleNotFoundError"
- Asegúrate que `requirements.txt` está actualizado
- Verifica que el build completó exitosamente

### Base de datos vacía
Si necesitas crear un superusuario:

```bash
# Desde Render Shell (Dashboard → Shell)
python manage.py createsuperuser

# O cargar datos de fixtures
python manage.py loaddata roles/fixtures/roles_data.json
python manage.py loaddata users/fixtures/users_data.json
```

### Archivos estáticos no cargan
- Verifica que `STATICFILES_STORAGE` está configurado
- Ejecuta manualmente: `python manage.py collectstatic`
- Revisa que WhiteNoise esté en MIDDLEWARE

## 📊 Comandos Útiles en Render Shell

```bash
# Acceder a Shell desde Dashboard → Shell tab

# Ver migraciones aplicadas
python manage.py showmigrations

# Sincronizar permisos
python manage.py sync_permissions

# Configurar roles
python manage.py setup_test_roles

# Crear superusuario
python manage.py createsuperuser
```

## 🔐 Seguridad en Producción

Asegúrate de:
- ✅ `DEBUG=False`
- ✅ `SECRET_KEY` único y seguro
- ✅ `ALLOWED_HOSTS` configurado correctamente
- ✅ HTTPS habilitado (Render lo hace automáticamente)
- ✅ Variables sensibles en Environment Variables (no en código)

## 📝 Actualizaciones

Para desplegar cambios:
1. Haz push a tu rama principal en GitHub
2. Render detectará los cambios automáticamente
3. Iniciará un nuevo build y deploy

O manualmente:
- En Render Dashboard → **"Manual Deploy"** → **"Deploy latest commit"**

## 🆘 Soporte

- [Documentación de Render](https://render.com/docs)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- Logs en tiempo real en Render Dashboard

## ✅ Checklist Final

Antes de lanzar a producción:

- [ ] `SECRET_KEY` generada y configurada
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` configurado
- [ ] Base de datos PostgreSQL creada
- [ ] `DATABASE_URL` configurada
- [ ] Variables de entorno de email configuradas
- [ ] Variables de Stripe configuradas (producción)
- [ ] Migraciones ejecutadas
- [ ] Archivos estáticos recolectados
- [ ] Superusuario creado
- [ ] Permisos sincronizados
- [ ] Pruebas básicas realizadas
- [ ] SSL/HTTPS funcionando
