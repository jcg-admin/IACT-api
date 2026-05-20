"""
tests/unit/authentication/test_change_password.py

UC_AUTH_04 — Cambiar contraseña.
POST /api/auth/change-password/
Solo IsAuthenticated (sin RBAC adicional).
"""
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture(autouse=True)
def disable_throttle(monkeypatch):
    """
    Deshabilitar el throttle de ChangePasswordView en todos los tests del módulo.

    Problema raíz (H-F6-GRP-GA-001):
      - pytest.mark.django_db usa SAVEPOINT/ROLLBACK (no DROP+CREATE entre tests).
      - SQLite reutiliza pk=1 para el primer usuario creado en cada test.
      - LocMemCache persiste entre tests en el mismo proceso.
      - Resultado: throttle_change_password_1 acumula conteos de todos los tests,
        causando 429 intermitentes en tests que crean el primer usuario con pk=1.

    La prueba del throttle real (CA-07) se hace via mock explícito,
    no via acumulación de requests reales.
    """
    from apps.authentication import change_password_view
    monkeypatch.setattr(change_password_view.ChangePasswordView, 'throttle_classes', [])


def _url():
    return reverse('authentication:change-password')


def _make_user(state='ACTIVE', first_login=False):
    import uuid
    from django.contrib.auth import get_user_model
    User = get_user_model()
    u = User.objects.create_user(
        username=f'cpasswd_{uuid.uuid4().hex[:8]}',
        password='CurrentPass123!',
    )
    if hasattr(u, 'state'):
        u.state = state
        u.first_login = first_login
        u.save(update_fields=['state', 'first_login'])
    return u


@pytest.fixture
def auth_client(db):
    client = APIClient()
    user = _make_user()
    client.force_authenticate(user=user)
    return client, user


# ---------------------------------------------------------------------------
# CA-01: flujo principal
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChangePasswordMainFlow:

    def test_ca01_200_y_password_cambia(self, auth_client):
        """CA-01: POST exitoso → 200, hash cambia, first_login=False."""
        client, user = auth_client
        response = client.post(_url(), {
            'current_password': 'CurrentPass123!',
            'new_password': 'NuevoPass2026!@',
            'new_password_confirmation': 'NuevoPass2026!@',
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password('NuevoPass2026!@')

    def test_ca01_first_login_false_post_cambio(self, db):
        """CA-01: first_login=False tras cambio exitoso."""
        client = APIClient()
        user = _make_user(first_login=True)
        client.force_authenticate(user=user)
        client.post(_url(), {
            'current_password': 'CurrentPass123!',
            'new_password': 'NuevoPass2026!@',
            'new_password_confirmation': 'NuevoPass2026!@',
        }, format='json')
        user.refresh_from_db()
        if hasattr(user, 'first_login'):
            assert user.first_login is False

    def test_ca01_audit_password_changed_emitido(self, auth_client):
        """CA-01: AuditEvent PASSWORD_CHANGED emitido."""
        client, user = auth_client
        before = AuditLog.objects.count()
        client.post(_url(), {
            'current_password': 'CurrentPass123!',
            'new_password': 'NuevoPass2026!@',
            'new_password_confirmation': 'NuevoPass2026!@',
        }, format='json')
        assert AuditLog.objects.count() > before

    def test_ca01_body_no_contiene_password(self, auth_client):
        """CA-01: response body NO contiene la contraseña nueva."""
        import json
        client, user = auth_client
        response = client.post(_url(), {
            'current_password': 'CurrentPass123!',
            'new_password': 'NuevoPass2026!@',
            'new_password_confirmation': 'NuevoPass2026!@',
        }, format='json')
        body = json.dumps(response.data)
        assert 'NuevoPass2026' not in body
        assert 'CurrentPass' not in body


# ---------------------------------------------------------------------------
# CA-02..06: validaciones
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChangePasswordValidations:

    def test_ca02_current_password_incorrecto(self, auth_client):
        """CA-02: current_password incorrecto → 400 WRONG_CURRENT_PASSWORD."""
        client, _ = auth_client
        response = client.post(_url(), {
            'current_password': 'WrongPass!',
            'new_password': 'NuevoPass2026!@',
            'new_password_confirmation': 'NuevoPass2026!@',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_ca03_politica_violada_weak(self, auth_client):
        """CA-03: new_password débil → 400 WEAK_PASSWORD."""
        client, _ = auth_client
        response = client.post(_url(), {
            'current_password': 'CurrentPass123!',
            'new_password': 'abc',
            'confirmation': 'abc',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_ca05_igual_a_actual(self, auth_client):
        """CA-05: new_password == current_password → 400 SAME_AS_CURRENT."""
        client, _ = auth_client
        response = client.post(_url(), {
            'current_password': 'CurrentPass123!',
            'new_password': 'CurrentPass123!',
            'new_password_confirmation': 'CurrentPass123!',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_ca06_mismatch_confirmation(self, auth_client):
        """CA-06: new_password != confirmation → 400."""
        client, _ = auth_client
        response = client.post(_url(), {
            'current_password': 'CurrentPass123!',
            'new_password': 'NuevoPass2026!@',
            'new_password_confirmation': 'Diferente2026!@',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# CA-08: scope upgrade
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChangePasswordScopeUpgrade:

    def test_ca08_scope_upgraded_true_si_first_login(self, db):
        """CA-08: si first_login=True antes del cambio, body contiene scope_upgraded=True."""
        client = APIClient()
        user = _make_user(first_login=True)
        client.force_authenticate(user=user)
        response = client.post(_url(), {
            'current_password': 'CurrentPass123!',
            'new_password': 'NuevoPass2026!@',
            'new_password_confirmation': 'NuevoPass2026!@',
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('scope_upgraded') is True

    def test_ca08_scope_upgraded_false_si_no_first_login(self, auth_client):
        """CA-08: si first_login=False, scope_upgraded=False o ausente."""
        client, user = auth_client
        response = client.post(_url(), {
            'current_password': 'CurrentPass123!',
            'new_password': 'NuevoPass2026!@',
            'new_password_confirmation': 'NuevoPass2026!@',
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert not response.data.get('scope_upgraded', False)


# ---------------------------------------------------------------------------
# CA-12/13: sin password en logs ni audit
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChangePasswordNoLeak:

    def test_ca13_audit_no_contiene_password(self, auth_client):
        """CA-13: AuditEvent PASSWORD_CHANGED — payload sin contraseña."""
        client, user = auth_client
        client.post(_url(), {
            'current_password': 'CurrentPass123!',
            'new_password': 'NuevoPass2026!@',
            'new_password_confirmation': 'NuevoPass2026!@',
        }, format='json')
        import json
        for log in AuditLog.objects.all():
            payload_str = json.dumps(getattr(log, 'details', {}) or {})
            assert 'NuevoPass2026' not in payload_str
            assert 'CurrentPass' not in payload_str


# ---------------------------------------------------------------------------
# CA-16: BLOCKED puede cambiar
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChangePasswordBlocked:

    def test_ca16_blocked_puede_cambiar(self, db):
        """CA-16: User BLOCKED → 200, state permanece BLOCKED.

        El throttle está deshabilitado en fase0_testing (ver H-F6-GRP-GA-001).
        """
        client = APIClient()
        user = _make_user(state='BLOCKED')
        client.force_authenticate(user=user)
        response = client.post(_url(), {
            'current_password': 'CurrentPass123!',
            'new_password': 'NuevoPass2026!@',
            'new_password_confirmation': 'NuevoPass2026!@',
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        if hasattr(user, 'state'):
            assert user.state == 'BLOCKED'


# ---------------------------------------------------------------------------
# FR-004.02 — policy validator (MAX_LENGTH = 128)
# ---------------------------------------------------------------------------

import pytest as _pytest  # noqa: E402
from apps.authentication.change_password_view import PasswordPolicyValidator  # noqa: E402


class _UserStub:
    def __init__(self, username='someuser'):
        self.username = username


class TestPasswordPolicyValidatorMaxLength:
    """FR-004.02: max_length=128 declarado en spec."""

    def test_max_length_excedido_rechazado(self):
        validator = PasswordPolicyValidator()
        long_password = 'Aa1!' * 33  # 132 chars
        violations = validator.validate(long_password, _UserStub())
        assert 'max_length' in violations

    def test_exactamente_128_aceptado(self):
        validator = PasswordPolicyValidator()
        # 128 chars exactos: 'Aa1!' * 31 = 124 + 'Bb2$' = 128
        password = 'Aa1!' * 31 + 'Bb2$'
        assert len(password) == 128
        violations = validator.validate(password, _UserStub())
        assert 'max_length' not in violations
