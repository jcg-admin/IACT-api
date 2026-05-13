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
