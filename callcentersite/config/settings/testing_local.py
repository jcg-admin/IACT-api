"""
testing_local.py — Settings para tests en entorno local.

Solo agrega TEST: a cada BD. Todo lo demás hereda de base.py.

Principio D-CFG-001: decisiones de configuración → settings files.
Las credenciales y rutas de socket vienen del .env vía base.py.
"""
from .base import *  # noqa: F401, F403

DEBUG = False

DATABASES['default']['TEST'] = {
    'NAME': 'test_iact_analytics',
}

DATABASES['ivr']['TEST'] = {
    'NAME': 'test_ivr_legacy',
    'MIGRATE': False,
    'CREATE_DB': False,
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
