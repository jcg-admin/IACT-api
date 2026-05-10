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
    # 'test_ivr_legacy' = 'test_' + DB_MARIADB_NAME (default: 'ivr_legacy').
    # El provisioner (provisioners/mariadb/setup.sh) crea esta BD con
    # GRANT CREATE, DROP en test_* al usuario django_user.
    # Debe coincidir con DB_MARIADB_NAME definido en .env o su default.
    'NAME': 'test_ivr_legacy',
    'MIGRATE': False,
    'CREATE_DB': False,
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
