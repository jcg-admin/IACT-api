"""
tests/unit/fase2/test_uc_auth_02_logout.py

UC_AUTH_02 — Cerrar Sesión.
Fuente: uc-auth-02/criterios-aceptacion.rst § 9
"""
import pytest
from datetime import timedelta
from django.utils import timezone

LOGOUT_URL = '/api/auth/logout/'


def make_session(user):
    from apps.authentication.models import Session
    return Session.objects.create(
        user=user, state='ACTIVE',
        expires_at=timezone.now() + timedelta(minutes=15),
    )


@pytest.mark.django_db
def test_logout_happy_path(api_client):
    """CA-01: Session CLOSED, close_reason=USER_LOGOUT, AuditEvent LOGOUT."""
    from apps.users.models import User
    from apps.authentication.models import Session
    from apps.audit.models import AuditLog

    user = User.objects.create_user(username='lu_alice', password='Pass123!', state='ACTIVE')
    s = make_session(user)
    api_client.force_authenticate(user=user)

    resp = api_client.post(LOGOUT_URL, {'refresh_token': 'tok'}, format='json')

    assert resp.status_code == 200
    assert resp.data['message'] == 'Sesión cerrada'
    assert resp.data['logout_at']
    s.refresh_from_db()
    assert s.state == 'CLOSED'
    assert s.close_reason == 'USER_LOGOUT'
    assert s.closed_at is not None
    assert AuditLog.objects.filter(action='LOGOUT').exists()


@pytest.mark.django_db
def test_logout_idempotent_no_active_session(api_client):
    """CA-02: sin Session ACTIVE → 200 con LOGOUT_REPLAY."""
    from apps.users.models import User
    from apps.audit.models import AuditLog

    user = User.objects.create_user(username='lu_bob', password='Pass123!', state='ACTIVE')
    api_client.force_authenticate(user=user)

    resp = api_client.post(LOGOUT_URL, {}, format='json')

    assert resp.status_code == 200
    assert 'cerrada' in resp.data['message'].lower()
    assert AuditLog.objects.filter(action='LOGOUT_REPLAY').exists()


@pytest.mark.django_db
def test_logout_without_refresh_token(api_client):
    """CA-03: FA-01 — sin refresh_token, Session cierra igual."""
    from apps.users.models import User

    user = User.objects.create_user(username='lu_carol', password='Pass123!', state='ACTIVE')
    make_session(user)
    api_client.force_authenticate(user=user)

    resp = api_client.post(LOGOUT_URL, {}, format='json')

    assert resp.status_code == 200
    from apps.authentication.models import Session
    s = Session.objects.get(user=user)
    assert s.state == 'CLOSED'


@pytest.mark.django_db
def test_logout_atomicity_session_stays_active_on_audit_failure(api_client):
    """CA-06/CA-07: si AuditEvent falla → rollback, Session permanece ACTIVE."""
    from unittest import mock
    from apps.users.models import User
    from apps.authentication.models import Session

    user = User.objects.create_user(username='lu_dan', password='Pass123!', state='ACTIVE')
    s = make_session(user)
    api_client.force_authenticate(user=user)

    with mock.patch(
        'apps.audit.services.AuditLogService.emit',
        side_effect=Exception('BD failure'),
    ):
        resp = api_client.post(LOGOUT_URL, {}, format='json')

    assert resp.status_code == 500
    s.refresh_from_db()
    assert s.state == 'ACTIVE'


@pytest.mark.django_db
def test_logout_no_pii_in_audit(api_client):
    """CA-14: CNST-026 — no PII en AuditEvent."""
    from apps.users.models import User
    from apps.audit.models import AuditLog

    user = User.objects.create_user(username='lu_eve', password='SecretPass123!', state='ACTIVE')
    make_session(user)
    api_client.force_authenticate(user=user)

    api_client.post(LOGOUT_URL, {}, format='json')

    for ev in AuditLog.objects.filter(action='LOGOUT'):
        assert 'SecretPass123!' not in str(ev.details)
        assert user.email not in str(ev.details)


@pytest.mark.django_db
def test_logout_requires_authentication(api_client):
    """CA-04: sin token → 401."""
    resp = api_client.post(LOGOUT_URL, {}, format='json')
    assert resp.status_code == 401
