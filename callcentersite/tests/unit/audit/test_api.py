"""Tests para API de AuditLog."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.audit.models import AuditLog

User = get_user_model()


@pytest.mark.django_db
class TestAuditLogAPI:
    """Tests para AuditLogViewSet."""
    
    def test_list_logs_authenticated(self):
        """Test listar logs autenticado."""
        user = User.objects.create_user(username='test', password='test')
        AuditLog.objects.create(
            user=user,
            action='CREATE',
            resource='Test:1',
            result='SUCCESS'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/v1/audit/logs/')
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
    
    def test_list_logs_unauthenticated(self):
        """Test sin autenticación."""
        client = APIClient()
        response = client.get('/api/v1/audit/logs/')
        assert response.status_code == 401
    
    def test_create_log_not_allowed(self):
        """Test que no se permite crear via API."""
        user = User.objects.create_user(username='test', password='test')
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.post('/api/v1/audit/logs/', {
            'action': 'CREATE',
            'resource': 'Test:1',
            'result': 'SUCCESS'
        })
        
        # ReadOnlyModelViewSet no permite POST
        assert response.status_code == 405
    
    def test_filter_by_action(self):
        """Test filtrar por acción."""
        user = User.objects.create_user(username='test', password='test')
        AuditLog.objects.create(user=user, action='CREATE', resource='Test:1', result='SUCCESS')
        AuditLog.objects.create(user=user, action='DELETE', resource='Test:2', result='SUCCESS')
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/v1/audit/logs/?action=CREATE')
        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['action'] == 'CREATE'
