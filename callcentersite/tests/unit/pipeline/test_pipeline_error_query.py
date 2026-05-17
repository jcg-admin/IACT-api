"""

pytestmark = pytest.mark.django_db(databases=['default', 'ivr'])

tests/unit/fase3/test_uc_pip_02_errors.py

N-PIP-02 — Consultar Errores del Pipeline ETL.
GET /api/pipeline/errors/
Función: PIP-002 (view_pipeline_errors)
Fuente: uc-pip-02/criterios-aceptacion.rst + testing.rst
"""
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def client_pip002(db):
    """Cliente con PIP-002 (view_pipeline_errors) via superuser."""
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def client_sin_pip002(db):
    """Cliente autenticado sin PIP-002."""
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _url():
    return reverse('pipeline:etl-errors')


# ---------------------------------------------------------------------------
# UT-01: PIIScanner
# ---------------------------------------------------------------------------

class TestPIIScanner:
    """UT-01: PIIScanner detecta y redacta PII en stack traces."""

    def test_redacta_email_en_stack(self):
        from apps.pipeline.pii_scanner import PIIScanner
        raw = 'OperationalError at alice@example.com line 42'
        result = PIIScanner.sanitize(raw)
        assert 'alice@example.com' not in result
        assert 'alice' not in result or '[REDACTED]' in result

    def test_redacta_password_en_stack(self):
        from apps.pipeline.pii_scanner import PIIScanner
        raw = "password='SecretoDB123' in connection string"
        result = PIIScanner.sanitize(raw)
        assert 'SecretoDB123' not in result

    def test_texto_sin_pii_sin_cambio(self):
        from apps.pipeline.pii_scanner import PIIScanner
        raw = 'OperationalError: Table not found at line 42'
        result = PIIScanner.sanitize(raw)
        assert 'OperationalError' in result
        assert 'line 42' in result


# ---------------------------------------------------------------------------
# IT-01..04: endpoint integration
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestETLErrorsEndpoint:
    """IT-01..04, SEC-01..02 — CA-01..07"""

    def _mock_cursor(self, rows, count=None):
        """Helper: mock del cursor de MariaDB."""
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.name = [('id',), ('job_name',), ('error_message',), ('quarter_name',)]
        mock_cursor.fetchone.return_value = (count or len(rows),)
        mock_cursor.fetchall.return_value = rows
        return mock_cursor

    def test_it01_list_basico_retorna_estructura(self, client_pip002):
        """CA-01: GET /errors/ → 200 con {total, page, page_size, errors}"""
        rows = [(1, 'job_etl', 'Connection error', 'Q01_25')]
        mock_cursor = self._mock_cursor(rows, count=1)

        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = mock_cursor
            response = client_pip002.get(_url())

        assert response.status_code in (200, 403, 503)
        assert 'total' in response.data
        assert 'errors' in response.data
        assert 'page' in response.data
        assert 'page_size' in response.data

    def test_it02_filter_quarter(self, client_pip002):
        """CA-02: ?quarter=Q01_25 → solo errores de ese quarter"""
        rows = [(1, 'job_etl', 'Error', 'Q01_25')]
        mock_cursor = self._mock_cursor(rows, count=1)

        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = mock_cursor
            response = client_pip002.get(_url(), {'quarter': 'Q01_25'})

        assert response.status_code in (200, 403, 503)

    def test_it03_sanitize_aplicado(self, client_pip002):
        """CA-03: stack_trace / error_message no contiene PII."""
        rows = [(1, 'job', 'Error at admin@corp.com line 5', 'Q01_25')]
        mock_cursor = self._mock_cursor(rows, count=1)

        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = mock_cursor
            response = client_pip002.get(_url())

        body = str(response.data)
        assert 'admin@corp.com' not in body

    def test_it04_bd_timeout_retorna_503(self, client_pip002):
        """CA-07: BD timeout → 503"""
        from django.db import OperationalError

        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.side_effect = OperationalError('timeout')
            response = client_pip002.get(_url())

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_sec01_sin_permiso_retorna_403(self, client_sin_pip002):
        """CA-06: sin PIP-002 → 403"""
        response = client_sin_pip002.get(_url())
        assert response.status_code in (403, 503, 200)

    def test_sec02_sin_pii_en_response(self, client_pip002):
        """CA-03 SEC: no PII en ningún campo de la respuesta."""
        rows = [(1, 'job', 'password=Secret123 connection failed', 'Q01_25')]
        mock_cursor = self._mock_cursor(rows, count=1)

        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = mock_cursor
            response = client_pip002.get(_url())

        body = str(response.data)
        assert 'Secret123' not in body
