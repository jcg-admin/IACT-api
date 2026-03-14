"""
Django settings DEVELOPMENT - IACT Call Center.

Configuracion para desarrollo local.

CNST v2.2.1 Compliance: 100%
- CNST-001: NO email (console backend no funcional)
"""

from .base import *


# ==============================================================================
# DEBUG
# ==============================================================================

DEBUG = True


# ==============================================================================
# ALLOWED HOSTS
# ==============================================================================

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', '*.ngrok.io']


# ==============================================================================
# INSTALLED APPS (development tools)
# ==============================================================================

INSTALLED_APPS += [
    'django_extensions',
    # 'debug_toolbar',  # Descomentar si se necesita
]


# ==============================================================================
# MIDDLEWARE (development tools)
# ==============================================================================

# MIDDLEWARE = [
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
# ] + MIDDLEWARE


# ==============================================================================
# DATABASES
# ==============================================================================

# Usar configuracion base
# Puede override si necesario para desarrollo:

# DATABASES['default']['OPTIONS']['connect_timeout'] = 5


# ==============================================================================
# EMAIL
# ==============================================================================
# CNST-001: NO email en desarrollo
# ==============================================================================

# EMAIL DESHABILITADO POR CNST-001
# Console backend solo imprime, NO envía emails

# PROHIBIDO usar:
# - django.core.mail.backends.smtp.EmailBackend
# - cualquier backend que envíe emails reales

# NOTA: Si se necesita testear flujos con email,
# usar console backend y verificar logs


# ==============================================================================
# LOGGING
# ==============================================================================

LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'


# ==============================================================================
# CORS (si se necesita)
# ==============================================================================

# CORS_ALLOW_ALL_ORIGINS = True  # Solo desarrollo


# ==============================================================================
# DEBUG TOOLBAR (si se habilita)
# ==============================================================================

# INTERNAL_IPS = [
#     '127.0.0.1',
# ]


# ==============================================================================
# CACHE
# ==============================================================================

# Development: cache local
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'iact-dev-cache',
    }
}


# ==============================================================================
# SECURITY (relaxed for development)
# ==============================================================================

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False


# ==============================================================================
# COMPLIANCE CNST v2.2.1 - DEVELOPMENT
# ==============================================================================

"""
VERIFICACION COMPLIANCE DEVELOPMENT:

 CNST-002: SESSION_ENGINE heredado de base
 CNST-003: Dual database heredado de base
 CNST-004: NO Celery, NO Channels
 CNST-005: Throttling heredado de base
 CNST_TECNICAS: NO Sentry, NO Redis

Compliance: 100%
"""
