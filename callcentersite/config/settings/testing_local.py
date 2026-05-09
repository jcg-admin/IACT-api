"""
testing_local.py — Settings para tests en entorno local de desarrollo.

Hereda toda la configuración de base.py — incluyendo lectura de .env
via config() para credenciales, HOST, PORT, OPTIONS y CONN_MAX_AGE.

Solo agrega lo específico de tests:
  - TEST.NAME para PostgreSQL
  - TEST.MIGRATE=False y TEST.CREATE_DB=False para MariaDB
"""
from .base import *  # noqa: F401, F403

DEBUG = False

# PostgreSQL: agregar solo config de test
DATABASES['default']['TEST'] = {
    'NAME': 'test_iact_analytics',
}

# MariaDB: agregar solo config de test
DATABASES['ivr']['TEST'] = {
    'NAME': 'test_ivr_legacy',
    'MIGRATE': False,
    'CREATE_DB': False,
}

# Hashers rápidos — solo en tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
