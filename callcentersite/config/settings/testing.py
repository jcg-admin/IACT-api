"""
Django settings TESTING - IACT Call Center.

Configuracion para ejecucion tests (pytest).

CNST v2.2.1 Compliance: 100%
- CNST-001: NO email (locmem backend para tests)
"""

from .base import *


# ==============================================================================
# DEBUG
# ==============================================================================

DEBUG = False


# ==============================================================================
# SECRET KEY (test only)
# ==============================================================================

SECRET_KEY = 'django-insecure-test-key-DO-NOT-USE-IN-PRODUCTION'


# ==============================================================================
# DATABASES (in-memory for speed)
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
    # IVR legacy se mantiene si tests lo requieren
    # O se puede mock
}


# ==============================================================================
# EMAIL
# ==============================================================================
# CNST-001: NO email en tests
# ==============================================================================

# EMAIL DESHABILITADO POR CNST-001
# locmem backend almacena en memoria, NO envía emails

# PROHIBIDO usar:
# - django.core.mail.backends.smtp.EmailBackend
# - cualquier backend que envíe emails reales

# NOTA: locmem permite verificar emails en tests:
# from django.core import mail
# assert len(mail.outbox) == 0  # Siempre 0 si no se usa


# ==============================================================================
# PASSWORD HASHERS (fast for tests)
# ==============================================================================

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]


# ==============================================================================
# CACHES (dummy for tests)
# ==============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}


# ==============================================================================
# LOGGING (minimal)
# ==============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'level': 'CRITICAL',
        },
    },
}


# ==============================================================================
# MEDIA & STATIC (temp)
# ==============================================================================
# CORRECCIÓN: Paths dinámicos usando tempfile (agnóstico del sistema)

import tempfile
from pathlib import Path

MEDIA_ROOT = Path(tempfile.gettempdir()) / 'iact-test-media'
STATIC_ROOT = Path(tempfile.gettempdir()) / 'iact-test-static'


# ==============================================================================
# CELERY (disabled for tests)
# ==============================================================================

# CNST-004: NO Celery
# En tests, ejecutar tareas sincronicamente


# ==============================================================================
# COMPLIANCE CNST v2.2.1 - TESTING
# ==============================================================================

"""
VERIFICACION COMPLIANCE TESTING:

 CNST-002: SESSION_ENGINE heredado de base
 CNST-003: Database simplificada para tests
 CNST-004: NO Celery
 CNST-005: Throttling heredado de base
 CNST_TECNICAS: NO Sentry, NO Redis

Compliance: 100%
"""
