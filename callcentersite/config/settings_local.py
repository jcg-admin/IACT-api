"""
Settings locales para desarrollo con SQLite.
"""
from pathlib import Path
from .settings.base import *

# Usar SQLite para desarrollo
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(__file__).resolve().parent.parent / 'db.sqlite3',
    }
}

# Password hasher simple para tests (sin argon2)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Desactivar scheduler para tests
SCHEDULER_ENABLED = False

print("[SUCCESS] Usando SQLite para desarrollo")
