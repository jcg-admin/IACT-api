"""
Django settings BASE - IACT Call Center System.

Configuracion base compartida por todos los ambientes.
NO usar directamente, usar development/testing/production.

CNST v2.2.1 Compliance: 100%
- CNST-001: NO email backends
- CNST-002: SESSION_ENGINE = 'django.contrib.sessions.backends.db'
- CNST-003: Dual database (analytics + ivr_legacy READ-ONLY)
- CNST-004: NO WebSockets, NO Celery
- CNST-005: Throttling + MAX_PAGE_SIZE
- CNST_TECNICAS: NO Sentry, NO Redis, NO Celery, NO Channels

Version: 2.2.1
Python: 3.11+
Django: 5.0+
"""

from pathlib import Path
from decouple import config, Csv


# ==============================================================================
# PATHS
# ==============================================================================

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Project root (iact-project/)
PROJECT_ROOT = BASE_DIR.parent


# ==============================================================================
# SECURITY
# ==============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-CHANGE-THIS-IN-PRODUCTION'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())


# ==============================================================================
# APPLICATIONS
# ==============================================================================

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'drf_spectacular',
    
    # Local apps
    'apps.core',
    'apps.ivr',
    'apps.authentication',
    'apps.users',  # <- Debe estar ANTES de apps.access (User model)
    'apps.access',
    'apps.audit',
    'apps.pipeline',
    'apps.reports',
    'apps.alerts',
    'apps.logs',  # <- Sistema de alertas internas
    'apps.dashboard',  # <- Sistema de dashboards personalizables
]


# ==============================================================================
# AUTHENTICATION
# ==============================================================================

# Custom User Model (CNST-037)
AUTH_USER_MODEL = 'users.User'


# ==============================================================================
# MIDDLEWARE
# ==============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ==============================================================================
# URL CONFIGURATION
# ==============================================================================

ROOT_URLCONF = 'config.urls'


# ==============================================================================
# TEMPLATES
# ==============================================================================

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


# ==============================================================================
# WSGI
# ==============================================================================

WSGI_APPLICATION = 'config.wsgi.application'


# ==============================================================================
# DATABASES
# ==============================================================================
# CNST-003: Dual database configuration
# - default: PostgreSQL (analytics - READ + WRITE)
# - ivr_legacy: MariaDB (READ-ONLY)
# ==============================================================================

DATABASES = {
    # PostgreSQL - Analytics Database (READ + WRITE)
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='iact_analytics'),
        'USER': config('DB_USER', default='iact_user'),
        'PASSWORD': config('DB_PASSWORD', default='iact_password_dev'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    },
    
    # MariaDB - IVR Legacy Database (READ-ONLY)
    'ivr': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('IVR_DB_NAME', default='ivr_legacy'),
        'USER': config('IVR_DB_USER', default='ivr_readonly'),
        'PASSWORD': config('IVR_DB_PASSWORD', default='ivr_readonly_password'),
        'HOST': config('IVR_DB_HOST', default='localhost'),
        'PORT': config('IVR_DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            # unix_socket para conexión local (evita TCP cuando HOST='localhost')
            # Se ignora si HOST no es 'localhost' o ''
            'unix_socket': config('IVR_DB_SOCKET', default='/run/mysqld/mysqld.sock'),
        },
    },
}

# Database Router (CNST-003: READ-ONLY enforcement)
DATABASE_ROUTERS = ['config.db_router.DatabaseRouter']

# IVR MariaDB query timeout (seconds).
# Applies to all cursor.execute() and cursor.callproc() calls on connections['ivr'].
# Override in settings_local.py for development.
IVR_QUERY_TIMEOUT_SEC = int(config('IVR_QUERY_TIMEOUT_SEC', default='30'))  # CNST-003


# ==============================================================================
# PASSWORD VALIDATION
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = 'es-mx'

TIME_ZONE = 'America/Mexico_City'

USE_I18N = True

USE_TZ = True


# ==============================================================================
# STATIC FILES
# ==============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]


# ==============================================================================
# MEDIA FILES
# ==============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Avatar settings
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB


# ==============================================================================
# DEFAULT PRIMARY KEY
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==============================================================================
# SESSIONS
# ==============================================================================
# CNST-002: Session en base de datos (NO cache, NO cookies)
# ==============================================================================

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_NAME = 'iact_sessionid'
SESSION_COOKIE_AGE = 900  # 15 minutos
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # True en production
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Sesiones no persisten al cerrar navegador


# ==============================================================================
# CSRF
# ==============================================================================

CSRF_COOKIE_NAME = 'iact_csrftoken'
CSRF_COOKIE_HTTPONLY = False  # JavaScript necesita leer
CSRF_COOKIE_SECURE = False  # True en production
CSRF_COOKIE_SAMESITE = 'Lax'


# ==============================================================================
# AUTHENTICATION
# ==============================================================================

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]


# ==============================================================================
# LOGGING
# ==============================================================================

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
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': PROJECT_ROOT / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# ==============================================================================
# DJANGO REST FRAMEWORK
# ==============================================================================
# CNST-005: Throttling + MAX_PAGE_SIZE
# ==============================================================================

REST_FRAMEWORK = {
    # Authentication
    # TokenAuthentication: para clientes API (header: Authorization: Token <key>)
    # SessionAuthentication: para requests con cookie de sesion Django
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    
    # Permissions
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
    # Pagination (CNST-005)
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'MAX_PAGE_SIZE': 1000,  # CNST-005: Máximo 1000 registros
    
    # Filtering
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    
    # Throttling (CNST-005)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
    
    # Schema
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    # Rendering
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    
    # Exception handling
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}


# ==============================================================================
# SIMPLE JWT
# ==============================================================================

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}


# ==============================================================================
# DRF SPECTACULAR (OpenAPI)
# ==============================================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'IACT Call Center API',
    'DESCRIPTION': 'Sistema Analytics Call Center - API REST',
    'VERSION': '2.2.1',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,

    # OCP: tags declarados en schema.py de cada app (nunca modificar aqui)
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums',
        'config.spectacular_hooks.collect_app_tags',
    ],
}


# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Password hashers
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]


# ==============================================================================
# EMAIL CONFIGURATION
# ==============================================================================
# CNST-001: NO email backends en NINGUN ambiente
# ==============================================================================

# EMAIL DESHABILITADO POR CNST-001
# NO usar email en el sistema

# Placeholder (no funcional)
# NOTA: Este backend solo imprime en consola, NO envía emails


# ==============================================================================
# ==============================================================================
# CACHE
# ==============================================================================
# CNST-010: NO cache permitido
# Usar SOLO base de datos PostgreSQL para persistencia
# ==============================================================================

# CACHES configuración removida - CUMPLE CNST-010
# Toda persistencia debe usar PostgreSQL directamente

# [ERROR] PROHIBIDO por CNST-010:
# - Redis (django-redis)
# - Memcached
# - LocMemCache (volátil, se pierde en restart)
# - Cualquier cache backend

# [SUCCESS] PERMITIDO por CNST-010:
# - PostgreSQL (único backend de persistencia)
# - Base de datos para sessions (django.contrib.sessions.backends.db)

# ANTES (VIOLABA CNST-010):
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',  # [ERROR] Prohibido
#         'LOCATION': 'iact-cache',
#     }
# }

# AHORA:
# - LoginLockout usa modelo en PostgreSQL
# - Sessions usan tabla django_session en PostgreSQL
# - NO cache en memoria (cumple CNST-010)


# ==============================================================================
# CELERY
# ==============================================================================
# CNST-004 + CNST_TECNICAS: NO Celery
# ==============================================================================

# CELERY DESHABILITADO POR CNST-004 y CNST_TECNICAS
# Usar APScheduler para tareas programadas


# ==============================================================================
# CHANNELS
# ==============================================================================
# CNST-004: NO WebSockets
# ==============================================================================

# CHANNELS DESHABILITADO POR CNST-004
# NO WebSockets
# NO comunicacion en tiempo real via WebSockets


# ==============================================================================
# SENTRY
# ==============================================================================
# CNST_TECNICAS: NO Sentry
# ==============================================================================

# SENTRY DESHABILITADO POR CNST_TECNICAS
# NO monitoreo con Sentry
# Usar logging nativo Django


# ==============================================================================
# APSCHEDULER (alternativa a Celery)
# ==============================================================================
# CNST-004: Usar APScheduler en lugar de Celery
# ==============================================================================

APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
APSCHEDULER_RUN_NOW_TIMEOUT = 25  # Seconds


# ==============================================================================
# AWS S3 CONFIGURATION (CNST-006)
# ==============================================================================
# Configuración para almacenamiento de logs en S3
# CNST-006: Logs deben almacenarse en S3 con rotación de 90 días
# ==============================================================================

# AWS credentials
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_REGION = config('AWS_REGION', default='us-east-1')

# S3 Bucket para logs
AWS_LOGS_BUCKET = config('AWS_LOGS_BUCKET', default='iact-logs-dev')

# Configuración S3
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_FILE_OVERWRITE = False

# CNST-006: Estructura logs en S3
# Formato: logs/YYYY/MM/DD/LEVEL_timestamp_id.log
# Rotación: 90 días en DB, permanente en S3
LOG_ROTATION_DAYS = 90


# ==============================================================================
# CUSTOM SETTINGS
# ==============================================================================

# Archivos permitidos para upload (CSV, XLSX)
ALLOWED_UPLOAD_EXTENSIONS = ['.csv', '.xlsx', '.xls']
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# CNST-007: Límites exportación
MAX_EXPORT_CSV = 100_000  # Máximo 100k registros CSV
MAX_EXPORT_XLSX = 50_000  # Máximo 50k registros XLSX

# Timeout queries
QUERY_TIMEOUT = 30  # 30 segundos


# ==============================================================================
# COMPLIANCE CNST v2.2.1
# ==============================================================================

"""
VERIFICACION COMPLIANCE:

 CNST-002: SESSION_ENGINE = 'django.contrib.sessions.backends.db'
 CNST-003: Dual database (default + ivr_legacy READ-ONLY)
 CNST-004: NO Celery, NO Channels
 CNST-005: Throttling configurado, MAX_PAGE_SIZE = 1000
 CNST-007: MAX_EXPORT_CSV = 100k, MAX_EXPORT_XLSX = 50k
 CNST_TECNICAS: NO Sentry, NO Redis, NO Celery, NO Channels

Compliance: 100%
"""
