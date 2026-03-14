"""
Mocks para conexiones de Base de Datos.

CONTEXTO: NO tenemos IPs de MySQL/PostgreSQL reales en desarrollo/tests.
Simulamos respuestas de BD usando mocks.

RESTRICCIONES:
- CNST-002: Dual DB (PostgreSQL + MariaDB IVR readonly)
- En tests: SQLite para ambas BD
- En mocks: Simulamos queries sin tocar BD real

CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from decimal import Decimal
from datetime import date, datetime


# ============================================================================
# IVR DATABASE MOCKS (MariaDB -> SQLite en tests)
# ============================================================================

@pytest.fixture
def mock_ivr_connection(mocker):
    """
    Mock de conexión a BD IVR (MariaDB en producción).
    
    CNST-002: BD IVR es readonly.
    En tests: Simula queries SELECT sin tocar BD real.
    
    Uso:
        def test_etl(mock_ivr_connection):
            # BD IVR mockeada, retorna datos fake
            data = extract_ivr_data()
            assert len(data) > 0
    
    Simula:
        - cursor.execute()
        - cursor.fetchall()
        - cursor.fetchone()
        - connection.commit() (NO permitido en readonly)
    """
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    
    # Configurar cursor
    mock_connection.cursor.return_value = mock_cursor
    
    # Datos fake de ejemplo (QuarterlyReport)
    mock_cursor.fetchall.return_value = [
        (2025, 1, 10000, 5000, 180, Decimal('500.5'), Decimal('0.15')),
        (2025, 2, 12000, 6000, 190, Decimal('600.0'), Decimal('0.12')),
    ]
    
    mock_cursor.fetchone.return_value = (2025, 1, 10000, 5000, 180)
    
    # commit() NO permitido en readonly (debe lanzar error)
    mock_connection.commit.side_effect = Exception(
        "IVR database is readonly - COMMIT not allowed"
    )
    
    # Mockear django.db.connections['ivr_legacy']
    mocker.patch(
        'django.db.connections.__getitem__',
        side_effect=lambda db_alias: mock_connection if db_alias == 'ivr' else Mock()
    )
    
    return mock_connection


@pytest.fixture
def mock_ivr_cursor_quarterly(mocker, mock_ivr_connection):
    """
    Mock específico para queries de QuarterlyReport.
    
    Uso:
        def test_quarterly_etl(mock_ivr_cursor_quarterly):
            data = QuarterlyReport.objects.using('ivr_legacy').all()
            # Retorna datos mockeados de quarterly
    """
    cursor = mock_ivr_connection.cursor.return_value
    
    cursor.fetchall.return_value = [
        {
            'year': 2025,
            'quarter': 1,
            'total_calls': 10000,
            'unique_clients': 5000,
            'avg_duration_seconds': 180,
            'total_duration_hours': Decimal('500.5'),
            'abandonment_rate': Decimal('0.15')
        }
    ]
    
    return cursor


@pytest.fixture
def mock_ivr_cursor_transfers(mocker, mock_ivr_connection):
    """
    Mock específico para queries de TransferReport.
    
    Uso:
        def test_transfer_etl(mock_ivr_cursor_transfers):
            data = TransferReport.objects.using('ivr_legacy').all()
    """
    cursor = mock_ivr_connection.cursor.return_value
    
    cursor.fetchall.return_value = [
        {
            'year': 2025,
            'quarter': 1,
            'menu_option': '1',
            'total_transfers': 500,
            'avg_wait_time_seconds': 30,
            'successful_transfers': 450,
            'failed_transfers': 50
        },
        {
            'year': 2025,
            'quarter': 1,
            'menu_option': '2',
            'total_transfers': 300,
            'avg_wait_time_seconds': 25,
            'successful_transfers': 280,
            'failed_transfers': 20
        }
    ]
    
    return cursor


@pytest.fixture
def mock_ivr_empty_result(mocker, mock_ivr_connection):
    """
    Mock que retorna resultado vacío (sin datos).
    
    Uso:
        def test_etl_no_data(mock_ivr_empty_result):
            data = extract_ivr_data()
            assert len(data) == 0
    """
    cursor = mock_ivr_connection.cursor.return_value
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None
    
    return cursor


# ============================================================================
# POSTGRESQL MOCKS
# ============================================================================

@pytest.fixture
def mock_postgresql_connection(mocker):
    """
    Mock de conexión a PostgreSQL (BD principal).
    
    En tests: SQLite
    En producción: PostgreSQL
    
    Uso:
        def test_user_query(mock_postgresql_connection):
            users = User.objects.all()
            # Query usa SQLite en tests
    """
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    
    mock_connection.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None
    
    # Mockear conexión default
    mocker.patch(
        'django.db.connections.__getitem__',
        side_effect=lambda db_alias: mock_connection if db_alias == 'default' else Mock()
    )
    
    return mock_connection


# ============================================================================
# DATABASE ROUTER MOCKS
# ============================================================================

@pytest.fixture
def mock_database_router(mocker):
    """
    Mock del Database Router (IVRRouter).
    
    CNST-002: Router decide qué BD usar.
    - IVR models -> 'ivr_legacy' (readonly)
    - Otros models -> 'default' (PostgreSQL/SQLite)
    
    Uso:
        def test_router(mock_database_router):
            # Router mockeado retorna BD correcta
            assert router.db_for_read(IVRModel) == 'ivr_legacy'
            assert router.db_for_write(IVRModel) is None  # readonly
    """
    from apps.ivr.routers import IVRRouter
    
    mock_router = MagicMock(spec=IVRRouter)
    
    # db_for_read: IVR -> 'ivr', otros -> 'default'
    def mock_db_for_read(model, **hints):
        if hasattr(model, '_meta') and model._meta.app_label == 'ivr':
            return 'ivr'
        return 'default'

    mock_router.db_for_read.side_effect = mock_db_for_read

    # db_for_write: IVR -> None (readonly), otros -> 'default'
    def mock_db_for_write(model, **hints):
        if hasattr(model, '_meta') and model._meta.app_label == 'ivr':
            return None  # IVR readonly
        return 'default'

    mock_router.db_for_write.side_effect = mock_db_for_write

    # allow_relation: siempre True en tests
    mock_router.allow_relation.return_value = True

    # allow_migrate: IVR no migra, otros sí
    def mock_allow_migrate(db, app_label, model_name=None, **hints):
        if app_label == 'ivr':
            return db == 'ivr'
        return db == 'default'
    
    mock_router.allow_migrate.side_effect = mock_allow_migrate
    
    mocker.patch(
        'apps.ivr_legacy.routers.IVRRouter',
        return_value=mock_router
    )
    
    return mock_router


@pytest.fixture
def mock_readonly_violation(mocker, mock_ivr_connection):
    """
    Mock que simula violación de readonly (intento de WRITE en IVR).
    
    Uso:
        def test_ivr_readonly(mock_readonly_violation):
            with pytest.raises(Exception, match="readonly"):
                # Intento de crear objeto en BD IVR
                QuarterlyReport.objects.create(year=2025, quarter=1)
    """
    cursor = mock_ivr_connection.cursor.return_value
    
    # execute() con INSERT/UPDATE/DELETE lanza error
    def mock_execute(sql, params=None):
        sql_upper = sql.upper() if isinstance(sql, str) else ''
        if any(keyword in sql_upper for keyword in ['INSERT', 'UPDATE', 'DELETE']):
            raise Exception("IVR database is readonly - WRITE operations not allowed")
    
    cursor.execute.side_effect = mock_execute
    
    return cursor


# ============================================================================
# QUERY PERFORMANCE MOCKS
# ============================================================================

@pytest.fixture
def mock_slow_query(mocker, mock_ivr_connection):
    """
    Mock que simula query lenta (timeout).
    
    Uso:
        def test_query_timeout(mock_slow_query):
            with pytest.raises(Exception, match="timeout"):
                extract_ivr_data()
    """
    import time
    cursor = mock_ivr_connection.cursor.return_value
    
    def slow_fetchall():
        time.sleep(5)  # Simular query lenta
        raise Exception("Query timeout after 5 seconds")
    
    cursor.fetchall.side_effect = slow_fetchall
    
    return cursor


@pytest.fixture
def mock_connection_error(mocker):
    """
    Mock que simula error de conexión a BD.
    
    Uso:
        def test_connection_failure(mock_connection_error):
            with pytest.raises(Exception, match="connection"):
                connect_to_ivr()
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
    
    Uso:
        def test_settings(mock_database_settings):
            from django.conf import settings
            assert settings.DATABASES['default']['ENGINE'] == 'sqlite3'
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
    
    En tests, las transacciones son manejadas por pytest-django.
    
    Uso:
        def test_atomic(mock_transaction_atomic):
            with transaction.atomic():
                # Operaciones
                pass
    """
    mock_atomic = MagicMock()
    mock_atomic.__enter__ = MagicMock()
    mock_atomic.__exit__ = MagicMock()
    
    mocker.patch('django.db.transaction.atomic', return_value=mock_atomic)
    
    return mock_atomic


# ============================================================================
# TOTAL MOCKS: 12
# 
# IVR Connection Mocks (5):
#   - mock_ivr_connection (base)
#   - mock_ivr_cursor_quarterly
#   - mock_ivr_cursor_transfers
#   - mock_ivr_empty_result
#   - mock_readonly_violation
# 
# PostgreSQL Mocks (1):
#   - mock_postgresql_connection
# 
# Router Mocks (1):
#   - mock_database_router
# 
# Error Mocks (2):
#   - mock_slow_query
#   - mock_connection_error
# 
# Helper Mocks (3):
#   - mock_database_settings
#   - mock_transaction_atomic
# 
# CNST-002: Dual DB (readonly IVR) [SUCCESS]
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
