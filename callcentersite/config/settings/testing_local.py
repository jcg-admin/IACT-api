"""
testing_local.py — Settings para tests en entorno local de desarrollo.

Diferencias respecto a testing.py (que apunta a 192.168.56.x):
  - PostgreSQL: 127.0.0.1:5432 (instancia local)
  - MariaDB:    127.0.0.1:3306 (instancia local)
  - Alias 'ivr' (consistente con base.py y db_router.py)

Bug corregido de testing.py:
  testing.py usaba alias 'legacy' para la BD secundaria.
  El DatabaseRouter en db_router.py espera el alias 'ivr'.
  Con alias incorrecto, el router no encontraba la BD y
  todas las queries a apps.ivr fallaban silenciosamente.
"""
from .base import *  # noqa: F401, F403

DEBUG = False

DATABASES = {
    # PostgreSQL — BD principal (READ + WRITE)
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'iact_analytics',
        'USER': 'django_user',
        'PASSWORD': 'django_pass',
        'HOST': '127.0.0.1',
        'PORT': '5432',
        'TEST': {
            'NAME': 'test_iact_analytics',
        },
    },

    # MariaDB — ivr_legacy (READ-ONLY, CNST-003)
    # Alias 'ivr' requerido por config/db_router.py
    # Usa socket en entorno local (sin systemd, sin TCP en 3306)
    'ivr': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ivr_legacy',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '',          # vacío → usa socket
        'PORT': '',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'unix_socket': '/run/mysqld/mysqld.sock',
            'read_default_file': '',
        },
        'TEST': {
            'NAME': 'test_ivr_legacy',
            # IACT-db provee el schema — Django no gestiona esta BD.
            # pytest-django no debe destruirla ni correr migraciones en ella.
            'MIGRATE': False,
            'CREATE_DB': False,
        },
    },
}

# Hashers rapidos para tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
