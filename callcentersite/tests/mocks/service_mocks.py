"""
tests/mocks/service_mocks.py

Stub de service_mocks — reconstruido en F6-P0 (H-F6-GRP-P0-003).
El archivo original fue omitido del repositorio (probablemente por .gitignore).
Los fixtures son mocks pytest compatibles con el contrato del __init__.py.
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_etl_service():
    with patch('apps.pipeline.services.ETLService') as m:
        m.return_value.run.return_value = {'status': 'success', 'rows': 100}
        yield m


@pytest.fixture
def mock_etl_service_empty():
    with patch('apps.pipeline.services.ETLService') as m:
        m.return_value.run.return_value = {'status': 'success', 'rows': 0}
        yield m


@pytest.fixture
def mock_etl_service_error():
    with patch('apps.pipeline.services.ETLService') as m:
        m.return_value.run.side_effect = Exception('ETL connection failed')
        yield m


@pytest.fixture
def mock_report_generator_service():
    return MagicMock(name='mock_report_generator_service')


@pytest.fixture
def mock_report_service_limit_exceeded():
    return MagicMock(name='mock_report_service_limit_exceeded')


@pytest.fixture
def mock_access_service():
    return MagicMock(name='mock_access_service')


@pytest.fixture
def mock_access_service_denied():
    m = MagicMock(name='mock_access_service_denied')
    m.check.return_value = False
    return m


@pytest.fixture
def mock_audit_service():
    return MagicMock(name='mock_audit_service')


@pytest.fixture
def mock_user_service():
    return MagicMock(name='mock_user_service')


@pytest.fixture
def mock_authentication_service():
    return MagicMock(name='mock_authentication_service')


@pytest.fixture
def mock_authentication_service_invalid():
    m = MagicMock(name='mock_authentication_service_invalid')
    m.authenticate.return_value = None
    return m


@pytest.fixture
def mock_dashboard_service():
    return MagicMock(name='mock_dashboard_service')


@pytest.fixture
def mock_alert_service():
    return MagicMock(name='mock_alert_service')
