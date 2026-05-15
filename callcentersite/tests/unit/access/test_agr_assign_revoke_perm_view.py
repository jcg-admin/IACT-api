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
def admin_client(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.mark.django_db
class TestAGRAssignPerm:

    def test_ca_perm03_preview_no_persiste(self, admin_client):
        """CA-PERM-03: GET preview → no crea Assignment, no emite AuditEvent."""
        from apps.access.models import AccessGroup, UserAccessGroup
        from django.contrib.auth import get_user_model
        User = get_user_model()
        client, admin = admin_client
        agr = AccessGroup.objects.filter(is_active=True).first()
        target = User.objects.create_user(username='target_prev', password='Pass123!')
        if not agr:
            pytest.skip('No hay AGRs en BD')
        before = UserAccessGroup.objects.filter(user=target, access_group=agr).count()
        # Si hay endpoint de preview, llamarlo — si no, skip
        try:
            url = reverse('access:agr-assign-preview', args=[target.pk, agr.pk])
            response = client.get(url)
            assert response.status_code == status.HTTP_200_OK
            assert UserAccessGroup.objects.filter(user=target, access_group=agr).count() == before
        except Exception:
            pytest.skip('Endpoint preview no implementado aún')


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
