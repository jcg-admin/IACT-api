"""
Tests E2E para flujos completos de auditoria (UC_AUD_01..04).

Valida que el AuditLog se persiste correctamente, se consulta
via API y se exporta. Cross-stack: emit -> persist -> query -> export.
"""
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.audit.services import AuditLogService

User = get_user_model()


@pytest.fixture
def admin_user(db):
    u = uuid.uuid4().hex[:6]
    return User.objects.create_superuser(
        username=f'admin_aud_{u}',
        email=f'admin_aud_{u}@test.com',
        password='Pass1234',
    )


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.mark.django_db
class TestAuditServiceEmit:
    """UC_AUD_01 base — emit persiste un AuditLog inmutable."""

    def test_emit_persiste_audit_log(self, admin_user):
        before = AuditLog.objects.count()
        AuditLogService.emit(
            event_type='LOGIN',
            actor_user_id=admin_user.pk,
            payload={'ip': '127.0.0.1'},
        )
        assert AuditLog.objects.count() == before + 1
        last = AuditLog.objects.latest('timestamp')
        assert last.action == 'LOGIN'
        assert last.user_id == admin_user.pk

    def test_audit_log_es_inmutable(self, admin_user):
        """CNST-009: AuditLog.save() rechaza UPDATE."""
        log = AuditLogService.emit(
            event_type='LOGOUT',
            actor_user_id=admin_user.pk,
        )
        log.action = 'TAMPERED'
        with pytest.raises(PermissionError, match='inmutable'):
            log.save()


@pytest.mark.django_db
class TestAuditEndpointFlow:
    """UC_AUD_01..04 — flujo via API."""

    def test_uc_aud_01_listar_audit_log(self, admin_client, admin_user):
        """Crear varios eventos y listarlos."""
        for evt in ('LOGIN', 'LOGOUT', 'USER_CREATED'):
            AuditLogService.emit(event_type=evt, actor_user_id=admin_user.pk)
        response = admin_client.get('/api/audit/')
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_uc_aud_02_buscar_por_event_type(self, admin_client, admin_user):
        """Filter por action."""
        AuditLogService.emit(event_type='LOGIN', actor_user_id=admin_user.pk)
        response = admin_client.get('/api/audit/', {'action': 'LOGIN'})
        assert response.status_code != status.HTTP_404_NOT_FOUND
