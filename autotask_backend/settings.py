import os
import sys
from pathlib import Path
from datetime import timedelta
import dj_database_url
from whitenoise.storage import CompressedManifestStaticFilesStorage


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-clave-secreta-dev'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']  # Temporal para pruebas, luego reemplaza con:
# ALLOWED_HOSTS = ['tu-app.onrender.com', 'localhost', '127.0.0.1']
# ALLOWED_HOSTS = ['192.168.1.7', 'localhost', '127.0.0.1', '192.168.1.5', '192.168.1.6', '192.168.1.8', '192.168.1.2']

# Application definition

INSTALLED_APPS = [

    'api',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    
    'django_filters',
    'drf_yasg',
    'django_celery_beat',
    'charts',
    
]

MIDDLEWARE = [
    
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'api.middleware.DisableCSRFForAuth',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

# Permitir todas las conexiones (en desarrollo)
CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'autotask_backend.urls'

STATICFILES_DIRS = [BASE_DIR / "static"]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'autotask_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
#}

#DATABASES = {
#    'default': dj_database_url.config(
#        default=os.getenv('DATABASE_URL'),  # Lee la URL de la variable de entorno
#        conn_max_age=600  # Mejora el rendimiento de conexión
#    )
#}

if 'dumpdata' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Tu configuración actual con dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL', 'sqlite:///' + str(BASE_DIR / 'db.sqlite3')),
            conn_max_age=600
        )
    }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/



# Configuración de archivos estáticos
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'api.User'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
}

# Simple JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'api.models.User',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# ==================== CELERY CONFIGURATION ====================
# Configuración específica para Windows
import sys
if sys.platform.startswith('win'):
    # Usar solo pool para Windows (evita errores de permisos)
    CELERY_WORKER_POOL = 'solo'
    CELERY_TASK_ALWAYS_EAGER = False  # Mantener False para testing real
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_WORKER_CONCURRENCY = 1
else:
    CELERY_WORKER_POOL = 'prefork'
    CELERY_WORKER_CONCURRENCY = 4
    
# Configuración de Celery
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Argentina/Buenos_Aires'
CELERY_ENABLE_UTC = True
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_TASK_ALWAYS_EAGER', 'False') == 'True'

# Configuración de tareas periódicas (Beat)
CELERY_BEAT_SCHEDULE = {
    'verificar-mantenimientos-preventivos': {
        'task': 'api.tasks.verificar_mantenimientos_preventivos',
        'schedule': timedelta(hours=24),  # Cada 24 horas
        'options': {'queue': 'periodic_tasks'}
    },
    'recordatorios-ordenes-pendientes': {
        'task': 'api.tasks.recordatorios_ordenes_pendientes',
        'schedule': timedelta(hours=12),  # Cada 12 horas
        'options': {'queue': 'periodic_tasks'}
    },
    'reintentar-notificaciones-fallidas': {
        'task': 'api.tasks.reintentar_notificaciones_fallidas',
        'schedule': timedelta(hours=1),  # Cada hora
        'options': {'queue': 'periodic_tasks'}
    },
    'limpiar-dispositivos-inactivos': {
        'task': 'api.tasks.limpiar_dispositivos_inactivos',
        'schedule': timedelta(days=7),  # Cada 7 días
        'options': {'queue': 'periodic_tasks'}
    },
    'tarea-prueba-celery': {
        'task': 'api.tasks.tarea_prueba_celery',
        'schedule': timedelta(minutes=5),
        'options': {'queue': 'periodic_tasks'}
    },
    
    'prueba-servicios-externos': {
        'task': 'api.tasks.prueba_servicios_externos',
        'schedule': timedelta(minutes=30),
        'options': {'queue': 'periodic_tasks'}
    },
    
    'limpiar-dispositivos-inactivos': {
        'task': 'api.tasks.limpiar_dispositivos_inactivos',
        'schedule': timedelta(days=7),
        'options': {'queue': 'periodic_tasks'}
    },
}

# Configuración para entornos de producción
if 'RENDER' in os.environ:
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.5,
    }
    # En producción, deshabilitar eager execution
    CELERY_TASK_ALWAYS_EAGER = False

# ==================== FIREBASE CONFIGURATION ====================

# Firebase Cloud Messaging
FCM_SERVER_KEY = os.environ.get('FCM_SERVER_KEY', 'foGrVmvHTP0b8RE3Es7YosOhV35Zygk6O1q35joXhNM')

# ==================== LOGGING CONFIGURATION ====================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'celery_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'celery.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'api': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'celery_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'api.tasks': {
            'handlers': ['console', 'celery_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'api.services': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Crear directorio de logs si no existe
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# ==================== SECURITY SETTINGS ====================

# Configuración de seguridad para producción
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Restringir hosts en producción
    ALLOWED_HOSTS = [
        'https://maintech-backend.onrender.com',
        'localhost',
        '127.0.0.1',
    ]

# ==================== FILE UPLOAD SETTINGS ====================

# Configuración de subida de archivos
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# ==================== CACHE CONFIGURATION ====================

# Configuración de caché con Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Tiempo de vida de la caché (en segundos)
CACHE_TTL = 60 * 15  # 15 minutos


# URLs de autenticación
#LOGIN_URL = '/api/dashboard/produccion.html'       # URL a la que se redirige si no está logueado
#LOGIN_REDIRECT_URL = '/api/dashboard/mantenimiento.html'  # URL después de hacer login
#LOGIN_REDIRECT_URL = '/api/dashboard/inventario.html' 
# ✅ Corregido (usa solo uno)
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'  # Redirige al dashboard principal
LOGOUT_REDIRECT_URL = '/accounts/login/'
LOGOUT_REDIRECT_URL = '/api/dashboard/produccion.html'  # URL después de hacer logout