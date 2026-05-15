"""
integration_ivr.py — Tests de integración con BDs reales del sandbox.

- default: PostgreSQL real (iact_analytics en 127.0.0.1:5432)
- ivr:     MariaDB real   (ivr_legacy via /run/mysqld/mysqld.sock)

Arranca las BDs con:
    nohup mysqld_safe --user=mysql --socket=/run/mysqld/mysqld.sock >/tmp/msqld.log 2>&1 &
    pg_ctlcluster 16 main start
"""
from .fase0_testing import *  # noqa: F401, F403

# PostgreSQL real
DATABASES['default'] = {
    'ENGINE':            'django.db.backends.postgresql',
    'NAME':              'iact_analytics',
    'USER':              'django_user',
    'PASSWORD':          'django_pass',
    'HOST':              '127.0.0.1',
    'PORT':              '5432',
    'TIME_ZONE':         None,
    'CONN_MAX_AGE':      0,
    'CONN_HEALTH_CHECKS': False,
    'OPTIONS':           {'connect_timeout': 10},
    'TEST':              {'NAME': 'test_iact_analytics'},
    'AUTOCOMMIT':        True,
    'ATOMIC_REQUESTS':   False,
}

# MariaDB real via socket Unix
DATABASES['ivr'] = {
    'ENGINE':            'django.db.backends.mysql',
    'NAME':              'ivr_legacy',
    'USER':              'django_user',
    'PASSWORD':          'django_pass',
    'HOST':              'localhost',
    'PORT':              '3306',
    'TIME_ZONE':         None,
    'CONN_MAX_AGE':      0,
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
    'AUTOCOMMIT':      True,
    'ATOMIC_REQUESTS': False,
}

# Throttle cache deshabilitado en tests de integración.
# DummyCache evita que el conteo de intentos (AnonLoginThrottle) persista
# entre tests que comparten la misma IP (127.0.0.1 en el test runner).
# Ref: H-INT-008 — LockoutService usa PostgreSQL (persiste) pero
# AnonLoginThrottle usa CACHES (volátil). DummyCache limpia el throttle
# entre transacciones Django pero no entre tests sin clear explícito.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
