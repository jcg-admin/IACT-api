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
# DATABASES — Schemas aislados para tests
# ==============================================================================
# Hereda conexiones de base.py (.env: host, user, password).
# Django crea/destruye estos schemas automáticamente al correr pytest.
#
# default → test_iact_analytics  (PostgreSQL — migrations completas)
# ivr     → test_ivr_legacy      (MariaDB — schema vacío, managed=False)
#
# El schema de IVR (tbl_temp_prueba_ivr) es responsabilidad del provisioner:
#   scripts/provisioners/mariadb/schema_temp_prueba.sh
# Python solo CONSUME (SELECT) — no crea schema desde Python.
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# ==============================================================================

DATABASES['default']['TEST'] = {'NAME': 'test_iact_analytics'}
# ivr MIGRATE=False: IVR es READ-ONLY (CNST-003). Modelos managed=False,
# no hay tablas que crear. Django no corre migrations ni necesita INSERT.
# Tests de IVR usan mocks (tests/mocks/database_mocks.py). Bug B-20/B-21.
DATABASES['ivr']['TEST'] = {'NAME': 'test_ivr_legacy', 'MIGRATE': False}


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
