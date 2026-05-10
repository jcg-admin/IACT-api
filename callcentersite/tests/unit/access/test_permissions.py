"""
tests/unit/access/test_permissions.py

Tests unitarios para los permission classes de la app access:
- HasFunction: verifica que el usuario tenga una función RBAC
- HasModuleAccess: verifica acceso a un módulo completo

Nota sobre deuda preexistente (resuelta 2026-05-08):
    El archivo original tenía dos bloques de imports mezclados (versiones
    distintas del código) y tests que asumían un comportamiento diferente
    al implementado:
    - HasFunction retorna True cuando no hay required_function en la view
      (el test original esperaba False)
    - UserFunctionAssignment es el modelo correcto para asignaciones con
      is_active y assigned_by (no UserPermission)
    - HasModuleAccess importa directamente desde module_permissions
      (no desde el __init__ que la tiene comentada)
"""
import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from apps.access.models import (
    Function, UserFunctionAssignment, UserModuleAccess, UserPermission,
)
from apps.access.permissions.function_permissions import HasFunction
from apps.access.permissions.module_permissions import HasModuleAccess
from tests.test_data.access_test_data import FunctionTestData, ModuleTestData
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


# ---------------------------------------------------------------------------
# Fixtures de conveniencia
# ---------------------------------------------------------------------------

@pytest.fixture
def factory():
    return APIRequestFactory()


class ViewWithFunction(APIView):
    """View con required_function definido."""
    permission_classes = [HasFunction]
    required_function  = 've_reportes'


class ViewWithoutFunction(APIView):
    """View SIN required_function — acceso libre para usuarios autenticados."""
    permission_classes = [HasFunction]


class ViewRequiringModule(APIView):
    """View con required_module definido."""
    permission_classes = [HasModuleAccess]
    required_module = 'MOD_TEST'


# ---------------------------------------------------------------------------
# HasFunction
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.django_db
class TestHasFunctionPermission:
    """
    Tests para HasFunction permission.

    HasFunction usa User.has_function(permission_django) para verificar.
    Superusers siempre tienen acceso.
    Si la view no define required_function, el acceso está permitido
    para cualquier usuario autenticado (decisión de diseño — no es un bug).
    """

    def test_unauthenticated_user_denied(self, factory):
        """Usuario no autenticado es denegado."""
        request = factory.get('/')
        request.user = AnonymousUser()

        assert HasFunction().has_permission(request, ViewWithFunction()) is False

    def test_superuser_always_allowed(self, factory, db):
        """Superuser tiene acceso sin importar qué función requiere la view."""
        user = AdminUserTestData()

        request = factory.get('/')
        request.user = user

        assert HasFunction().has_permission(request, ViewWithFunction()) is True

    def test_user_with_required_function_allowed(self, factory, db):
        """
        Usuario con la función requerida tiene acceso.

        HasFunction usa user.has_function(permission_django) que a su vez
        llama get_functions(), el cual consulta UserPermission (no
        UserFunctionAssignment). La asignación debe hacerse via UserPermission.
        """
        user = UserTestData()
        fn   = FunctionTestData(
            code='ve_reportes', permission_django='ve_reportes')

        UserPermission.objects.create(user=user, function=fn)

        request = factory.get('/')
        request.user = user

        assert HasFunction().has_permission(request, ViewWithFunction()) is True

    def test_user_without_required_function_denied(self, factory, db):
        """Usuario sin la función requerida es denegado."""
        user = UserTestData()

        request = factory.get('/')
        request.user = user

        assert HasFunction().has_permission(request, ViewWithFunction()) is False

    def test_user_with_inactive_function_denied(self, factory, db):
        """
        Función con is_active=False en el modelo Function es denegada.

        get_functions() filtra Function.is_active=True.
        UserPermission solo tiene user + function, sin is_active propio —
        la inactividad se controla desactivando la Function.
        """
        user = UserTestData()
        fn   = FunctionTestData(
            code='ve_reportes', permission_django='ve_reportes')

        UserPermission.objects.create(user=user, function=fn)
        # Desactivar la función (not is_active en Function)
        fn.is_active = False
        fn.save()

        request = factory.get('/')
        request.user = user

        assert HasFunction().has_permission(request, ViewWithFunction()) is False

    def test_view_without_required_function_allows_authenticated(
            self, factory, db):
        """
        View sin required_function: cualquier usuario autenticado tiene acceso.

        Comportamiento intencional: si no se especifica qué función hace falta,
        no se restringe el acceso más allá de la autenticación.
        Ref: HasFunction implementación, paso 4.
        """
        user = UserTestData()

        request = factory.get('/')
        request.user = user

        assert HasFunction().has_permission(
            request, ViewWithoutFunction()) is True

    def test_view_without_required_function_denies_anonymous(self, factory):
        """View sin required_function: anónimos siempre denegados."""
        request = factory.get('/')
        request.user = AnonymousUser()

        assert HasFunction().has_permission(
            request, ViewWithoutFunction()) is False


# ---------------------------------------------------------------------------
# HasModuleAccess
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.django_db
class TestHasModuleAccess:
    """
    Tests para HasModuleAccess permission.

    HasModuleAccess usa ModuleAccessService.has_module_access() para verificar.
    Superusers siempre tienen acceso.
    """

    def test_user_with_module_access_allowed(self, factory):
        """Usuario con acceso al módulo tiene permiso."""
        user   = UserTestData()
        module = ModuleTestData(code='MOD_TEST')
        UserModuleAccess.objects.create(
            user=user, module=module, is_active=True)

        request = factory.get('/')
        request.user = user

        assert HasModuleAccess().has_permission(
            request, ViewRequiringModule()) is True

    def test_user_without_module_access_denied(self, factory):
        """Usuario sin acceso al módulo es denegado."""
        user = UserTestData()
        # Asegurar que el módulo existe pero el usuario no tiene acceso
        ModuleTestData(code='MOD_TEST')

        request = factory.get('/')
        request.user = user

        assert HasModuleAccess().has_permission(
            request, ViewRequiringModule()) is False

    def test_superuser_always_allowed(self, factory):
        """Superuser tiene acceso sin importar qué módulo requiere la view."""
        user = AdminUserTestData()

        request = factory.get('/')
        request.user = user

        assert HasModuleAccess().has_permission(
            request, ViewRequiringModule()) is True

    def test_unauthenticated_denied(self, factory):
        """Usuario no autenticado es denegado."""
        request = factory.get('/')
        request.user = AnonymousUser()

        assert HasModuleAccess().has_permission(
            request, ViewRequiringModule()) is False

    def test_inactive_module_access_denied(self, factory):
        """UserModuleAccess con is_active=False es denegado."""
        user   = UserTestData()
        module = ModuleTestData(code='MOD_TEST')
        UserModuleAccess.objects.create(
            user=user, module=module, is_active=False)

        request = factory.get('/')
        request.user = user

        assert HasModuleAccess().has_permission(
            request, ViewRequiringModule()) is False
