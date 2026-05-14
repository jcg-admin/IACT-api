"""
tests/unit/authentication/test_login_jwt.py

UC_AUTH_01 — Iniciar Sesión. JWT + BlacklistedToken. 16 CAs del corpus.
"""
import pytest
from unittest import mock
from datetime import timedelta
from django.utils import timezone

LOGIN_URL = '/api/auth/login/'


def make_active_user(username, password, state='ACTIVE',
                     first_login=False, password_expires_at=None):
    """Helper de testing.rst § 12.5 — crea user listo para login."""
    from apps.users.models import User
    user = User.objects.create_user(
        username=username, password=password,
        state=state, first_login=first_login,
    )
    if password_expires_at is not None:
        user.password_expires_at = password_expires_at
        user.save(update_fields=['password_expires_at'])
    return user


def add_to_group(user, group_code='AGR-001'):
    """Asigna un AccessGroup al usuario para que tenga permisos."""
    from apps.access.models import AccessGroup, UserAccessGroup
    from django.core.management import call_command
    from io import StringIO
    call_command('create_functions', stdout=StringIO())
    call_command('create_access_groups', stdout=StringIO())
    agr = AccessGroup.objects.get(code=group_code)
    UserAccessGroup.objects.get_or_create(user=user, access_group=agr)


# CA-01: Login exitoso — flujo principal
@pytest.mark.django_db
def test_login_happy_path(api_client):
    """CA-01: User ACTIVE con permisos, sin Sessions previas."""
    user = make_active_user('alice', 'S3cret!XY')
    add_to_group(user)

    resp = api_client.post(LOGIN_URL,
                           {'username': 'alice', 'password': 'S3cret!XY'}, format='json')

    assert resp.status_code == 200
    d = resp.data
    assert d['tokens']['access']
    assert d['tokens']['refresh']
    assert d['user']['username'] == 'alice'
    assert d['next_step'] is None
    assert d['warning'] is None
    assert d['session']['session_id']
    assert d['session']['expires_at']

    from apps.authentication.models import Session
    assert Session.objects.filter(user=user, state='ACTIVE').count() == 1

    from apps.audit.models import AuditLog
    assert AuditLog.objects.filter(action='LOGIN').exists()

    user.refresh_from_db()
    assert user.last_login_at is not None

    # CNST-026: no PII en AuditLog
    audit = AuditLog.objects.get(action='LOGIN')
    assert 'S3cret!XY' not in str(audit.details)


# CA-02: Sesión única (BR-005)
@pytest.mark.django_db
def test_login_supersedes_previous_session(api_client):
    """CA-02: Sesión previa → CLOSED + SUPERSEDED."""
    from apps.authentication.models import Session
    from apps.audit.models import AuditLog

    user = make_active_user('bob', 'S3cret!XY')
    add_to_group(user)
    prev = Session.objects.create(
        user=user, state='ACTIVE',
        expires_at=timezone.now() + timedelta(minutes=15),
    )

    api_client.post(LOGIN_URL,
                    {'username': 'bob', 'password': 'S3cret!XY'}, format='json')

    prev.refresh_from_db()
    assert prev.state == 'CLOSED'
    assert prev.close_reason == 'SUPERSEDED'
    assert prev.closed_at is not None
    assert AuditLog.objects.filter(action='SESSION_CLOSED').exists()


# CA-03: Rollback atómico si AuditEvent falla
@pytest.mark.django_db
def test_login_rollback_on_db_failure(api_client):
    """CA-03: transacción atómica — si AuditEvent falla, rollback."""
    from apps.authentication.models import Session

    user = make_active_user('carol', 'S3cret!XY')

    with mock.patch(
        'apps.audit.services.AuditLogService.emit',
        side_effect=Exception('DB failure'),
    ):
        resp = api_client.post(LOGIN_URL,
                               {'username': 'carol', 'password': 'S3cret!XY'}, format='json')

    assert resp.status_code == 503
    assert resp.data['error']['code'] == 'DB_TRANSIENT_ERROR'
    assert Session.objects.filter(user=user).count() == 0


# CA-04: first_login → next_step = 'change_password'
@pytest.mark.django_db
def test_login_first_login_change_password(api_client):
    """CA-04: FA-01 — first_login=True → next_step y scope=restricted."""
    from apps.authentication.models import Session

    user = make_active_user('dan', 'temp-Pwd1!', first_login=True)
    resp = api_client.post(LOGIN_URL,
                           {'username': 'dan', 'password': 'temp-Pwd1!'}, format='json')

    assert resp.status_code == 200
    assert resp.data['next_step'] == 'change_password'

    s = Session.objects.get(user=user, state='ACTIVE')
    assert s.scope == 'restricted'
    user.refresh_from_db()
    assert user.first_login is True  # sigue True hasta UC_AUTH_04


# CA-05: password próximo a expirar
@pytest.mark.django_db
def test_login_warns_password_expiring(api_client):
    """CA-05: FA-02 — warning.type='password_expiring'."""
    user = make_active_user('eve', 'S3cret!XY',
                            password_expires_at=timezone.now() + timedelta(days=2))
    add_to_group(user)
    resp = api_client.post(LOGIN_URL,
                           {'username': 'eve', 'password': 'S3cret!XY'}, format='json')

    assert resp.status_code == 200
    assert resp.data['warning']['type'] == 'password_expiring'
    assert resp.data['next_step'] is None


# CA-06: sin permisos → warning
@pytest.mark.django_db
def test_login_warns_no_permissions(api_client):
    """CA-06: FA-04 — sin Assignments → warning.type='no_permissions'."""
    from apps.audit.models import AuditLog

    user = make_active_user('frank', 'S3cret!XY')
    resp = api_client.post(LOGIN_URL,
                           {'username': 'frank', 'password': 'S3cret!XY'}, format='json')

    assert resp.status_code == 200
    assert resp.data['warning']['type'] == 'no_permissions'
    assert AuditLog.objects.filter(action='LOGIN_NO_PERMISSIONS').exists()


# CA-07: username inexistente → 401
@pytest.mark.django_db
def test_login_unknown_username(api_client):
    """CA-07: EX-01 — 401 INVALID_CREDENTIALS."""
    resp = api_client.post(LOGIN_URL,
                           {'username': 'nonexistent', 'password': 'whatever12!'}, format='json')
    assert resp.status_code == 401
    assert resp.data['error']['code'] == 'INVALID_CREDENTIALS'


# CA-08: password incorrecto → 401
@pytest.mark.django_db
def test_login_wrong_password(api_client):
    """CA-08: EX-02 — 401 INVALID_CREDENTIALS."""
    make_active_user('gina', 'S3cret!XY')
    resp = api_client.post(LOGIN_URL,
                           {'username': 'gina', 'password': 'wrong-Pwd!'}, format='json')
    assert resp.status_code == 401
    assert resp.data['error']['code'] == 'INVALID_CREDENTIALS'


# CA-09: cuenta bloqueada → 403
@pytest.mark.django_db
def test_login_blocked_account(api_client):
    """CA-09: EX-03 — state=BLOCKED → 403 ACCOUNT_BLOCKED + AuditLog."""
    from apps.audit.models import AuditLog

    make_active_user('hank', 'S3cret!XY', state='BLOCKED')
    resp = api_client.post(LOGIN_URL,
                           {'username': 'hank', 'password': 'S3cret!XY'}, format='json')

    assert resp.status_code == 403
    assert resp.data['error']['code'] == 'ACCOUNT_BLOCKED'
    assert AuditLog.objects.filter(action='BLOCKED_LOGIN_ATTEMPT').exists()


# CA-10: cuenta inactiva → 403
@pytest.mark.django_db
def test_login_inactive_account(api_client):
    """CA-10: EX-04 — state=INACTIVE → 403 ACCOUNT_INACTIVE."""
    make_active_user('ivan', 'S3cret!XY', state='INACTIVE')
    resp = api_client.post(LOGIN_URL,
                           {'username': 'ivan', 'password': 'S3cret!XY'}, format='json')
    assert resp.status_code == 403
    assert resp.data['error']['code'] == 'ACCOUNT_INACTIVE'


# CA-11: BR-015 — 5 intentos → bloqueo
@pytest.mark.django_db
def test_login_lockout_after_5_attempts(api_client):
    """CA-11: BR-015 — 5 intentos fallidos → state=BLOCKED → 403."""
    make_active_user('jack', 'S3cret!XY')
    for _ in range(5):
        api_client.post(LOGIN_URL,
                        {'username': 'jack', 'password': 'WRONG!123'}, format='json')

    from apps.users.models import User
    jack = User.objects.get(username='jack')
    assert jack.state == 'BLOCKED'

    resp = api_client.post(LOGIN_URL,
                           {'username': 'jack', 'password': 'S3cret!XY'}, format='json')
    assert resp.status_code == 403
    assert resp.data['error']['code'] == 'ACCOUNT_BLOCKED'


# CA-12: payload inválido → 400
@pytest.mark.django_db
def test_login_validation_error(api_client):
    """CA-12: EX-06 — campos vacíos → 400 VALIDATION_ERROR con fields."""
    resp = api_client.post(LOGIN_URL,
                           {'username': '', 'password': 'sh'}, format='json')
    assert resp.status_code == 400
    assert resp.data['error']['code'] == 'VALIDATION_ERROR'
    assert 'username' in resp.data['error'].get('fields', {})


# CA-14: AuditLog inmutable
@pytest.mark.django_db
def test_audit_event_immutable(api_client):
    """CA-14: CNST-025 — AuditLog no puede modificarse ni eliminarse."""
    from apps.audit.models import AuditLog

    make_active_user('kate', 'S3cret!XY')
    api_client.post(LOGIN_URL,
                    {'username': 'kate', 'password': 'S3cret!XY'}, format='json')

    audit = AuditLog.objects.first()
    with pytest.raises(PermissionError):
        audit.action = 'TAMPERED'
        audit.save()
    with pytest.raises(PermissionError):
        audit.delete()


# CA-15b: no PII en AuditLog
@pytest.mark.django_db
def test_no_pii_in_audit_payload(api_client):
    """CA-15b: CNST-026 — password no aparece en AuditEvent."""
    from apps.audit.models import AuditLog

    make_active_user('laura', 'TopSecret!XYZ')
    api_client.post(LOGIN_URL,
                    {'username': 'laura', 'password': 'TopSecret!XYZ'}, format='json')

    for ev in AuditLog.objects.all():
        assert 'TopSecret!XYZ' not in str(ev.details)
