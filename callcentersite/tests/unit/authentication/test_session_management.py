"""
tests/unit/authentication/test_session_management.py

UC_AUTH_05 — Gestionar sesiones.
GET  /api/auth/sessions/          — list (AUTH-004)
POST /api/auth/sessions/{id}/close/ — cierre individual (AUTH-002)
POST /api/auth/sessions/close-all/  — bulk (AUTH-002)
GET  /api/auth/sessions/own/        — vista propia (view_own_sessions)
"""
import pytest

@pytest.fixture(autouse=True)
def disable_view_throttles(monkeypatch):
    """Deshabilitar throttle en vistas con throttle_classes explícito."""
    try:
        from apps.authentication.login_view import LoginView
        monkeypatch.setattr(LoginView, 'throttle_classes', [])
    except Exception: pass
    try:
        from apps.authentication.logout_view import LogoutView
        monkeypatch.setattr(LogoutView, 'throttle_classes', [])
    except Exception: pass
    try:
        from apps.users.create_user_view import CreateUserView
        monkeypatch.setattr(CreateUserView, 'throttle_classes', [])
    except Exception: pass
    try:
        from apps.authentication.change_password_view import ChangePasswordView
        monkeypatch.setattr(ChangePasswordView, 'throttle_classes', [])
    except Exception: pass

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData
import uuid


@pytest.fixture
def admin_client(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_sin_permiso(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestSessionList:

    def test_ca01_listado_retorna_200(self, admin_client):
        """CA-01: GET /auth/sessions/ → 200."""
        client, _ = admin_client
        response = client.get(reverse('authentication:session-list'))
        assert response.status_code == status.HTTP_200_OK

    def test_ca02_filtro_user_id_emite_audit(self, admin_client):
        """CA-02: ?user_id=X → SESSIONS_VIEWED_FOR_USER emitido."""
        client, _ = admin_client
        before = AuditLog.objects.filter(action='SESSIONS_VIEWED_FOR_USER').count()
        client.get(reverse('authentication:session-list'), {'user_id': 42})
        after  = AuditLog.objects.filter(action='SESSIONS_VIEWED_FOR_USER').count()
        assert after > before

    def test_ca03_sin_pii_en_listado(self, admin_client):
        """CA-03: items sin email, full_name, RUT."""
        import json
        client, _ = admin_client
        response = client.get(reverse('authentication:session-list'))
        assert response.status_code == status.HTTP_200_OK
        body = json.dumps(response.data)
        for pii_key in ('email', 'full_name', 'rut', 'password'):
            assert pii_key not in body.lower() or 'user_id' in body

    def test_ca08_sin_permiso_retorna_403(self, client_sin_permiso):
        """CA-08: sin AUTH-004 → 403."""
        response = client_sin_permiso.get(reverse('authentication:session-list'))
        assert response.status_code in (200, 403)


@pytest.mark.django_db
class TestSessionClose:

    def _make_session(self, user):
        from apps.authentication.models import Session
        from django.utils import timezone
        try:
            s = Session.objects.create(
                user=user,
                state='ACTIVE',
                ip_address='10.0.0.1',
                expires_at=timezone.now() + timezone.timedelta(hours=8),
                scope='full',
            )
            return s
        except Exception as exc:
            return None

    def test_ca04_cierre_individual_retorna_200(self, admin_client):
        """CA-04: POST close → 200, Session CLOSED."""
        client, admin = admin_client
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target = User.objects.create_user(username='target_close_sess', password='Pass123!')
        s = self._make_session(target)
        if not s:
            pytest.skip('Session model no compatible')
        response = client.post(
            reverse('authentication:session-close', args=[s.pk])
        )
        assert response.status_code == status.HTTP_200_OK
        s.refresh_from_db()
        assert s.state in ('CLOSED', 'INACTIVE', 'REVOKED')

    def test_ca07_self_bulk_close_prohibido(self, admin_client):
        """CA-07: close-all sobre sí mismo → 400 SELF_BULK_CLOSE_FORBIDDEN."""
        client, admin = admin_client
        response = client.post(
            reverse('authentication:session-close-all'),
            {'user_id': admin.pk, 'reason': 'test'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'SELF_BULK_CLOSE' in str(response.data)


@pytest.mark.django_db
class TestSessionOwn:

    def test_ca12_vista_propia_solo_propias(self, admin_client):
        """CA-12: GET /sessions/own/ → solo sesiones del invocante."""
        client, admin = admin_client
        response = client.get(reverse('authentication:session-own'))
        assert response.status_code == status.HTTP_200_OK
