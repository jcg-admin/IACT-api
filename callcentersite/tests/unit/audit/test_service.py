"""Tests para AuditLogService."""
import pytest
from django.contrib.auth import get_user_model
from apps.audit.services import AuditLogService
from apps.audit.models import AuditLog

User = get_user_model()


@pytest.mark.django_db
class TestAuditLogService:
    """Tests para AuditLogService."""
    
    def test_log_create(self):
        """Test registrar creación."""
        user = User.objects.create_user(username='test')
        
        log = AuditLogService.log_create(
            user=user,
            resource_type='Report',
            resource_id=123,
            details={'name': 'Test Report'}
        )
        
        assert log.action == 'CREATE'
        assert log.resource == 'Report:123'
        assert log.result == 'SUCCESS'
        assert log.user == user
    
    def test_log_update(self):
        """Test registrar actualización."""
        user = User.objects.create_user(username='test')
        
        log = AuditLogService.log_update(
            user=user,
            resource_type='User',
            resource_id=1
        )
        
        assert log.action == 'UPDATE'
        assert log.resource == 'User:1'
    
    def test_log_delete(self):
        """Test registrar eliminación."""
        user = User.objects.create_user(username='test')
        
        log = AuditLogService.log_delete(
            user=user,
            resource_type='Report',
            resource_id=456
        )
        
        assert log.action == 'DELETE'
        assert log.resource == 'Report:456'
    
    def test_log_access_denied(self):
        """Test registrar acceso denegado."""
        user = User.objects.create_user(username='test')
        
        log = AuditLogService.log_access_denied(
            user=user,
            resource='Report:789',
            reason='No permission'
        )
        
        assert log.action == 'ACCESS_DENIED'
        assert log.result == 'FAILURE'
        assert log.details == {'reason': 'No permission'}
    
    def test_log_immutable(self):
        """Test que logs son inmutables."""
        user = User.objects.create_user(username='test')
        log = AuditLogService.log_create(user=user, resource_type='Test', resource_id=1)
        
        # Intentar modificar debe fallar
        log.action = 'MODIFIED'
        with pytest.raises(PermissionError):
            log.save()
    
    def test_log_no_delete(self):
        """Test que logs no se pueden eliminar."""
        user = User.objects.create_user(username='test')
        log = AuditLogService.log_create(user=user, resource_type='Test', resource_id=1)
        
        with pytest.raises(PermissionError):
            log.delete()
