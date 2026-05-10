"""Testing settings.

Sobreescribe DATABASES para apuntar a las BDs de test.
Hereda el resto de base.py (incluyendo config(), DATABASE_ROUTERS, etc.)

Principio D-CFG-001: las credenciales y rutas vienen del .env via base.py.
Este archivo solo sobreescribe los nombres de BD y usa config() para HOST/PORT,
evitando IPs Vagrant hardcodeadas que no aplican en desarrollo local.
"""
from .base import *  # noqa: F401, F403

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'iact_test',
        'USER': config('DB_USER', default='django_user'),
        'PASSWORD': config('DB_PASSWORD', default='django_pass'),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='5432'),
    },
    # Alias 'ivr' — coincide con base.py y con el DatabaseRouter.
    # 'legacy' era incorrecto: el router usa 'ivr' y no encontraba la BD.
    'ivr': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ivr_legacy_test',
        'USER': config('IVR_DB_USER', default='django_user'),
        'PASSWORD': config('IVR_DB_PASSWORD', default='django_pass'),
        'HOST': config('IVR_DB_HOST', default='127.0.0.1'),
        'PORT': config('IVR_DB_PORT', default='3306'),
    },
}

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
