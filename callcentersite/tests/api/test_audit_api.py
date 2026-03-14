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
    """Tests para /api/v1/audit/logs/"""
    
    def test_list_logs_authenticated(self, authenticated_client, sample_user):
        """Test listar logs autenticado."""
        # Crear log de prueba
        AuditLog.objects.create(
            user=sample_user,
            action='TEST',
            resource='Test:1',
            result='SUCCESS'
        )
        
        response = authenticated_client.get('/api/v1/audit/logs/')
        assert response.status_code == 200
    
    def test_list_logs_unauthenticated(self, api_client):
        """Test sin autenticación."""
        response = api_client.get('/api/v1/audit/logs/')
        assert response.status_code == 401
    
    def test_create_log_not_allowed(self, authenticated_client):
        """Test que no se permite crear via API."""
        response = authenticated_client.post('/api/v1/audit/logs/', {
            'action': 'CREATE',
            'resource': 'Test:1',
            'result': 'SUCCESS'
        })
        # ReadOnlyModelViewSet no permite POST
        assert response.status_code == 405
