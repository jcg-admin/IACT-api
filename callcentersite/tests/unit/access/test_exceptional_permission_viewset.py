"""
tests/unit/access/test_exceptional_permission_viewset.py

N-005 — Tests del ExceptionalPermissionViewSet.
Flujo completo: pending → approved → revoked.
"""
import pytest
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from apps.access.models import ExceptionalPermission
from tests.test_data.access_test_data import (
    ExceptionalPermissionTestData,
    FunctionTestData,
)
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


def _get_permissions_fn_codes():
    return [
        'access.view_exceptional_permissions',
        'access.request_exceptional_permission',
        'access.manage_exceptional_permissions',
    ]


@pytest.fixture
def manager_client(db, api_client):
    user = AdminUserTestData()
    api_client.force_authenticate(user=user)
    from apps.access.models import UserPermission
    from tests.test_data.access_test_data import FunctionTestData
    for code in _get_permissions_fn_codes():
        fn = FunctionTestData(code=code, permission_django=code)
        UserPermission.objects.get_or_create(user=user, function=fn)
    api_client._user = user
    return api_client


@pytest.mark.django_db
class TestExceptionalPermissionLifecycle:
    """N-005: ciclo de vida completo del permiso excepcional."""

    def test_create_sets_status_pending(self, manager_client):
        fn = FunctionTestData()
        requester = UserTestData()
        url = reverse('access:exceptional-list')
        now = timezone.now()
        response = manager_client.post(url, {
            'user': requester.pk,
            'function': fn.pk,
            'justification': 'J' * 55,
            'valid_from': now.isoformat(),
            'valid_until': (now + timedelta(days=7)).isoformat(),
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'pending'

    def test_approve_changes_status_to_approved(self, manager_client):
        perm = ExceptionalPermissionTestData(status='pending')
        url = reverse('access:exceptional-approve', args=[perm.pk])
        response = manager_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        perm.refresh_from_db()
        assert perm.status == 'approved'

    def test_revoke_changes_status_to_revoked(self, manager_client):
        perm = ExceptionalPermissionTestData(status='approved',
                                             granted_by=manager_client._user)
        url = reverse('access:exceptional-revoke', args=[perm.pk])
        response = manager_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        perm.refresh_from_db()
        assert perm.status == 'revoked'

    def test_cannot_approve_already_revoked(self, manager_client):
        perm = ExceptionalPermissionTestData(status='revoked')
        url = reverse('access:exceptional-approve', args=[perm.pk])
        response = manager_client.patch(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_revoke_already_revoked(self, manager_client):
        perm = ExceptionalPermissionTestData(status='revoked')
        url = reverse('access:exceptional-revoke', args=[perm.pk])
        response = manager_client.patch(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_revoke_already_expired(self, manager_client):
        perm = ExceptionalPermissionTestData(status='expired')
        url = reverse('access:exceptional-revoke', args=[perm.pk])
        response = manager_client.patch(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
