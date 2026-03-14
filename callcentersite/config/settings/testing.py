"""Testing settings."""
from .base import *  # noqa: F401, F403

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'iact_test',
        'USER': 'django_user',
        'PASSWORD': 'django_pass',
        'HOST': '192.168.56.11',
        'PORT': '5432',
    },
    'legacy': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ivr_legacy_test',
        'USER': 'django_user',
        'PASSWORD': 'django_pass',
        'HOST': '192.168.56.10',
        'PORT': '3306',
    },
}

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
