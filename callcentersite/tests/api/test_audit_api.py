"""
Tests API centralizados para Audit (Logs).

Tests de integración para endpoints de auditoría.
"""
import pytest
from apps.audit.models import AuditLog
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAuditLogAPI:
    """Tests para /api/audit/logs/"""

    def test_list_logs_authenticated(self, admin_client, sample_user):
        """Test listar logs autenticado con permiso AUD-001 (superusuario)."""
        AuditLog.objects.create(
            user=sample_user,
            action='TEST',
            resource='Test:1',
            result='SUCCESS'
        )

        response = admin_client.get('/api/audit/logs/')
        assert response.status_code == 200

    def test_list_logs_unauthenticated(self, api_client):
        """Test sin autenticación."""
        response = api_client.get('/api/audit/logs/')
        assert response.status_code == 401

    def test_create_log_not_allowed(self, admin_client):
        """Test que no se permite crear via API (ReadOnlyModelViewSet)."""
        response = admin_client.post('/api/audit/logs/', {
            'action': 'CREATE',
            'resource': 'Test:1',
            'result': 'SUCCESS'
        })
        # ReadOnlyModelViewSet no permite POST
        assert response.status_code == 405
