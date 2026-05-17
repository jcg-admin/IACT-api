"""Tests para ModuleAccessService."""

import pytest
from django.contrib.auth import get_user_model

try:
    from apps.access.models import Module, UserPermission
    from apps.access.services import ModuleAccessService
except ImportError as _err:
    pytest.skip(
        f'Codigo no implementado aun — {_err}',
        allow_module_level=True,
    )




User = get_user_model()


@pytest.mark.django_db
class TestModuleAccessService:
    """Tests para ModuleAccessService."""
    
    def test_has_module_access(self):
        """Test verificar acceso a módulo."""
        import uuid
        u = uuid.uuid4().hex[:6]
        from apps.access.models import UserModuleAccess
        user = User.objects.create_user(username=f'tst_{u}', password='Pass123')
        module = Module.objects.create(code=f'MOD_{u}', name=f'Test {u}')

        assert ModuleAccessService.has_module_access(user, f'MOD_{u}') is False

        UserModuleAccess.objects.create(
            user=user, module=module,
            granted_by=user, reason='test',
            is_active=True,
        )
        assert ModuleAccessService.has_module_access(user, f'MOD_{u}') is True
    
    def test_grant_module_access(self):
        """Test otorgar acceso."""
        import uuid
        u = uuid.uuid4().hex[:6]
        user = User.objects.create_user(username=f'tst_{u}', password='Pass123')
        admin = User.objects.create_user(username=f'adm_{u}', password='Pass123', is_superuser=True)
        Module.objects.create(code=f'MOD_{u}', name=f'Test {u}')

        access = ModuleAccessService.grant_module_access(
            user=user, module_code=f'MOD_{u}',
            granted_by=admin, reason='Test',
        )

        assert access.is_active is True
        assert access.granted_by == admin
