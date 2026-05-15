"""
Settings para tests de FASE 0 — sin dependencia de PostgreSQL/MariaDB.
Usa SQLite en memoria para velocidad máxima.
"""
from .base import *  # noqa

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {'NAME': ':memory:'},
    },
    'ivr': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {'NAME': None},  # F0-T6: Django no crea BD de test para ivr
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Throttling deshabilitado en tests.
# Motivo: LocMemCache no se limpia entre tests pytest (usa SAVEPOINT, no rollback
# de caché). SQLite reutiliza pk=1 tras SAVEPOINT ROLLBACK, lo que hace que todos
# los tests compartan la clave throttle_change_password_1. Después de suficientes
# tests que hacen POST a /change-password/, la ventana de 10/hour se satura.
# Los tests de throttle específicos (CA-07) deben usar mocking explícito.
# Referencia: H-F6-GRP-GA-001 detectado durante implementación FASE 6.
REST_FRAMEWORK_OVERRIDE = {
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
}

# Aplicar override sobre la configuración base de REST_FRAMEWORK
_base_rf = globals().get('REST_FRAMEWORK', {})
REST_FRAMEWORK = {**_base_rf, **REST_FRAMEWORK_OVERRIDE}

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
