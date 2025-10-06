"""
Configuración de Django para el proyecto Casa de Cambios.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# ═════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN BASE
# ═════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno
load_dotenv(os.path.join(BASE_DIR, '.env'))

# ═════════════════════════════════════════════════════════════════════
# SEGURIDAD
# ═════════════════════════════════════════════════════════════════════

# ⚠️ IMPORTANTE: Asegúrate de tener SECRET_KEY en .env
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY no está configurada. "
        "Agrega SECRET_KEY='tu-clave-secreta' en el archivo .env"
    )

# Debug mode (solo True en desarrollo)
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

# Hosts permitidos
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ═════════════════════════════════════════════════════════════════════
# APLICACIONES
# ═════════════════════════════════════════════════════════════════════

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third-party apps
    'widget_tweaks',
    
    # Local apps
    'users.apps.UsersConfig',
    'roles',
    'clientes',
    'divisas',
    'medios_pago',
    'transacciones',
    'operacion_divisas',
    'banco',
    'billetera',
    'simulador',
    'mfa',
    'autenticacion',
    'interfaz',
]

# ═════════════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═════════════════════════════════════════════════════════════════════

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'clientes.middleware.ClienteActivoMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # ✅ AGREGAR AL FINAL (solo en desarrollo)
    'roles.middleware.CustomErrorHandlerMiddleware',
]

ROOT_URLCONF = 'casa_de_cambios.urls'

# ═════════════════════════════════════════════════════════════════════
# TEMPLATES
# ═════════════════════════════════════════════════════════════════════

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # ✅ Context processors de Django (TODOS necesarios)
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # ✅ Context processors personalizados
                'roles.context_processors.grupo_usuario',  # ← MANTENER SOLO ESTE (incluye user_permissions)
                'simulador.context_processors.simulador_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'casa_de_cambios.wsgi.application'

# ═════════════════════════════════════════════════════════════════════
# BASE DE DATOS
# ═════════════════════════════════════════════════════════════════════

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'global_exchange'),
        'USER': os.environ.get('DB_USER', 'django_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'django123'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': int(os.environ.get('DB_PORT', '5432')),
        'TEST': {
            'NAME': 'test_global_exchange',
        },
    }
}

# ═════════════════════════════════════════════════════════════════════
# AUTENTICACIÓN
# ═════════════════════════════════════════════════════════════════════

AUTH_USER_MODEL = 'users.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # ← Buena práctica: mínimo 8 caracteres
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# URLs de autenticación
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/redirect-dashboard/'
LOGOUT_REDIRECT_URL = 'inicio'

# ═════════════════════════════════════════════════════════════════════
# EMAIL
# ═════════════════════════════════════════════════════════════════════

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'glex.globalexchange@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'tpsh yedw lthc oprs')

# ⚠️ RECOMENDACIÓN: Mover credenciales de email a .env
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# ═════════════════════════════════════════════════════════════════════
# INTERNACIONALIZACIÓN
# ═════════════════════════════════════════════════════════════════════

LANGUAGE_CODE = 'es-py'  # Español de Paraguay
TIME_ZONE = 'America/Asuncion'
USE_I18N = True
USE_TZ = True

# ═════════════════════════════════════════════════════════════════════
# ARCHIVOS ESTÁTICOS
# ═════════════════════════════════════════════════════════════════════

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# ═════════════════════════════════════════════════════════════════════
# LOGGING
# ═════════════════════════════════════════════════════════════════════

import os  # ← Asegurar que está importado al inicio

# Crear carpeta de logs automáticamente
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)  # ← AGREGAR ESTA LÍNEA

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'roles': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# ═════════════════════════════════════════════════════════════════════
# OTROS
# ═════════════════════════════════════════════════════════════════════

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'