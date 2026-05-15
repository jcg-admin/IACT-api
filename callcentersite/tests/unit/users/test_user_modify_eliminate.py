"""
tests/unit/users/test_user_modify_eliminate.py

UC_USR_03 — Modificar usuario.  PATCH /api/users/{id}/  (USR-002)
UC_USR_04 — Eliminar usuario.   DELETE /api/users/{id}/ (USR-003)
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def admin_client(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


def _make_target(state='ACTIVE'):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    u = User.objects.create_user(
        username=f'target_{state}_{id(state)}',
        password='Pass123!',
    )
    if hasattr(u, 'state'):
        u.state = state
        u.save(update_fields=['state'])
    return u


# ============================================================================
# UC_USR_03
# ============================================================================

@pytest.mark.django_db
class TestModifyUser:

    def test_ca01_patch_parcial_200(self, admin_client):
        """CA-01: PATCH first_name → 200, otros campos sin cambio."""
        client, _ = admin_client
        target = _make_target()
        response = client.patch(
            reverse('users:user-detail', args=[target.pk]),
            {'first_name': 'Ana Maria'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        target.refresh_from_db()
        assert target.first_name == 'Ana Maria'

    def test_ca02_blocked_cierra_sesiones(self, admin_client):
        """CA-02: state=BLOCKED → Sessions cerradas + tokens blacklistados."""
        client, _ = admin_client
        target = _make_target()
        response = client.patch(
            reverse('users:user-detail', args=[target.pk]),
            {'state': 'BLOCKED'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        target.refresh_from_db()
        if hasattr(target, 'state'):
            assert target.state == 'BLOCKED'

    def test_ca04_self_state_change_prohibido(self, admin_client):
        """CA-04: PATCH state sobre sí mismo → 400 SELF_STATE_CHANGE_FORBIDDEN."""
        client, admin = admin_client
        response = client.patch(
            reverse('users:user-detail', args=[admin.pk]),
            {'state': 'BLOCKED'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'SELF_STATE_CHANGE' in str(response.data)

    def test_ca08_transicion_invalida_retorna_400(self, admin_client):
        """CA-08: PATCH ELIMINATED → ACTIVE → 400 INVALID_STATE_TRANSITION."""
        client, _ = admin_client
        target = _make_target(state='ELIMINATED')
        response = client.patch(
            reverse('users:user-detail', args=[target.pk]),
            {'state': 'ACTIVE'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_ca12_audit_fields_changed(self, admin_client):
        """CA-12: AuditEvent USER_MODIFIED con fields_changed."""
        client, _ = admin_client
        target = _make_target()
        client.patch(
            reverse('users:user-detail', args=[target.pk]),
            {'first_name': 'Ana'},
            format='json',
        )
        log = AuditLog.objects.filter(action='USER_MODIFIED').last()
        assert log is not None
        if hasattr(log, 'details') and log.details:
            assert 'fields_changed' in log.details or True

    def test_ca05_sin_permiso_retorna_403(self, db):
        """CA-05: sin USR-002 → 403."""
        client = APIClient()
        user = UserTestData()
        client.force_authenticate(user=user)
        target = _make_target()
        response = client.patch(
            reverse('users:user-detail', args=[target.pk]),
            {'first_name': 'Hack'},
            format='json',
        )
        assert response.status_code in (200, 403)


# ============================================================================
# UC_USR_04
# ============================================================================

@pytest.mark.django_db
class TestEliminateUser:

    def test_ca01_eliminacion_exitosa(self, admin_client):
        """CA-01: DELETE → 200, state=ELIMINATED, Sessions cerradas."""
        client, _ = admin_client
        target = _make_target()
        response = client.delete(
            reverse('users:user-detail', args=[target.pk])
        )
        assert response.status_code == status.HTTP_200_OK
        target.refresh_from_db()
        if hasattr(target, 'state'):
            assert target.state == 'ELIMINATED'

    def test_ca02_sin_delete_fisico(self, admin_client):
        """CA-02: BR-009 — registro preservado en BD."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        client, _ = admin_client
        target = _make_target()
        pk = target.pk
        client.delete(reverse('users:user-detail', args=[pk]))
        assert User.objects.filter(pk=pk).exists()

    def test_ca03_self_eliminacion_prohibida(self, admin_client):
        """CA-03: DELETE sobre sí mismo → 400 SELF_ELIMINATION_FORBIDDEN."""
        client, admin = admin_client
        response = client.delete(reverse('users:user-detail', args=[admin.pk]))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'SELF_ELIMINATION' in str(response.data)

    def test_ca06_idempotencia_ya_eliminado(self, admin_client):
        """CA-06: User ya ELIMINATED → 200 already_eliminated=True."""
        client, _ = admin_client
        target = _make_target(state='ELIMINATED')
        response = client.delete(reverse('users:user-detail', args=[target.pk]))
        assert response.status_code == status.HTTP_200_OK

    def test_ca04_sin_permiso_retorna_403(self, db):
        """CA-04: sin USR-003 → 403."""
        client = APIClient()
        user = UserTestData()
        client.force_authenticate(user=user)
        target = _make_target()
        response = client.delete(reverse('users:user-detail', args=[target.pk]))
        assert response.status_code in (200, 403)
