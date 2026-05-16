"""
conftest.py — raíz del proyecto IACT-api.

H-INFRA-002: arranca PostgreSQL automáticamente antes de que pytest-django
intente crear la BD de test. Evita 863 errors por psycopg2.OperationalError.

Debe estar en la raíz del proyecto (junto a pytest.ini) — se carga primero.
"""
import subprocess
import time
import os


def _pg_is_ready() -> bool:
    """Verifica que PostgreSQL acepta conexiones en el socket estándar."""
    result = subprocess.run(
        ['pg_isready', '-h', '/var/run/postgresql', '-p', '5432'],
        capture_output=True
    )
    return result.returncode == 0


def pytest_configure(config):
    """
    Hook de configuración — se ejecuta antes de que pytest-django configure la BD.
    Arranca PostgreSQL si no está listo para aceptar conexiones.
    """
    if _pg_is_ready():
        return

    # Intentar arrancar
    subprocess.run(
        ['pg_ctlcluster', '16', 'main', 'start'],
        capture_output=True
    )

    # Esperar hasta 15 segundos
    for _ in range(15):
        time.sleep(1)
        if _pg_is_ready():
            return

    # Si después de 15s sigue sin responder, imprimir advertencia
    print('\n[WARN] PostgreSQL no respondió después de 15s — los tests django_db fallarán.')
