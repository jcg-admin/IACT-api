"""
conftest.py — tests/unit/config/

Configuracion local de pytest para los tests del patron OCP
de drf-spectacular. No carga las fixtures del proyecto que
requieren BD externa (PostgreSQL en 192.168.56.11).

Estos tests son puramente unitarios: no necesitan BD, no necesitan
fixtures de usuarios ni RBAC. Solo necesitan Django configurado
(DJANGO_SETTINGS_MODULE) para poder importar los modulos.
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.testing')


def pytest_configure(config):
    """Configura Django sin iniciar la BD."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.testing')
