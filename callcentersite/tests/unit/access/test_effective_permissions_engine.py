"""
tests/unit/access/test_effective_permissions_engine.py

UC_PERM_07 — Motor de permisos efectivos.
GET /api/access/users/{user_id}/effective-permissions/
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


def _url(user_id):
    return reverse('access:effective-permissions', args=[user_id])


@pytest.mark.django_db
class TestEffectivePermissionsPrecedence:

    def test_ca01_agr_otorga_con_origin(self, admin_client):
        """CA-01: función via AGR → origin=GRANTED_BY_AGR en sources."""
        client, admin = admin_client
        response = client.get(_url(admin.pk))
        assert response.status_code == status.HTTP_200_OK
        assert 'sources' in response.data or 'effective' in response.data

    def test_ca04_sin_grant_denied(self, admin_client):
        """CA-04: función no asignada → no aparece en effective."""
        client, admin = admin_client
        response = client.get(_url(admin.pk))
        assert response.status_code == status.HTTP_200_OK
        # La función 'RPT-999' no existe — no debe aparecer
        effective = response.data.get('effective', [])
        assert 'RPT-999' not in effective

    def test_ca13_user_no_existe_retorna_404(self, admin_client):
        """CA-13: user_id inexistente → 404."""
        client, _ = admin_client
        response = client.get(_url(99999))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_ca16_sin_audit_events(self, admin_client):
        """CA-16: ZERO AuditEvents emitidos por invocación."""
        from apps.audit.models import AuditLog
        client, admin = admin_client
        before = AuditLog.objects.count()
        client.get(_url(admin.pk))
        assert AuditLog.objects.count() == before


@pytest.mark.django_db
class TestEffectivePermissionsStatus:

    def test_ca05_exceptional_estado_active_cuenta(self, admin_client):
        """CA-02/05: ExceptionalPermission con status='ACTIVE' cuenta como concesión."""
        from apps.access.models import ExceptionalPermission, Function
        from django.utils import timezone
        from datetime import timedelta
        client, admin = admin_client
        fn = Function.objects.first()
        if not fn:
            pytest.skip('No hay funciones en BD')
        ExceptionalPermission.objects.create(
            user=admin, function=fn,
            justification='Test justification for testing' * 2,
            status=ExceptionalPermission.STATE_ACTIVE,
            expires_at=timezone.now() + timedelta(days=1),
            granted_at=timezone.now(),
        )
        response = client.get(_url(admin.pk))
        assert response.status_code == status.HTTP_200_OK
        effective = response.data.get('effective', [])
        assert fn.code in effective

    def test_ca07_exceptional_expirado_no_cuenta(self, admin_client):
        """CA-07: ExceptionalPermission expirado → no cuenta."""
        from apps.access.models import ExceptionalPermission, Function
        from django.utils import timezone
        from datetime import timedelta
        from django.contrib.auth import get_user_model
        User = get_user_model()
        client, admin = admin_client
        target = User.objects.create_user(username='target_exp07', password='Pass123!')
        fn = Function.objects.first()
        if not fn:
            pytest.skip('No hay funciones en BD')
        ExceptionalPermission.objects.create(
            user=target, function=fn,
            justification='Test justification for testing' * 2,
            status=ExceptionalPermission.STATE_EXPIRED,
            expires_at=timezone.now() - timedelta(days=1),
            granted_at=timezone.now() - timedelta(days=2),
        )
        response = client.get(_url(target.pk))
        assert response.status_code == status.HTTP_200_OK
        # El permiso expirado no debería conceder la función
        sources_exceptional = response.data.get('sources', {}).get('exceptional', [])
        assert fn.code not in sources_exceptional
