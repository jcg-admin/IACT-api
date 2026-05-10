"""
tests/unit/access/test_access_group_viewset.py

N-003 — Tests del AccessGroupViewSet.
CRUD completo + add-function / remove-function.
"""
import pytest
from django.urls import reverse
from rest_framework import status

from tests.test_data.access_test_data import (
    AccessGroupTestData,
    FunctionTestData,
)
from tests.test_data.user_test_data import AdminUserTestData


@pytest.fixture
def admin_client(db, api_client):
    user = AdminUserTestData()
    api_client.force_authenticate(user=user)
    # Dar función de gestión de grupos
    from apps.access.models import UserPermission
    from tests.test_data.access_test_data import FunctionTestData
    fn = FunctionTestData(code='access.manage_groups', permission_django='access.manage_groups')
    UserPermission.objects.get_or_create(user=user, function=fn)
    return api_client


@pytest.mark.django_db
class TestAccessGroupCRUD:
    """N-003-A: CRUD básico de AccessGroup."""

    def test_list_groups(self, admin_client):
        AccessGroupTestData.create_batch(3)
        url = reverse('access:accessgroup-list')
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_group(self, admin_client):
        url = reverse('access:accessgroup-list')
        response = admin_client.post(url, {
            'name': 'Supervisores IVR',
            'code': 'SUPERVISOR_IVR',
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == 'SUPERVISOR_IVR'

    def test_retrieve_group(self, admin_client):
        group = AccessGroupTestData()
        url = reverse('access:accessgroup-detail', args=[group.pk])
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == group.code

    def test_update_group(self, admin_client):
        group = AccessGroupTestData()
        url = reverse('access:accessgroup-detail', args=[group.pk])
        response = admin_client.patch(url, {'name': 'Nombre actualizado'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Nombre actualizado'

    def test_delete_group(self, admin_client):
        group = AccessGroupTestData()
        url = reverse('access:accessgroup-detail', args=[group.pk])
        response = admin_client.delete(url)
        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
        )


@pytest.mark.django_db
class TestAccessGroupFunctionAssignment:
    """N-003-B: add-function y remove-function."""

    def test_add_function_to_group(self, admin_client):
        group = AccessGroupTestData()
        fn = FunctionTestData()
        url = reverse('access:accessgroup-add-function', args=[group.pk])
        response = admin_client.post(url, {'function_id': fn.pk})
        assert response.status_code == status.HTTP_200_OK
        group.refresh_from_db()
        assert fn in group.functions.all()

    def test_remove_function_from_group(self, admin_client):
        group = AccessGroupTestData()
        fn = FunctionTestData()
        group.functions.add(fn)
        url = reverse('access:accessgroup-remove-function', args=[group.pk])
        response = admin_client.delete(url, {'function_id': fn.pk},
                                       format='json')
        assert response.status_code == status.HTTP_200_OK
        group.refresh_from_db()
        assert fn not in group.functions.all()

    def test_add_nonexistent_function_returns_404(self, admin_client):
        group = AccessGroupTestData()
        url = reverse('access:accessgroup-add-function', args=[group.pk])
        response = admin_client.post(url, {'function_id': 99999})
        assert response.status_code == status.HTTP_404_NOT_FOUND
