import pytest
from django.contrib.auth.models import User, AnonymousUser
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

try:
    from apps.access.models import Function, UserFunctionAssignment
    from apps.access.permissions import HasFunction

except ImportError as _err:
    pytest.skip(
        f'Codigo no implementado: {_err}',
        allow_module_level=True,
    )
"""Tests para permissions de módulos."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

try:
    from apps.access.models import Module, UserModuleAccess
    from apps.access.permissions.module_permissions import HasModuleAccess

except ImportError as _err:
    pytest.skip(
        f'Codigo no implementado: {_err}',
        allow_module_level=True,
    )
User = get_user_model()


@pytest.mark.django_db
class TestHasModuleAccess:
    """Tests para HasModuleAccess permission."""
    
    def test_permission_with_access(self):
        """Test permiso con acceso."""
        user = User.objects.create_user(username='test')
        module = Module.objects.create(code='MOD_Test', name='Test')
        UserModuleAccess.objects.create(user=user, module=module)
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        
        class MockView:
            required_module = 'MOD_Test'
        
        permission = HasModuleAccess()
        assert permission.has_permission(request, MockView()) is True
    
    def test_permission_without_access(self):
        """Test permiso sin acceso."""
        user = User.objects.create_user(username='test')
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        
        class MockView:
            required_module = 'MOD_Test'
        
        permission = HasModuleAccess()
        assert permission.has_permission(request, MockView()) is False

class DummyView(APIView):
    """View dummy para tests."""
    permission_classes = [HasFunction]
    required_function = 've_reportes'


@pytest.mark.unit
@pytest.mark.django_db
class TestHasFunctionPermission:
    """Tests para permission HasFunction."""
    
    def test_unauthenticated_user_denied(self):
        """Usuario no autenticado es denegado."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()  # Usuario anonimo (no autenticado)
        
        view = DummyView()
        permission = HasFunction()
        
        assert permission.has_permission(request, view) is False
    
    def test_superuser_always_allowed(self):
        """Superuser siempre tiene permiso."""
        user = User.objects.create_user(
            username='admin',
            is_superuser=True
        )
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        
        view = DummyView()
        permission = HasFunction()
        
        assert permission.has_permission(request, view) is True
    
    def test_user_with_function_allowed(self):
        """Usuario con la funcion es permitido."""
        user = User.objects.create_user('testuser')
        admin = User.objects.create_user('admin')
        
        func = Function.objects.create(
            code='ve_reportes',
            module='MOD_Reports',
            name='Ver Reportes'
        )
        
        UserFunctionAssignment.objects.create(
            user=user,
            function=func,
            assigned_by=admin,
            reason='Test',
            is_active=True
        )
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        
        view = DummyView()
        permission = HasFunction()
        
        assert permission.has_permission(request, view) is True
    
    def test_user_without_function_denied(self):
        """Usuario sin la funcion es denegado."""
        user = User.objects.create_user('testuser')
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        
        view = DummyView()
        permission = HasFunction()
        
        assert permission.has_permission(request, view) is False
    
    def test_user_with_inactive_function_denied(self):
        """Usuario con funcion inactiva es denegado."""
        user = User.objects.create_user('testuser')
        admin = User.objects.create_user('admin')
        
        func = Function.objects.create(
            code='ve_reportes',
            module='MOD_Reports',
            name='Ver Reportes'
        )
        
        UserFunctionAssignment.objects.create(
            user=user,
            function=func,
            assigned_by=admin,
            reason='Test',
            is_active=False  # INACTIVA
        )
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        
        view = DummyView()
        permission = HasFunction()
        
        assert permission.has_permission(request, view) is False
    
    def test_view_without_required_function_denied(self):
        """View sin required_function definido deniega acceso."""
        user = User.objects.create_user('testuser')
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        
        # View sin required_function
        class ViewWithoutFunction(APIView):
            permission_classes = [HasFunction]
        
        view = ViewWithoutFunction()
        permission = HasFunction()
        
        assert permission.has_permission(request, view) is False
