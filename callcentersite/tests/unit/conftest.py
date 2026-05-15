"""
tests/unit/conftest.py

Fixtures compartidas para todos los tests unit/.
Reemplaza los conftest.py eliminados de fase0/, fase1/, fase2/
durante la remediación DT-NAMING-001 (commit d178bfc).

H-F6-GRP-GA-001: throttle deshabilitado globalmente en fase0_testing settings.
"""
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from io import StringIO
from django.core.management import call_command


@pytest.fixture
def api_client():
    """Cliente API sin autenticación."""
    return APIClient()


@pytest.fixture
def db_with_catalog(db):
    """BD con catálogo de funciones y access groups populados."""
    call_command('create_functions', stdout=StringIO())
    call_command('create_access_groups', stdout=StringIO())
    return db


@pytest.fixture
def admin_with_catalog(db_with_catalog):
    """Usuario admin con AGR-006 (user_admin_group) — catálogo ya populado."""
    User = get_user_model()
    from apps.access.models import AccessGroup, UserAccessGroup
    user = User.objects.create_user(
        username='admin_conftest',
        password='AdminPass123!',
        state='ACTIVE',
        first_login=False,
    )
    try:
        agr006 = AccessGroup.objects.get(code='AGR-006')
        UserAccessGroup.objects.get_or_create(user=user, access_group=agr006)
    except AccessGroup.DoesNotExist:
        pass
    return user


def _make_admin_client():
    """Helper (no fixture) — crea un admin con AGR-006 y retorna (APIClient, User)."""
    import uuid
    User = get_user_model()
    from apps.access.models import AccessGroup, UserAccessGroup
    user = User.objects.create_user(
        username=f'admin_{uuid.uuid4().hex[:8]}',
        password='AdminPass123!',
        state='ACTIVE',
        first_login=False,
    )
    try:
        agr006 = AccessGroup.objects.get(code='AGR-006')
        UserAccessGroup.objects.get_or_create(user=user, access_group=agr006)
    except AccessGroup.DoesNotExist:
        pass
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_admin(db_with_catalog):
    """Tupla (APIClient autenticado, admin User con AGR-006)."""
    return _make_admin_client()


@pytest.fixture
def client_sin(db):
    """APIClient autenticado con usuario sin permisos RBAC."""
    User = get_user_model()
    import uuid
    user = User.objects.create_user(
        username=f'noperm_{uuid.uuid4().hex[:6]}',
        password='NoPermPass123!',
        state='ACTIVE',
        first_login=False,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def client_acc09(db_with_catalog):
    """APIClient con función ACC-013 (access_audit_view) para UC_ACC_09."""
    import uuid
    User = get_user_model()
    from apps.access.models import AccessGroup, UserAccessGroup, Function, UserPermission
    user = User.objects.create_user(
        username=f'acc09_{uuid.uuid4().hex[:8]}',
        password='AdminPass123!',
        state='ACTIVE',
        first_login=False,
    )
    # Asignar ACC-013 directamente via UserPermission
    for code in ['ACC-013', 'AUD-001', 'AUD-002', 'AUD-003', 'AUD-005']:
        try:
            fn = Function.objects.get(code=code)
            UserPermission.objects.get_or_create(user=user, function=fn)
        except Function.DoesNotExist:
            pass
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_aud04(db_with_catalog):
    """APIClient con funciones AUD para UC_AUD_04."""
    import uuid
    User = get_user_model()
    from apps.access.models import Function, UserPermission
    user = User.objects.create_user(
        username=f'aud04_{uuid.uuid4().hex[:8]}',
        password='AdminPass123!',
        state='ACTIVE',
        first_login=False,
    )
    for code in ['AUD-001', 'AUD-002', 'AUD-003', 'AUD-004', 'AUD-005', 'ACC-013']:
        try:
            fn = Function.objects.get(code=code)
            UserPermission.objects.get_or_create(user=user, function=fn)
        except Function.DoesNotExist:
            pass
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_alr05(db_with_catalog):
    return _make_admin_client()


@pytest.fixture
def client_log03(db_with_catalog):
    return _make_admin_client()


@pytest.fixture
def client_rpt09(db_with_catalog):
    return _make_admin_client()
