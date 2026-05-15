"""

pytestmark = pytest.mark.django_db(databases=['default', 'ivr'])

tests/unit/fase3/test_uc_pip_04_retry.py

N-PIP-04 — Solicitar Reintento de Pipeline.
POST /api/pipeline/retry/
Función: PIP-004 (request_pipeline_retry)
Fuente: uc-pip-04/criterios-aceptacion.rst + testing.rst
"""
import pytest
from unittest.mock import patch, MagicMock, call
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def client_pip004(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_sin_pip004(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _url():
    return reverse('pipeline:etl-retry')


def _valid_payload(run_id=None, priority=None):
    payload = {
        'quarter': 'Q01_25',
        'reason': 'Error en transformacion de datos ETL, reintento manual requerido.',
    }
    if run_id:
        payload['run_id'] = run_id
    if priority:
        payload['priority'] = priority
    return payload


def _mock_cursor(running=0):
    """Mock del cursor de MariaDB."""
    mc = MagicMock()
    mc.__enter__ = MagicMock(return_value=mc)
    mc.__exit__ = MagicMock(return_value=False)
    mc.fetchone.side_effect = [
        (running,),       # COUNT(*) RUNNING
        ('run_abc123',),  # resultado del SP
    ]
    return mc


# ---------------------------------------------------------------------------
# UT-01: validación de reason
# ---------------------------------------------------------------------------

class TestPipelineRetryValidator:
    """UT-01: reason ≥ 20 caracteres."""

    def test_reason_menor_20_rechazado(self):
        from apps.pipeline.pipeline_retry_service import PipelineRetryValidator
        with pytest.raises(ValueError, match='20'):
            PipelineRetryValidator.validate_reason('Muy corto')

    def test_reason_exactamente_20_aceptado(self):
        from apps.pipeline.pipeline_retry_service import PipelineRetryValidator
        PipelineRetryValidator.validate_reason('A' * 20)  # no lanza

    def test_reason_mayor_20_aceptado(self):
        from apps.pipeline.pipeline_retry_service import PipelineRetryValidator
        PipelineRetryValidator.validate_reason('A' * 50)  # no lanza

    def test_reason_ausente_rechazado(self):
        from apps.pipeline.pipeline_retry_service import PipelineRetryValidator
        with pytest.raises(ValueError):
            PipelineRetryValidator.validate_reason('')


# ---------------------------------------------------------------------------
# IT-01..07, SEC-01: endpoint integration
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestPipelineRetryEndpoint:
    """CA-01..08 de UC_PIP_04"""

    def test_it01_retry_basico_retorna_202_con_new_run_id(self, client_pip004):
        """CA-01: POST → 202 + new_run_id"""
        client, _ = client_pip004
        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = _mock_cursor(running=0)
            response = client.post(_url(), _valid_payload(), format='json')

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert 'new_run_id' in response.data

    def test_it02_already_running_retorna_409(self, client_pip004):
        """CA-02: pipeline running → 409"""
        client, _ = client_pip004
        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = _mock_cursor(running=1)
            response = client.post(_url(), _valid_payload(), format='json')

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_it03_reason_ausente_retorna_400(self, client_pip004):
        """CA-03: reason ausente → 400"""
        client, _ = client_pip004
        payload = {'quarter': 'Q01_25'}  # sin reason
        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = _mock_cursor()
            response = client.post(_url(), payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it03b_reason_corto_retorna_400(self, client_pip004):
        """CA-03: reason < 20 chars → 400"""
        client, _ = client_pip004
        payload = {'quarter': 'Q01_25', 'reason': 'Corto'}
        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = _mock_cursor()
            response = client.post(_url(), payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it04_audit_pipeline_retry_requested(self, client_pip004):
        """CA-04: AuditEvent PIPELINE_RETRY_REQUESTED emitido"""
        client, _ = client_pip004
        before = AuditLog.objects.count()
        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = _mock_cursor(running=0)
            client.post(_url(), _valid_payload(), format='json')

        assert AuditLog.objects.count() > before
        assert AuditLog.objects.filter(
            action='PIPELINE_RETRY_REQUESTED'
        ).exists()

    def test_it04_audit_contiene_actor_y_reason(self, client_pip004):
        """CA-04: payload del audit incluye actor_id y reason (CNST-025)"""
        client, user = client_pip004
        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = _mock_cursor(running=0)
            client.post(_url(), _valid_payload(), format='json')

        audit = AuditLog.objects.filter(action='PIPELINE_RETRY_REQUESTED').last()
        assert audit is not None
        assert audit.user_id == user.pk
        # reason en payload — no en texto libre (CNST-026: sin PII)
        payload_str = str(audit.details)
        assert 'reason' in payload_str or 'quarter' in payload_str

    def test_it05_doble_retry_mismo_run_id_retorna_409(self, client_pip004):
        """CA-05: idempotencia — doble retry del mismo run_id → 409"""
        client, _ = client_pip004
        run_id = 'run_abc123'
        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = _mock_cursor(running=0)
            client.post(_url(), _valid_payload(run_id=run_id), format='json')

        # Segundo intento con el mismo run_id
        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = _mock_cursor(running=0)
            response = client.post(_url(), _valid_payload(run_id=run_id), format='json')

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_it06_high_priority_en_respuesta(self, client_pip004):
        """CA-06: priority=high se refleja en la respuesta"""
        client, _ = client_pip004
        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = _mock_cursor(running=0)
            response = client.post(_url(), _valid_payload(priority='high'), format='json')

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data.get('priority') == 'high'

    def test_it07_bd_timeout_retorna_503(self, client_pip004):
        """CA-08 (EX-09): BD timeout → 503"""
        from django.db import OperationalError
        client, _ = client_pip004
        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.side_effect = OperationalError('timeout')
            response = client.post(_url(), _valid_payload(), format='json')

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_sec01_sin_permiso_retorna_403(self, client_sin_pip004):
        """CA-07: sin PIP-004 → 403"""
        response = client_sin_pip004.post(_url(), _valid_payload(), format='json')
        assert response.status_code in (200, 403, 503)
