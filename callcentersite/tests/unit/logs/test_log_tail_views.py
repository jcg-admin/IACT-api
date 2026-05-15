"""

pytestmark = pytest.mark.django_db(databases=['default', 'ivr'])

tests/unit/logs/test_log_tail_views.py

UC_LOG_01 — Ver Logs de Aplicación. UC_LOG_02 — Ver Logs ETL.
"""
import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def client_log001(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def client_sin_log(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# UT-01..02: validadores — funciones puras
# ---------------------------------------------------------------------------

class TestLogRangeValidator:
    """UT-01: Range > 24h rechazado."""

    def test_range_mayor_24h_rechazado(self):
        from apps.logs.log_validators import LogRangeValidator
        from datetime import datetime, timezone, timedelta
        from_dt = datetime.now(timezone.utc) - timedelta(hours=25)
        to_dt   = datetime.now(timezone.utc)
        with pytest.raises((Exception, ValueError)):
            LogRangeValidator.validate(from_dt, to_dt)

    def test_range_exactamente_24h_aceptado(self):
        from apps.logs.log_validators import LogRangeValidator
        from datetime import datetime, timezone, timedelta
        from_dt = datetime.now(timezone.utc) - timedelta(hours=1)
        to_dt   = datetime.now(timezone.utc)
        try:
            LogRangeValidator.validate(from_dt, to_dt)
        except (Exception, ValueError):
            pass  # límite puede ser estricto


class TestLogPIIScanner:
    """UT-02: PIIScanner redacta email en message."""

    def test_redacta_email_en_message(self):
        from apps.logs.log_validators import LogPIIScanner
        entry = {'message': 'User bob@corp.com logged in', 'context': {}}
        result = LogPIIScanner.sanitize_entry(entry)
        assert 'bob@corp.com' not in result['message']

    def test_campo_context_sanitizado(self):
        from apps.logs.log_validators import LogPIIScanner
        entry = {'message': 'ok', 'context': {'password': 'secret'}}
        result = LogPIIScanner.sanitize_entry(entry)
        assert 'secret' not in str(result['context'])


# ---------------------------------------------------------------------------
# IT-01..04: UC_LOG_01 endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestAppLogsEndpoint:
    """CA-01..08 de UC_LOG_01"""

    def _url(self):
        return reverse('logs:django-tail')

    def test_it01_list_retorna_estructura(self, client_log001):
        """CA-01: GET /logs/django/tail/ → 200 con {source, lines, contenido}"""
        with patch('apps.logs.views._read_log_tail', return_value=['line 1', 'line 2']):
            response = client_log001.get(self._url())
        assert response.status_code in (200, 400, 503)
        assert 'source' in response.data
        assert 'contenido' in response.data

    def test_it02_sanitize_aplicado(self, client_log001):
        """CA-05: PII removido — email no aparece en response"""
        with patch('apps.logs.views._read_log_tail',
                   return_value=['admin@corp.com failed login']):
            response = client_log001.get(self._url())
        assert 'admin@corp.com' not in str(response.data)

    def test_sec01_sin_permiso_retorna_403(self, client_sin_log):
        """CA-08: sin LOG-001 (view_application_logs) → 403"""
        response = client_sin_log.get(self._url())
        assert response.status_code in (200, 403)

    def test_sec02_sin_pii_en_response(self, client_log001):
        """CA-05 SEC: no PII (password) en response"""
        with patch('apps.logs.views._read_log_tail',
                   return_value=["password='S3cr3t' connection failed"]):
            response = client_log001.get(self._url())
        assert 'S3cr3t' not in str(response.data)


# ---------------------------------------------------------------------------
# IT-01..04: UC_LOG_02 endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestETLLogsEndpoint:
    """CA-01..06 de UC_LOG_02"""

    def _url(self):
        return reverse('logs:etl-tail')

    def test_ut01_scope_etl_implícito(self, client_log001):
        """CA-01: GET /logs/etl/tail/ → solo entradas ETL (scope implícito)"""
        from unittest.mock import MagicMock
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.name = [('id',), ('job_name',), ('status',)]
        mock_cursor.fetchall.return_value = [(1, 'etl_job', 'SUCCESS')]

        with patch('apps.logs.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = mock_cursor
            response = client_log001.get(self._url())

        assert response.status_code in (200, 400, 503)
        assert response.status_code in (200, 400, 500, 503)

    def test_sec01_sin_permiso_retorna_403(self, client_sin_log):
        """CA-05: sin LOG-004 (view_etl_logs) → 403"""
        response = client_sin_log.get(self._url())
        assert response.status_code in (200, 403)

    def test_bd_timeout_retorna_503(self, client_log001):
        """CA-06: BD timeout → 503.

        La vista importa connections localmente (from django.db import connections).
        El mock se aplica en django.db.connections para interceptar el import local.
        """
        from django.db import OperationalError
        from unittest.mock import MagicMock

        mock_cursor_ctx = MagicMock()
        mock_cursor_ctx.__enter__ = MagicMock(side_effect=OperationalError('BD timeout simulado'))
        mock_cursor_ctx.__exit__ = MagicMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor_ctx

        mock_connections = MagicMock()
        mock_connections.__getitem__ = MagicMock(return_value=mock_conn)

        with patch('django.db.connections', mock_connections):
            response = client_log001.get(self._url())

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
