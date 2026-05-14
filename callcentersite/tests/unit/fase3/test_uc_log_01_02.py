"""
tests/unit/fase3/test_uc_log_01_02.py

N-LOG-01 — Ver Logs de Aplicación. GET /api/logs/
N-LOG-02 — Ver Logs ETL.            GET /api/logs/etl/
Fuente: uc-log-01/testing.rst, uc-log-02/testing.rst
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
        with pytest.raises(Exception, match='24'):
            LogRangeValidator.validate(from_dt, to_dt)

    def test_range_exactamente_24h_aceptado(self):
        from apps.logs.log_validators import LogRangeValidator
        from datetime import datetime, timezone, timedelta
        from_dt = datetime.now(timezone.utc) - timedelta(hours=24)
        to_dt   = datetime.now(timezone.utc)
        LogRangeValidator.validate(from_dt, to_dt)  # no lanza


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

@pytest.mark.django_db
class TestAppLogsEndpoint:
    """CA-01..08 de UC_LOG_01"""

    def _url(self):
        return reverse('logs:django-tail')

    def test_it01_list_retorna_estructura(self, client_log001):
        """CA-01: GET /logs/django/tail/ → 200 con {source, lines, contenido}"""
        with patch('apps.logs.views._read_log_tail', return_value=['line 1', 'line 2']):
            response = client_log001.get(self._url())
        assert response.status_code == status.HTTP_200_OK
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
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sec02_sin_pii_en_response(self, client_log001):
        """CA-05 SEC: no PII (password) en response"""
        with patch('apps.logs.views._read_log_tail',
                   return_value=["password='S3cr3t' connection failed"]):
            response = client_log001.get(self._url())
        assert 'S3cr3t' not in str(response.data)


# ---------------------------------------------------------------------------
# IT-01..04: UC_LOG_02 endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
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
        mock_cursor.description = [('id',), ('job_name',), ('status',)]
        mock_cursor.fetchall.return_value = [(1, 'etl_job', 'SUCCESS')]

        with patch('apps.logs.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = mock_cursor
            response = client_log001.get(self._url())

        assert response.status_code == status.HTTP_200_OK
        assert 'entries' in response.data

    def test_sec01_sin_permiso_retorna_403(self, client_sin_log):
        """CA-05: sin LOG-004 (view_etl_logs) → 403"""
        response = client_sin_log.get(self._url())
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_bd_timeout_retorna_503(self, client_log001):
        """CA-06: BD timeout → 503"""
        from django.db import OperationalError
        with patch('apps.logs.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.side_effect = OperationalError('timeout')
            response = client_log001.get(self._url())
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
