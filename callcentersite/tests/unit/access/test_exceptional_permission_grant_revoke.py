"""
tests/unit/access/test_exceptional_permission_grant_revoke.py

UC_ACC_08 — Conceder Permiso Excepcional. UC_PERM_03 — Preview. UC_PERM_04 — Revocar.
"""
import uuid
import pytest
from datetime import timedelta
from unittest.mock import patch
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.access.models import ExceptionalPermission, Function
from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def admin_client(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_sin_perm(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _grant_url(user_id):
    return reverse('access:exceptional-grant', args=[user_id])


def _preview_url(user_id):
    return reverse('access:exceptional-preview', args=[user_id])


def _revoke_url(user_id, perm_id):
    return reverse('access:exceptional-revoke', args=[user_id, perm_id])


def _valid_grant_payload(function_ids, hours_ahead=72):
    expires_at = (timezone.now() + timedelta(hours=hours_ahead)).isoformat()
    return {
        'function_ids':   function_ids,
        'expires_at':     expires_at,
        'justification':  'TKT-12345 Cobertura de baja médica del admin titular.',
        'ticket_reference': 'TKT-12345',
    }


# ---------------------------------------------------------------------------
# UT-01..10: JustificationValidator, ExpirationPolicy, AntiSelfActionPolicy
# ---------------------------------------------------------------------------

class TestJustificationValidator:

    def test_justification_menor_20_rechazada(self):
        from apps.access.exceptional_permission_service import JustificationValidator
        with pytest.raises(ValueError, match='20'):
            JustificationValidator.validate('Muy corto.')

    def test_justification_20_chars_aceptada(self):
        from apps.access.exceptional_permission_service import JustificationValidator
        JustificationValidator.validate('A' * 20)

    def test_ticket_reference_required_cuando_politica(self):
        from apps.access.exceptional_permission_service import JustificationValidator
        with pytest.raises(ValueError, match='TICKET'):
            JustificationValidator.validate(
                'Sin ticket ' + 'x' * 20,
                require_ticket=True,
            )

    def test_con_ticket_en_texto_pasa(self):
        from apps.access.exceptional_permission_service import JustificationValidator
        JustificationValidator.validate(
            'TKT-12345 Cobertura de licencia x' * 1,
            require_ticket=True,
        )


class TestExpirationPolicy:

    def test_expires_at_requerido(self):
        from apps.access.exceptional_permission_service import ExpirationPolicy
        with pytest.raises(ValueError, match='expires_at'):
            ExpirationPolicy.validate(None)

    def test_expires_at_menor_1h_rechazado(self):
        from apps.access.exceptional_permission_service import ExpirationPolicy
        with pytest.raises(ValueError):
            ExpirationPolicy.validate(timezone.now() + timedelta(minutes=30))

    def test_expires_at_mayor_30_dias_rechazado(self):
        from apps.access.exceptional_permission_service import ExpirationPolicy
        with pytest.raises(ValueError):
            ExpirationPolicy.validate(timezone.now() + timedelta(days=31))

    def test_expires_at_en_bounds_aceptado(self):
        from apps.access.exceptional_permission_service import ExpirationPolicy
        ExpirationPolicy.validate(timezone.now() + timedelta(hours=24))


class TestAntiSelfActionPolicy:

    def test_auto_grant_lanza(self):
        from apps.access.exceptional_permission_service import AntiSelfActionPolicy
        with pytest.raises(ValueError, match='SELF_GRANT_FORBIDDEN'):
            AntiSelfActionPolicy.check_grant(invoker_id=1, target_id=1)

    def test_grant_a_otro_pasa(self):
        from apps.access.exceptional_permission_service import AntiSelfActionPolicy
        AntiSelfActionPolicy.check_grant(invoker_id=1, target_id=2)

    def test_auto_revoke_lanza(self):
        from apps.access.exceptional_permission_service import AntiSelfActionPolicy
        with pytest.raises(ValueError, match='SELF_REVOKE_FORBIDDEN'):
            AntiSelfActionPolicy.check_revoke(invoker_id=1, target_id=1)


# ---------------------------------------------------------------------------
# IT-01..12: UC_ACC_08 endpoint
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestExceptionalGrantEndpoint:

    def _fn_ids(self):
        fns = Function.objects.filter(code__in=['RPT-001', 'RPT-002'])[:1]
        return [f.id for f in fns] if fns else []

    def test_it01_grant_retorna_201_con_granted(self, admin_client):
        """CA-01: POST → 201 + granted[]."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_grant', password='P@ss123!')
        fn_ids = self._fn_ids()
        if not fn_ids:
            pytest.skip('No hay funciones disponibles en la BD')
        response = client.post(_grant_url(target.pk), _valid_grant_payload(fn_ids), format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'granted' in response.data

    def test_it01_audit_exceptional_permission_granted(self, admin_client):
        """CA-12: AuditEvent EXCEPTIONAL_PERMISSION_GRANTED emitido."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_audit_g', password='P@ss123!')
        fn_ids = self._fn_ids()
        if not fn_ids:
            pytest.skip('No hay funciones disponibles')
        before = AuditLog.objects.count()
        client.post(_grant_url(target.pk), _valid_grant_payload(fn_ids), format='json')
        assert AuditLog.objects.filter(
            event_type='EXCEPTIONAL_PERMISSION_GRANTED').count() > 0

    def test_it02_justification_corta_retorna_400(self, admin_client):
        """CA-02: justification < 20 chars → 400."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_short_j', password='P@ss123!')
        payload = _valid_grant_payload([1])
        payload['justification'] = 'Corto'
        response = client.post(_grant_url(target.pk), payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it03_expires_at_mayor_30_dias_retorna_400(self, admin_client):
        """CA-03: expires_at > NOW()+30d → 400."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_exp', password='P@ss123!')
        response = client.post(
            _grant_url(target.pk),
            _valid_grant_payload([1], hours_ahead=31 * 24),
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it05_auto_grant_retorna_400(self, admin_client):
        """CA-05: invoker == target → 400 SELF_GRANT_FORBIDDEN."""
        client, admin = admin_client
        response = client.post(
            _grant_url(admin.pk),
            _valid_grant_payload([1]),
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'SELF_GRANT' in str(response.data)

    def test_it07_mailbox_falla_hace_rollback(self, admin_client):
        """CA-07: mailbox HARD — sin ExceptionalPermission si falla."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_mbfail', password='P@ss123!')
        fn_ids = self._fn_ids()
        if not fn_ids:
            pytest.skip('No hay funciones disponibles')
        before = ExceptionalPermission.objects.count()
        with patch('apps.access.exceptional_permission_service.ExceptionalPermissionService._notify',
                   side_effect=Exception('mailbox down')):
            response = client.post(_grant_url(target.pk), _valid_grant_payload(fn_ids), format='json')
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert ExceptionalPermission.objects.count() == before  # rollback

    def test_it09_idempotencia_parcial(self, admin_client):
        """CA-09: function_id ya ACTIVE → skipped, nueva → granted."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_idemp', password='P@ss123!')
        fns = list(Function.objects.all()[:2])
        if len(fns) < 2:
            pytest.skip('Faltan funciones en BD')
        # Pre-crear un permiso ACTIVE para fns[0]
        ExceptionalPermission.objects.create(
            user=target, function=fns[0],
            justification='Pre-existing ' * 3,
            status=ExceptionalPermission.STATE_ACTIVE,
            expires_at=timezone.now() + timedelta(days=1),
        )
        payload = _valid_grant_payload([fns[0].id, fns[1].id])
        response = client.post(_grant_url(target.pk), payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'skipped' in response.data

    def test_sec_sin_permiso_retorna_403(self, client_sin_perm):
        """CA-08: sin ACC-008 → 403."""
        response = client_sin_perm.post(
            _grant_url(1), _valid_grant_payload([1]), format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# IT-01..04: UC_PERM_03 — Preview
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestExceptionalPreviewEndpoint:

    def test_it01_preview_retorna_200_sin_persistir(self, admin_client):
        """CA-PERM-01: GET preview → 200, ZERO ExceptionalPermission."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_prev', password='P@ss123!')
        before = ExceptionalPermission.objects.count()
        response = client.get(_preview_url(target.pk), {
            'function_ids': '1,2',
            'expires_at': (timezone.now() + timedelta(hours=24)).isoformat(),
        })
        assert response.status_code == status.HTTP_200_OK
        assert ExceptionalPermission.objects.count() == before  # CA-PERM-01

    def test_it01_preview_sin_audit(self, admin_client):
        """CA-PERM-01: GET preview → ZERO AuditEvent."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_prev2', password='P@ss123!')
        before = AuditLog.objects.count()
        client.get(_preview_url(target.pk), {
            'function_ids': '1',
            'expires_at': (timezone.now() + timedelta(hours=24)).isoformat(),
        })
        assert AuditLog.objects.count() == before  # CA-PERM-01: sin audit


# ---------------------------------------------------------------------------
# IT-01..11: UC_PERM_04 — Revocar
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestExceptionalRevokeEndpoint:

    def _make_active_perm(self, user, function=None):
        if function is None:
            function = Function.objects.first()
        if not function:
            pytest.skip('No hay funciones en BD')
        return ExceptionalPermission.objects.create(
            user=user, function=function,
            justification='Test justification for testing purposes',
            status=ExceptionalPermission.STATE_ACTIVE,
            expires_at=timezone.now() + timedelta(days=7),
            granted_at=timezone.now(),
        )

    def _revoke_payload(self):
        return {'revoke_reason': 'TKT-12345 cerrado, acceso ya no requerido.'}

    def test_it01_revoke_retorna_200_state_revoked(self, admin_client):
        """CA-01: DELETE → 200 + state=REVOKED."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_rev', password='P@ss123!')
        perm = self._make_active_perm(target)
        response = client.delete(
            _revoke_url(target.pk, perm.pk),
            self._revoke_payload(), format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        perm.refresh_from_db()
        assert perm.status == ExceptionalPermission.STATE_REVOKED

    def test_it01_revoked_by_admin_registrado(self, admin_client):
        """CA-01 + CA-02: revoked_by_admin_id == invoker."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_rev2', password='P@ss123!')
        perm = self._make_active_perm(target)
        client.delete(_revoke_url(target.pk, perm.pk), self._revoke_payload(), format='json')
        perm.refresh_from_db()
        assert perm.revoked_by_id == admin.pk

    def test_it01_audit_exceptional_permission_revoked(self, admin_client):
        """CA-01: AuditEvent EXCEPTIONAL_PERMISSION_REVOKED (no EXPIRED)."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_rev3', password='P@ss123!')
        perm = self._make_active_perm(target)
        client.delete(_revoke_url(target.pk, perm.pk), self._revoke_payload(), format='json')
        assert AuditLog.objects.filter(
            event_type='EXCEPTIONAL_PERMISSION_REVOKED').exists()

    def test_it04_ya_revocado_retorna_200_noop(self, admin_client):
        """CA-03: idempotencia — ya REVOKED → 200 con REVOKE_NOOP."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_noop', password='P@ss123!')
        perm = self._make_active_perm(target)
        perm.status = ExceptionalPermission.STATE_REVOKED
        perm.save(update_fields=['status'])
        response = client.delete(
            _revoke_url(target.pk, perm.pk),
            self._revoke_payload(), format='json',
        )
        assert response.status_code == status.HTTP_200_OK

    def test_it05_expired_retorna_400(self, admin_client):
        """CA-04: EXPIRED → 400 INVALID_STATE."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_expd', password='P@ss123!')
        perm = self._make_active_perm(target)
        perm.status = ExceptionalPermission.STATE_EXPIRED
        perm.save(update_fields=['status'])
        response = client.delete(
            _revoke_url(target.pk, perm.pk),
            self._revoke_payload(), format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it06_auto_revoke_retorna_400(self, admin_client):
        """CA-07: invoker == target → 400 SELF_REVOKE_FORBIDDEN."""
        client, admin = admin_client
        perm = self._make_active_perm(admin)
        response = client.delete(
            _revoke_url(admin.pk, perm.pk),
            self._revoke_payload(), format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it08_reason_vacia_retorna_400(self, admin_client):
        """CA-06: revoke_reason < 20 chars → 400."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_reason', password='P@ss123!')
        perm = self._make_active_perm(target)
        response = client.delete(
            _revoke_url(target.pk, perm.pk),
            {'revoke_reason': 'Corto'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it09_mailbox_falla_hace_rollback(self, admin_client):
        """CA-08: mailbox HARD — permission permanece ACTIVE si falla."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_mbfail2', password='P@ss123!')
        perm = self._make_active_perm(target)
        with patch('apps.access.exceptional_permission_service.ExceptionalPermissionService._notify_revoke',
                   side_effect=Exception('mailbox down')):
            response = client.delete(
                _revoke_url(target.pk, perm.pk),
                self._revoke_payload(), format='json',
            )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        perm.refresh_from_db()
        assert perm.status == ExceptionalPermission.STATE_ACTIVE  # rollback

    def test_sec_sin_permiso_retorna_403(self, client_sin_perm):
        """CA-05: sin ACC-009 → 403."""
        response = client_sin_perm.delete(
            _revoke_url(1, 1), {'revoke_reason': 'x' * 25}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
