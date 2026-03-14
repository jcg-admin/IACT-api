"""Tests para @audit_log decorator."""
import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from apps.audit.decorators import audit_log
from apps.audit.models import AuditLog

User = get_user_model()


@pytest.mark.django_db
class TestAuditLogDecorator:
    """Tests para @audit_log decorator."""
    
    def test_decorator_creates_log(self):
        """Test que decorator crea log."""
        user = User.objects.create_user(username='test')
        
        @audit_log(action='TEST', resource_type='TestResource')
        def test_view(request):
            return HttpResponse('OK')
        
        # Mock request
        class MockRequest:
            user = user
            method = 'POST'
            META = {}
        
        request = MockRequest()
        response = test_view(request)
        
        # Debe haber creado log
        assert AuditLog.objects.count() == 1
        log = AuditLog.objects.first()
        assert log.action == 'TEST'
        assert log.resource == 'TestResource'
    
    def test_decorator_infers_action(self):
        """Test que decorator infiere acción de método HTTP."""
        user = User.objects.create_user(username='test')
        
        @audit_log(resource_type='Resource')
        def test_view(request):
            return HttpResponse('OK')
        
        class MockRequest:
            user = user
            method = 'POST'
            META = {}
        
        request = MockRequest()
        test_view(request)
        
        log = AuditLog.objects.first()
        assert log.action == 'CREATE'  # Inferido de POST
