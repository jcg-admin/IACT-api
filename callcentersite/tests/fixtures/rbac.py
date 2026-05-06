"""
Fixtures RBAC (funciones, asignaciones).
Adaptado al modelo real: UserPermission (no UserFunctionAssignment).
"""
import pytest
from apps.access.models import Function, UserPermission


@pytest.fixture
def func_factory(db):
    """Factory para crear funciones bajo demanda."""
    def _create(code, module='MOD_DEFAULT', name='Test Function',
                description='Test Description'):
        from apps.access.models import Module
        mod, _ = Module.objects.get_or_create(
            code=module,
            defaults={'name': module, 'description': module},
        )
        return Function.objects.create(
            code=code,
            module=mod,
            name=name,
            description=description,
        )
    return _create


@pytest.fixture
def function_create_user(func_factory):
    """Funcion para crear usuarios."""
    return func_factory(
        code='create_user',
        module='MOD_USERS',
        name='Crear Usuario',
        description='Permite crear nuevos usuarios',
    )


@pytest.fixture
def function_delete_user(func_factory):
    """Funcion para eliminar usuarios."""
    return func_factory(
        code='delete_user',
        module='MOD_USERS',
        name='Eliminar Usuario',
        description='Permite eliminar usuarios',
    )


@pytest.fixture
def user_with_function(db, sample_user, function_create_user):
    """Usuario con funcion asignada via UserPermission."""
    return UserPermission.objects.create(
        user=sample_user,
        function=function_create_user,
    )
