"""
Settings locales con SQLite — para desarrollo sin servidor de BD.
Usar cuando PostgreSQL/MariaDB no estan disponibles.

Activar con:
  export DJANGO_SETTINGS_MODULE=config.settings.local_sqlite
"""
from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

INSTALLED_APPS += ['django_extensions']

# SQLite para ambas bases — permite arrancar sin instalar nada
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_local.sqlite3',
    },
    'ivr': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_ivr_local.sqlite3',
    },
}

# Sin Redis ni cache externa
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# Usar PBKDF2 en lugar de Argon2 (no disponible sin red)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]
