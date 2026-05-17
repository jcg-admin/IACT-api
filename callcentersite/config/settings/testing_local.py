"""
testing_local.py — Settings para tests en entorno local.

Solo agrega TEST: a cada BD. Todo lo demás hereda de base.py.

Principio D-CFG-001: decisiones de configuración → settings files.
Las credenciales y rutas de socket vienen del .env vía base.py.
"""
from .base import *  # noqa: F401, F403

DEBUG = False

# Throttle: deshabilitado en tests para evitar contaminación de estado entre
# requests dentro de la misma sesión de pytest. El LocMemCache por defecto
# acumula hits del throttle entre tests cuando no hay CACHES configurado.
# Ver: config/settings/fase0_testing.py (mismo patrón).
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}

# Caché: DummyCache garantiza que no persiste estado entre tests.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

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
