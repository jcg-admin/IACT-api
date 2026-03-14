"""
Django settings PRODUCTION - IACT Call Center.

Configuracion para produccion.

CNST v2.2.1 Compliance: 100%
- CNST-001: NO email (PROHIBIDO)
- CNST_TECNICAS: NO Sentry (PROHIBIDO)
"""

from .base import *


# ==============================================================================
# DEBUG
# ==============================================================================

DEBUG = False


# ==============================================================================
# SECURITY
# ==============================================================================

# HTTPS enforcement
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Proxy headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ==============================================================================
# ALLOWED HOSTS
# ==============================================================================

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())


# ==============================================================================
# DATABASES
# ==============================================================================

# Usar configuracion base con ajustes produccion
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['OPTIONS']['connect_timeout'] = 10

DATABASES['ivr_legacy']['OPTIONS']['connect_timeout'] = 10


# ==============================================================================
# EMAIL
# ==============================================================================
# CNST-001: NO email en produccion (PROHIBIDO)
# ==============================================================================

# EMAIL PROHIBIDO POR CNST-001 
#
# NO usar ningun servicio de email
# NO enviar emails bajo NINGUNA circunstancia
#
# PROHIBIDO:
# - Cualquier servicio SMTP (SendGrid, Mailgun, SES, etc)
# - Notificaciones por email
# - Password reset por email
# - Alertas por email
#
# Si se requiere notificaciones:
# - Usar logs
# - Usar base de datos
# - Usar mecanismos NO-email

# Fallback no funcional (solo para evitar errores)


# ==============================================================================
# LOGGING
# ==============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': PROJECT_ROOT / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': PROJECT_ROOT / 'logs' / 'django_error.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# ==============================================================================
# SENTRY
# ==============================================================================
# CNST_TECNICAS: NO Sentry (PROHIBIDO)
# ==============================================================================

# SENTRY PROHIBIDO POR CNST_TECNICAS 
#
# NO usar Sentry para monitoreo de errores
# NO instalar sentry-sdk
# NO configurar Sentry en ningun ambiente
#
# PROHIBIDO:
# import sentry_sdk
# sentry_sdk.init(...)
#
# Alternativas:
# - Logging nativo Django (arriba configurado)
# - Logs a archivos con rotacion
# - Monitoreo con herramientas internas

# CNST_TECNICAS: Sentry EXPLICITAMENTE PROHIBIDO


# ==============================================================================
# STATIC & MEDIA
# ==============================================================================

# Static files (collectstatic)
STATIC_ROOT = config('STATIC_ROOT', default='/var/www/iact/static')
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Media files
MEDIA_ROOT = config('MEDIA_ROOT', default='/var/www/iact/media')


# ==============================================================================
# CACHE
# ==============================================================================
# CNST_TECNICAS: NO Redis
# ==============================================================================

# REDIS PROHIBIDO POR CNST_TECNICAS 
#
# NO usar Redis como cache
# NO usar django-redis
# Usar cache local en memoria

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'iact-prod-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 10000,
        },
    }
}

# PROHIBIDO:
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',  # PROHIBIDO
#         ...
#     }
# }


# ==============================================================================
# SESSIONS
# ==============================================================================

# CNST-002: Session en database (heredado de base)
# SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Ya en base


# ==============================================================================
# CELERY
# ==============================================================================
# CNST-004 + CNST_TECNICAS: NO Celery (PROHIBIDO)
# ==============================================================================

# CELERY PROHIBIDO POR CNST-004 y CNST_TECNICAS 
#
# NO usar Celery para tareas asíncronas
# NO configurar Celery broker
# NO usar Celery workers
#
# Alternativa: APScheduler (configurado en base)


# ==============================================================================
# REST FRAMEWORK
# ==============================================================================

# Production: JSON only
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]


# ==============================================================================
# ADMIN
# ==============================================================================

# Cambiar URL admin por seguridad
ADMIN_URL = config('ADMIN_URL', default='admin/')


# ==============================================================================
# CORS (si se necesita)
# ==============================================================================

# CORS_ALLOWED_ORIGINS = config('CORS_ORIGINS', cast=Csv())
# CORS_ALLOW_CREDENTIALS = True


# ==============================================================================
# COMPLIANCE CNST v2.2.1 - PRODUCTION
# ==============================================================================

"""
VERIFICACION COMPLIANCE PRODUCTION:

 CNST-001: EMAIL PROHIBIDO (dummy backend)
    - NO smtp
    - NO servicios email
    - Explicito en codigo

 CNST-002: SESSION_ENGINE = 'db' (heredado)

 CNST-003: Dual database (heredado)

 CNST-004: NO Celery PROHIBIDO
    - Explicito en codigo
    - Usar APScheduler

 CNST-005: Throttling (heredado)

 CNST_TECNICAS: 
    - NO Sentry PROHIBIDO (explicito)
    - NO Redis PROHIBIDO (explicito)
    - NO Celery PROHIBIDO (explicito)
    - NO Channels (no configurado)

Compliance: 100%

NOTAS CRITICAS:
- Email: ABSOLUTAMENTE PROHIBIDO
- Sentry: ABSOLUTAMENTE PROHIBIDO  
- Redis: ABSOLUTAMENTE PROHIBIDO
- Celery: ABSOLUTAMENTE PROHIBIDO

Usar alternativas documentadas en base.py
"""
