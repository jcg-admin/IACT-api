"""
Fixtures RBAC (funciones, asignaciones).
Basado en el archivo rbac.py original, integrado con conftest.py.
"""
import pytest
from apps.access.models import Function, UserFunctionAssignment

@pytest.fixture
def func_factory(db):
    """
    Factory para crear funciones bajo demanda.
    Permite a los tests crear variaciones de funciones sin repetir código.
    """
    def _create(code, module='MOD_DEFAULT', name='Test Function', description='Test Description'):
        return Function.objects.create(
            code=code,
            module=module,
            name=name,
            description=description
        )
    return _create

@pytest.fixture
def function_create_user(func_factory):
    """Función para crear usuarios (usa la factory interna)."""
    return func_factory(
        code='create_user',
        module='MOD_USERS',
        name='Crear Usuario',
        description='Permite crear nuevos usuarios'
    )

@pytest.fixture
def function_delete_user(func_factory):
    """Función para eliminar usuarios."""
    return func_factory(
        code='delete_user',
        module='MOD_USERS',
        name='Eliminar Usuario',
        description='Permite eliminar usuarios'
    )

@pytest.fixture
def user_with_function(db, sample_user, sample_admin, function_create_user):
    """
    Usuario con función asignada.
    INTEGRACIÓN: Cambiado 'basic_user' por 'sample_user' para que coincida con conftest.py.
    Añadido 'assigned_by' usando 'sample_admin'.
    """
    return UserFunctionAssignment.objects.create(
        user=sample_user,
        function=function_create_user,
        assigned_by=sample_admin,  # Campo requerido en tu modelo
        reason='Asignación inicial para pruebas'
    )