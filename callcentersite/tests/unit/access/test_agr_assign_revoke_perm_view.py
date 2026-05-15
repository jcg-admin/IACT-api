"""
tests/unit/access/test_agr_assign_revoke_perm_view.py

UC_PERM_01 — Vista PERM: asignar AGR.
UC_PERM_02 — Vista PERM: revocar AGR. CA-PERM-01: 404 si AGR nunca asignado.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from tests.test_data.user_test_data import AdminUserTestData


@pytest.fixture
def admin_client(db_with_catalog):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.mark.django_db
class TestAGRAssignPerm:

    def test_ca_perm03_preview_no_persiste(self, admin_client):
        """
        CA-PERM-03: GET /api/access/users/{id}/agr/ → preview de AGR asignados.
        No crea UserAccessGroup, no emite AuditEvent.
        """
        import uuid
        from apps.access.models import AccessGroup, UserAccessGroup
        from django.contrib.auth import get_user_model
        User = get_user_model()
        client, admin = admin_client
        u = uuid.uuid4().hex[:6]
        target = User.objects.create_user(username=f'target_prev_{u}', password='Pass123!')
        url = reverse('access:agr-assign', kwargs={'user_id': target.pk})
        before = UserAccessGroup.objects.filter(user=target).count()
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Preview: no crea asignaciones
        assert UserAccessGroup.objects.filter(user=target).count() == before
        assert 'assigned_agr' in response.data


@pytest.mark.django_db
class TestAGRRevokePerm:

    def test_ca_perm01_agr_no_asignado_retorna_404(self, admin_client):
        """CA-PERM-01: DELETE revoke sobre AGR nunca asignado → 404 AGR_NOT_ASSIGNED."""
        from apps.access.models import AccessGroup
        from django.contrib.auth import get_user_model
        User = get_user_model()
        client, admin = admin_client
        agr = AccessGroup.objects.filter(is_active=True).first()
        target = User.objects.create_user(username='target_revoke', password='Pass123!')
        if not agr:
            pytest.skip('No hay AGRs en BD')
        # AGR nunca fue asignado al target
        response = client.delete(
            reverse('access:agr-revoke', args=[target.pk, agr.pk])
        )
        # CA-PERM-01: debe ser 404, no 200/400
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_revocar_agr_asignado_retorna_200(self, admin_client):
        """Revocar AGR que SÍ fue asignado → 200."""
        from apps.access.models import AccessGroup, UserAccessGroup
        from django.contrib.auth import get_user_model
        User = get_user_model()
        client, admin = admin_client
        agr = AccessGroup.objects.filter(is_active=True).first()
        target = User.objects.create_user(username='target_rev_ok', password='Pass123!')
        if not agr:
            pytest.skip('No hay AGRs en BD')
        # Asignar primero
        UserAccessGroup.objects.create(user=target, access_group=agr)
        response = client.delete(
            reverse('access:agr-revoke', args=[target.pk, agr.pk])
        )
        assert response.status_code == status.HTTP_200_OK
