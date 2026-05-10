"""
tests/unit/access/test_views.py

Tests unitarios para MyModulesView.

Nota sobre deuda preexistente (resuelta 2026-05-08):
    El test original tenía dos problemas:
    1. URL incorrecta: /api/v1/access/my-modules/ → la URL real es /api/access/my-modules/
    2. Usaba UserPermission(user=user, module=module) para otorgar acceso a módulos,
       pero UserPermission vincula users con functions (RBAC granular), no con modules.
       El modelo correcto para acceso a módulos es UserModuleAccess.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.access.models import UserModuleAccess
from tests.test_data.access_test_data import ModuleTestData
from tests.test_data.user_test_data import UserTestData


@pytest.mark.unit
@pytest.mark.django_db
class TestMyModulesView:
    """Tests para GET /api/access/my-modules/"""

    def test_unauthenticated_returns_401(self):
        """Sin autenticación el endpoint retorna 401."""
        client = APIClient()
        url = reverse('access:my-modules')
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_gets_own_modules(self):
        """Usuario autenticado con acceso a un módulo lo ve en la respuesta."""
        user   = UserTestData()
        module = ModuleTestData()
        UserModuleAccess.objects.create(
            user=user, module=module, is_active=True)

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse('access:my-modules')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] >= 1

    def test_user_without_modules_gets_empty_list(self):
        """Usuario sin módulos asignados retorna total_count=0."""
        user = UserTestData()

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse('access:my-modules')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 0

    def test_response_has_required_keys(self):
        """La respuesta incluye modules, total_count y root_count."""
        user = UserTestData()

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse('access:my-modules')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'modules'      in response.data
        assert 'total_count'  in response.data
        assert 'root_count'   in response.data

    def test_inactive_module_access_not_counted(self):
        """Acceso a módulo con is_active=False no aparece en total_count."""
        user   = UserTestData()
        module = ModuleTestData()
        UserModuleAccess.objects.create(
            user=user, module=module, is_active=False)

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse('access:my-modules')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 0
    def test_inaccessible_child_not_in_response(self):
        """
        Un módulo hijo al que el usuario no tiene acceso no aparece en la
        respuesta aunque el padre sí sea accesible.

        Escenario:
            parent_module  ← usuario TIENE acceso
            child_module   ← usuario NO TIENE acceso

        La respuesta debe incluir parent_module con children vacío.
        """
        user   = UserTestData()
        parent = ModuleTestData(code='MOD_PARENT_X', name='Parent X')
        child  = ModuleTestData(code='MOD_CHILD_X',  name='Child X',
                                parent=parent)

        # Solo dar acceso al padre
        UserModuleAccess.objects.create(
            user=user, module=parent, is_active=True)

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse('access:my-modules')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 1

        # El hijo no debe aparecer en el árbol
        modules = response.data['modules']
        assert len(modules) == 1
        assert modules[0]['code'] == 'MOD_PARENT_X'
        assert modules[0]['children'] == []

