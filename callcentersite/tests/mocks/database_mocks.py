"""
Mocks para conexiones de Base de Datos.

CNST-002: Dual DB (PostgreSQL + MariaDB IVR readonly).
CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from decimal import Decimal
from datetime import date, datetime


# ============================================================================
# DEUDA TÉCNICA — PENDIENTE
# ============================================================================
# Fecha de eliminación: 2026-03-21
# Motivo: Las fixtures de conexión IVR (mock_ivr_connection y derivadas)
#         simulaban acceso a tablas que no existen (call_logs, QuarterlyReport,
#         etc.). Desactivadas junto con IVRAdapter y los modelos legacy.
#         Reactivar cuando el schema real de ivr_legacy esté provisionado.
# Ver: documentos/planes/PLAN_IVR_SIMPLIFICACION_20260321.md
# ============================================================================
#
# @pytest.fixture
# def mock_ivr_connection(mocker):
#     """Mock de conexión a BD IVR (MariaDB en producción)."""
#     mock_connection = MagicMock()
#     mock_cursor = MagicMock()
#     mock_connection.cursor.return_value = mock_cursor
#     mock_cursor.fetchall.return_value = [
#         (2025, 1, 10000, 5000, 180, Decimal('500.5'), Decimal('0.15')),
#         (2025, 2, 12000, 6000, 190, Decimal('600.0'), Decimal('0.12')),
#     ]
#     mock_cursor.fetchone.return_value = (2025, 1, 10000, 5000, 180)
#     mock_connection.commit.side_effect = Exception(
#         "IVR database is readonly - COMMIT not allowed"
#     )
#     mocker.patch(
#         'django.db.connections.__getitem__',
#         side_effect=lambda db_alias: mock_connection if db_alias == 'ivr' else Mock()
#     )
#     return mock_connection
#
# @pytest.fixture
# def mock_ivr_cursor_quarterly(mocker, mock_ivr_connection): ...
#
# @pytest.fixture
# def mock_ivr_cursor_transfers(mocker, mock_ivr_connection): ...
#
# @pytest.fixture
# def mock_ivr_empty_result(mocker, mock_ivr_connection): ...
#
# @pytest.fixture
# def mock_readonly_violation(mocker, mock_ivr_connection): ...
#
# @pytest.fixture
# def mock_slow_query(mocker, mock_ivr_connection): ...


# ============================================================================
# POSTGRESQL MOCKS
# ============================================================================

@pytest.fixture
def mock_postgresql_connection(mocker):
    """
    Mock de conexión a PostgreSQL (BD principal).

    En tests: SQLite
    En producción: PostgreSQL
    """
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    mock_connection.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None

    mocker.patch(
        'django.db.connections.__getitem__',
        side_effect=lambda db_alias: mock_connection if db_alias == 'default' else Mock()
    )

    return mock_connection


# ============================================================================
# DATABASE ROUTER MOCKS
# ============================================================================

# DEUDA TÉCNICA — PENDIENTE
# mock_database_router desactivado: importaba 'apps.ivr.routers.IVRRouter'
# que no existe en el código actual (el router está en config/db_router.py).
# =============================================================================
#
# @pytest.fixture
# def mock_database_router(mocker):
#     from apps.ivr.routers import IVRRouter   # NO EXISTE
#     ...


# ============================================================================
# ERROR MOCKS
# ============================================================================

@pytest.fixture
def mock_connection_error(mocker):
    """
    Mock que simula error de conexión a BD.
    """
    mock_connection = MagicMock()
    mock_connection.cursor.side_effect = Exception("Database connection failed")

    mocker.patch(
        'django.db.connections.__getitem__',
        return_value=mock_connection
    )

    return mock_connection


# ============================================================================
# HELPER MOCKS
# ============================================================================

@pytest.fixture
def mock_database_settings(mocker):
    """
    Mock de settings.DATABASES para tests.
    Configura SQLite para ambas BD en tests.
    """
    test_databases = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        },
        'ivr': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

    mocker.patch('django.conf.settings.DATABASES', test_databases)

    return test_databases


@pytest.fixture
def mock_transaction_atomic(mocker):
    """
    Mock de transaction.atomic() para tests.
    """
    mock_atomic = MagicMock()
    mock_atomic.__enter__ = MagicMock()
    mock_atomic.__exit__ = MagicMock()

    mocker.patch('django.db.transaction.atomic', return_value=mock_atomic)

    return mock_atomic
