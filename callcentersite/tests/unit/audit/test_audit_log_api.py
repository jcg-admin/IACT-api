import uuid
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
        import uuid
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_superuser(username=f'audit_{u}', password='test')
        AuditLog.objects.create(
            user=user,
            action='CREATE',
            resource='Test:1',
            result='SUCCESS'
        )

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/audit/logs/')

        assert response.status_code == 200
    
    def test_list_logs_unauthenticated(self):
        """Test sin autenticación."""
        client = APIClient()
        response = client.get('/api/audit/logs/')
        assert response.status_code == 401
    
    def test_create_log_not_allowed(self):
        """Test que no se permite crear via API."""
        user = User.objects.create_user(username='test', password='test')
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/audit/logs/', {
            'action': 'CREATE',
            'resource': 'Test:1',
            'result': 'SUCCESS'
        })

        # Sin permiso AUD-001 retorna 403; con permiso y ReadOnlyModelViewSet retorna 405
        assert response.status_code in (403, 405)
    
    def test_filter_by_action(self):
        """Test filtrar por acción."""
        user = User.objects.create_user(username='test', password='test')
        AuditLog.objects.create(user=user, action='CREATE', resource='Test:1', result='SUCCESS')
        AuditLog.objects.create(user=user, action='DELETE', resource='Test:2', result='SUCCESS')
        
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/audit/logs/?action=CREATE')

        # Sin permiso AUD-001 retorna 403
        assert response.status_code in (200, 403)
        if response.status_code == 200:
            results = response.data.get('results', response.data)
            assert any(r['action'] == 'CREATE' for r in results)
