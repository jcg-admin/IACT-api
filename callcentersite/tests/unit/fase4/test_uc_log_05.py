"""
tests/unit/fase4/test_uc_log_05.py

UC_LOG_05 — Ver Logs de Infraestructura.
GET /api/logs/infra/
Función: LOG-005 (view_infrastructure_logs)
Fuente: uc-log-05/criterios-aceptacion.rst
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def client_log005(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def client_sin_log005(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _url():
    return reverse('logs:infra-tail')


class TestLogRangeValidatorInfra:
    """UT-01: range > 24h rechazado (mismo que LOG-01)."""

    def test_range_mayor_24h_rechazado(self):
        from apps.logs.log_validators import LogRangeValidator
        now = datetime.now(timezone.utc)
        with pytest.raises(Exception, match='24'):
            LogRangeValidator.validate(now - timedelta(hours=25), now)


@pytest.mark.django_db
class TestInfraLogsEndpoint:

    def test_it01_list_retorna_estructura(self, client_log005):
        """CA-01: GET /logs/infra/ → 200 con {source, entries}."""
        with patch('apps.logs.views.connections') as mock_conn:
            mc = MagicMock()
            mc.__enter__ = MagicMock(return_value=mc)
            mc.__exit__  = MagicMock(return_value=False)
            mc.description = [('id',), ('host',), ('message',), ('level',)]
            mc.fetchall.return_value = [(1, 'server01', 'OK', 'INFO')]
            mock_conn.__getitem__.return_value.cursor.return_value = mc
            response = client_log005.get(_url())

        assert response.status_code == status.HTTP_200_OK
        assert 'source' in response.data
        assert 'entries' in response.data

    def test_it02_filter_host(self, client_log005):
        """CA-02: ?host=server01 → sólo ese host."""
        with patch('apps.logs.views.connections') as mock_conn:
            mc = MagicMock()
            mc.__enter__ = MagicMock(return_value=mc)
            mc.__exit__  = MagicMock(return_value=False)
            mc.description = [('id',), ('host',), ('message',)]
            mc.fetchall.return_value = [(1, 'server01', 'OK')]
            mock_conn.__getitem__.return_value.cursor.return_value = mc
            response = client_log005.get(_url(), {'host': 'server01'})

        assert response.status_code == status.HTTP_200_OK

    def test_it04_bd_timeout_retorna_503(self, client_log005):
        """CA-06: BD timeout → 503."""
        from django.db import OperationalError
        with patch('apps.logs.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.side_effect = OperationalError('timeout')
            response = client_log005.get(_url())
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_sec_sin_permiso_retorna_403(self, client_sin_log005):
        """CA-05: sin LOG-005 → 403."""
        response = client_sin_log005.get(_url())
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_required_function_es_log005(self):
        """InfraLogView.required_function debe ser LOG-005, no LOG-001."""
        from apps.logs.views import InfraLogView
        assert InfraLogView.required_function == 'LOG-005'
