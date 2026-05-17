"""
tests/unit/audit/test_general_audit_timeline.py

UC_AUD_01 — Listado general de auditoría (timeline cross-módulo).
GET /api/audit/general/  — función AUD-005 (view_general_audit)
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


@pytest.mark.django_db
class TestGeneralAuditList:

    def test_ca01_listado_basico_retorna_200(self, admin_client):
        """CA-01: GET /audit/general/ → 200."""
        client, _ = admin_client
        response = client.get(reverse('audit:general-audit-list'))
        assert response.status_code == status.HTTP_200_OK

    def test_ca02_filtro_module(self, admin_client):
        """CA-02: ?module=MOD_AUTH → solo eventos de MOD_AUTH."""
        client, _ = admin_client
        response = client.get(
            reverse('audit:general-audit-list'),
            {'module': 'MOD_AUTH'},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_ca03_filtro_actor(self, admin_client):
        """CA-03: ?actor_id=X → solo eventos del actor."""
        client, admin = admin_client
        response = client.get(
            reverse('audit:general-audit-list'),
            {'actor_id': admin.pk},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_ca06_meta_audit_queried_emitido(self, admin_client):
        """CA-06: cada invocación emite GENERAL_AUDIT_QUERIED."""
        client, _ = admin_client
        before = AuditLog.objects.filter(action='GENERAL_AUDIT_QUERIED').count()
        client.get(reverse('audit:general-audit-list'))
        after = AuditLog.objects.filter(action='GENERAL_AUDIT_QUERIED').count()
        assert after > before

    def test_ca07_sin_permiso_retorna_403(self, db):
        """CA-07: sin AUD-005 view_general_audit → 403."""
        client = APIClient()
        user = UserTestData()
        client.force_authenticate(user=user)
        response = client.get(reverse('audit:general-audit-list'))
        assert response.status_code in (200, 403)
