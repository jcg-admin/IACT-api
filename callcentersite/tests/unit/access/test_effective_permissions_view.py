"""
tests/unit/access/test_effective_permissions_view.py

N-006 — Tests de EffectivePermissionsView.
Verifica la unión de las tres fuentes y que permisos expirados
no aparecen en el resultado.
"""
import pytest
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from apps.access.models import (
    ExceptionalPermission, UserPermission,
    AccessGroup, UserAccessGroup,
)
from tests.test_data.access_test_data import FunctionTestData
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def viewer_client(db, api_client):
    admin = AdminUserTestData()
    api_client.force_authenticate(user=admin)
    from apps.access.models import UserPermission
    from tests.test_data.access_test_data import FunctionTestData
    fn = FunctionTestData(code='access.view_permissions', permission_django='access.view_permissions')
    UserPermission.objects.get_or_create(user=admin, function=fn)
    return api_client


@pytest.mark.django_db
class TestEffectivePermissionsView:
    """N-006: unión de tres fuentes y exclusión de expirados."""

    def test_includes_direct_permission(self, viewer_client):
        user = UserTestData()
        fn = FunctionTestData()
        UserPermission.objects.create(user=user, function=fn)

        url = reverse('access:effective-permissions',
                      kwargs={'user_id': user.pk})
        response = viewer_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert fn.code in response.data['sources']['direct']
        assert fn.code in response.data['effective']

    def test_includes_function_from_access_group(self, viewer_client):
        user = UserTestData()
        fn = FunctionTestData()
        group = AccessGroup.objects.create(
            name='Test Group', code='TST_GRP')
        group.functions.add(fn)
        UserAccessGroup.objects.create(user=user, access_group=group)

        url = reverse('access:effective-permissions',
                      kwargs={'user_id': user.pk})
        response = viewer_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert fn.code in response.data['sources']['from_groups']
        assert fn.code in response.data['effective']

    def test_includes_active_exceptional_permission(self, viewer_client):
        user = UserTestData()
        fn = FunctionTestData()
        now = timezone.now()
        ExceptionalPermission.objects.create(
            user=user, function=fn,
            justification='J' * 55,
            status='approved',
            valid_from=now - timedelta(hours=1),
            valid_until=now + timedelta(days=7),
        )

        url = reverse('access:effective-permissions',
                      kwargs={'user_id': user.pk})
        response = viewer_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert fn.code in response.data['sources']['exceptional']
        assert fn.code in response.data['effective']

    def test_expired_exceptional_permission_excluded(self, viewer_client):
        user = UserTestData()
        fn = FunctionTestData()
        now = timezone.now()
        ExceptionalPermission.objects.create(
            user=user, function=fn,
            justification='J' * 55,
            status='approved',
            valid_from=now - timedelta(days=10),
            valid_until=now - timedelta(days=3),  # expirado
        )

        url = reverse('access:effective-permissions',
                      kwargs={'user_id': user.pk})
        response = viewer_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert fn.code not in response.data['effective']

    def test_union_of_all_three_sources(self, viewer_client):
        user = UserTestData()
        fn_direct = FunctionTestData()
        fn_group = FunctionTestData()
        fn_exceptional = FunctionTestData()

        # Fuente 1: directo
        UserPermission.objects.create(user=user, function=fn_direct)

        # Fuente 2: grupo
        group = AccessGroup.objects.create(
            name='Group N006', code='GRP_N006')
        group.functions.add(fn_group)
        UserAccessGroup.objects.create(user=user, access_group=group)

        # Fuente 3: excepcional
        now = timezone.now()
        ExceptionalPermission.objects.create(
            user=user, function=fn_exceptional,
            justification='J' * 55, status='approved',
            valid_from=now - timedelta(hours=1),
            valid_until=now + timedelta(days=7),
        )

        url = reverse('access:effective-permissions',
                      kwargs={'user_id': user.pk})
        response = viewer_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        effective = response.data['effective']
        assert fn_direct.code in effective
        assert fn_group.code in effective
        assert fn_exceptional.code in effective
        assert response.data['total_functions'] >= 3
