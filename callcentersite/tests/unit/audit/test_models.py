import pytest
from django.contrib.auth.models import User
from apps.audit.models import AuditLog


@pytest.mark.unit
@pytest.mark.django_db
class TestAuditLog:
    """Tests auditoria inmutable (CNST-009)."""
    
    def test_create_audit_log(self):
        """Crear log de auditoria."""
        user = User.objects.create_user('testuser')
        
        log = AuditLog.objects.create(
            user=user,
            action='LOGIN',
            resource='auth',
            result='SUCCESS',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
        )
        
        assert log.id is not None
        assert log.action == 'LOGIN'
        assert log.result == 'SUCCESS'
        assert log.ip_address == '192.168.1.1'
    
    def test_audit_log_str(self):
        """__str__ muestra timestamp, user y action."""
        user = User.objects.create_user('testuser')
        
        log = AuditLog.objects.create(
            user=user,
            action='CREATE_USER',
            resource='users',
            result='SUCCESS'
        )
        
        log_str = str(log)
        assert 'testuser' in log_str
        assert 'CREATE_USER' in log_str
    
    def test_audit_log_immutable_update(self):
        """AuditLog NO permite update (CNST-009)."""
        user = User.objects.create_user('testuser')
        log = AuditLog.objects.create(
            user=user,
            action='TEST',
            resource='test',
            result='SUCCESS'
        )
        
        # Intentar modificar
        log.action = 'MODIFIED'
        
        # Debe lanzar PermissionError
        with pytest.raises(PermissionError) as exc_info:
            log.save()
        
        assert 'CNST-009' in str(exc_info.value)
        assert 'inmutable' in str(exc_info.value).lower()
    
    def test_audit_log_immutable_delete(self):
        """AuditLog NO permite delete (CNST-009)."""
        user = User.objects.create_user('testuser')
        log = AuditLog.objects.create(
            user=user,
            action='TEST',
            resource='test',
            result='SUCCESS'
        )
        
        # Debe lanzar PermissionError
        with pytest.raises(PermissionError) as exc_info:
            log.delete()
        
        assert 'CNST-009' in str(exc_info.value)
    
    def test_audit_log_record_helper(self):
        """Helper record() para crear logs facilmente."""
        user = User.objects.create_user('testuser')
        
        log = AuditLog.record(
            user=user,
            action='CREATE_USER',
            resource='users',
            result='SUCCESS',
            ip_address='10.0.0.1',
            details={'username': 'newuser'}
        )
        
        assert log.id is not None
        assert log.action == 'CREATE_USER'
        assert log.details['username'] == 'newuser'
    
    def test_audit_log_ordering(self):
        """Logs ordenados por timestamp descendente (mas reciente primero)."""
        user = User.objects.create_user('testuser')
        
        log1 = AuditLog.objects.create(
            user=user, action='ACTION1', resource='r1', result='SUCCESS'
        )
        log2 = AuditLog.objects.create(
            user=user, action='ACTION2', resource='r2', result='SUCCESS'
        )
        log3 = AuditLog.objects.create(
            user=user, action='ACTION3', resource='r3', result='SUCCESS'
        )
        
        logs = list(AuditLog.objects.all())
        
        # Mas reciente primero
        assert logs[0].id == log3.id
        assert logs[1].id == log2.id
        assert logs[2].id == log1.id
    
    def test_audit_log_with_details_json(self):
        """AuditLog puede almacenar detalles en JSON."""
        user = User.objects.create_user('testuser')
        
        details = {
            'field': 'username',
            'old_value': 'olduser',
            'new_value': 'newuser',
            'metadata': {'ip': '192.168.1.1'}
        }
        
        log = AuditLog.objects.create(
            user=user,
            action='UPDATE_USER',
            resource='users',
            result='SUCCESS',
            details=details
        )
        
        assert log.details['field'] == 'username'
        assert log.details['old_value'] == 'olduser'
        assert log.details['metadata']['ip'] == '192.168.1.1'
