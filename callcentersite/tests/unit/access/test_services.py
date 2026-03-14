"""Tests para ModuleAccessService."""
import pytest
from django.contrib.auth import get_user_model
from apps.access.models import Module, UserModuleAccess
from apps.access.services import ModuleAccessService

User = get_user_model()


@pytest.mark.django_db
class TestModuleAccessService:
    """Tests para ModuleAccessService."""
    
    def test_has_module_access(self):
        """Test verificar acceso a módulo."""
        user = User.objects.create_user(username='test')
        module = Module.objects.create(code='MOD_Test', name='Test')
        
        assert ModuleAccessService.has_module_access(user, 'MOD_Test') is False
        
        UserModuleAccess.objects.create(user=user, module=module)
        assert ModuleAccessService.has_module_access(user, 'MOD_Test') is True
    
    def test_grant_module_access(self):
        """Test otorgar acceso."""
        user = User.objects.create_user(username='test')
        admin = User.objects.create_user(username='admin')
        Module.objects.create(code='MOD_Test', name='Test')
        
        access = ModuleAccessService.grant_module_access(
            user=user,
            module_code='MOD_Test',
            granted_by=admin,
            reason='Test'
        )
        
        assert access.is_active is True
        assert access.granted_by == admin
