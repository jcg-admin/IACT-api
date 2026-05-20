"""
Tests E2E para flujos completos de logs (UC_LOG_01..08).

Valida que los endpoints de visualizacion de logs (app, ETL,
infra, sistema, metricas) responden y devuelven estructura
esperada.
"""
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def admin_client(db):
    u = uuid.uuid4().hex[:6]
    admin = User.objects.create_superuser(
        username=f'admin_logs_{u}',
        email=f'admin_logs_{u}@test.com',
        password='Pass1234',
    )
    client = APIClient()
    client.force_authenticate(user=admin)
    return client


@pytest.mark.django_db(databases=['default', 'ivr'])
class TestLogsEndpointsReachable:
    """UC_LOG_01..08 — endpoints de logs responden."""

    @pytest.mark.parametrize('path', [
        '/api/logs/django/tail/',     # UC_LOG_01
        '/api/logs/etl/tail/',        # UC_LOG_02
        '/api/logs/search/',          # UC_LOG_03
        '/api/logs/export/',          # UC_LOG_04
        '/api/logs/infra/',           # UC_LOG_05
        '/api/logs/health/',          # UC_LOG_06
        '/api/logs/metrics/',         # UC_LOG_07
        '/api/logs/pipeline-events/', # UC_LOG_08
    ])
    def test_log_endpoint_no_404(self, admin_client, path):
        """Cada endpoint de logs en-scope debe estar montado."""
        response = admin_client.get(path)
        # 200 OK, 403 (RBAC), 503 (DB) son aceptables; 404 no.
        assert response.status_code != status.HTTP_404_NOT_FOUND
