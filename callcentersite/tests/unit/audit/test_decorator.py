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
            def __init__(self, u):
                self.user = u
                self.method = 'POST'
                self.META = {}

        request = MockRequest(user)
        response = test_view(request)

        # Verifica que se creó al menos un log (puede haber logs previos de otros tests)
        logs = AuditLog.objects.filter(action='TEST', resource='TestResource')
        assert logs.exists()
    
    def test_decorator_infers_action(self):
        """Test que decorator infiere acción de método HTTP."""
        user = User.objects.create_user(username='test')
        
        @audit_log(resource_type='Resource')
        def test_view(request):
            return HttpResponse('OK')
        
        class MockRequest:
            def __init__(self, u):
                self.user = u
                self.method = 'POST'
                self.META = {}

        request = MockRequest(user)
        test_view(request)

        logs = AuditLog.objects.filter(user=user)
        assert logs.exists()
        log = logs.first()
        assert log.action == 'CREATE'  # Inferido de POST
