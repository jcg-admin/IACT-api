"""
Settings para tests de FASE 0 — BDs reales PostgreSQL + MariaDB.

Usa las mismas BDs que integration_ivr pero con migraciones aplicadas.
El entorno requiere las BDs de IACT-db activas:
    nohup mysqld_safe --user=mysql --socket=/run/mysqld/mysqld.sock ...
    pg_ctlcluster 16 main start

Referencia: H-INT-007 — eliminación de SQLite en tests.
"""
from .base import *  # noqa

DEBUG = False

# PostgreSQL real — BD principal
DATABASES['default'] = {
    'ENGINE':             'django.db.backends.postgresql',
    'NAME':               'iact_analytics',
    'USER':               'django_user',
    'PASSWORD':           'django_pass',
    'HOST':               '127.0.0.1',
    'PORT':               '5432',
    'TIME_ZONE':          None,
    'CONN_MAX_AGE':       0,
    'CONN_HEALTH_CHECKS': False,
    'OPTIONS':            {'connect_timeout': 10},
    'TEST':               {'NAME': 'test_iact_analytics'},
    'AUTOCOMMIT':         True,
    'ATOMIC_REQUESTS':    False,
}

# MariaDB real — BD IVR legada (solo lectura en producción; tests usan test_ivr_legacy)
DATABASES['ivr'] = {
    'ENGINE':             'django.db.backends.mysql',
    'NAME':               'ivr_legacy',
    'USER':               'django_user',
    'PASSWORD':           'django_pass',
    'HOST':               'localhost',          # 'localhost' usa unix_socket en mysql
    'PORT':               '3306',
    'TIME_ZONE':          None,
    'CONN_MAX_AGE':       0,
    'CONN_HEALTH_CHECKS': False,
    'OPTIONS': {
        'charset':     'utf8mb4',
        'unix_socket': '/run/mysqld/mysqld.sock',
    },
    'TEST': {
        'NAME':      'test_ivr_legacy',
        'MIGRATE':   False,
        'CREATE_DB': True,
    },
    'AUTOCOMMIT':         True,
    'ATOMIC_REQUESTS':    False,
}

# DummyCache — evita contaminación de throttle entre tests.
# AnonLoginThrottle usa el cache por IP; con DummyCache el contador
# no persiste entre requests de distintos tests.
# Ref: H-INT-008
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Throttle deshabilitado globalmente en la suite de tests.
# Los tests de throttle específicos usan mocking explícito.
# Ref: H-F6-GRP-GA-001
REST_FRAMEWORK_OVERRIDE = {
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES':   {},
}
_base_rf = globals().get('REST_FRAMEWORK', {})
REST_FRAMEWORK = {**_base_rf, **REST_FRAMEWORK_OVERRIDE}

# MD5 acelera el hashing de passwords en tests (no producción)
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
SESSION_COOKIE_SECURE  = False
CSRF_COOKIE_SECURE     = False
SECURE_SSL_REDIRECT    = False
ALLOWED_HOSTS          = ['testserver', 'localhost', '127.0.0.1']
