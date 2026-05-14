"""
tests/unit/access/test_access_audit.py

UC_ACC_09 — Auditar Cambios de Acceso.
GET /api/access/audit/
GET /api/access/audit/{event_id}/
GET /api/access/audit/aggregations/
Función: ACC-013 (view_access_audit)
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.audit.access_audit_service import ACCESS_EVENT_TYPES
from tests.test_data.user_test_data import AdminUserTestData, UserTestData

def _acc_audit_url():
    return reverse('access:access-audit-list')

def _acc_audit_agg_url():
    return reverse('access:access-audit-aggregations')


class TestAccessScopeFilter:
    """UT: solo eventos de MOD_Access."""

    def test_scope_filter_solo_access_events(self):
        from apps.audit.access_audit_service import AccessScopeFilter, ACCESS_EVENT_TYPES
        for et in ACCESS_EVENT_TYPES:
            assert AccessScopeFilter.is_access_event(et)
        assert not AccessScopeFilter.is_access_event('LOGIN')
        assert not AccessScopeFilter.is_access_event('REPORT_EXPORT_QUEUED')


class TestAccessFilterValidator:
    """UT: anti-SQLi en ordering."""

    def test_ordering_invalido_rechazado(self):
        from apps.audit.access_audit_service import AccessFilterValidator
        with pytest.raises(ValueError, match='ordering'):
            AccessFilterValidator.validate_ordering("'; DROP TABLE users;--")

    def test_ordering_valido_aceptado(self):
        from apps.audit.access_audit_service import AccessFilterValidator
        AccessFilterValidator.validate_ordering('occurred_at')
        AccessFilterValidator.validate_ordering('-occurred_at')


@pytest.mark.django_db
class TestAccessAuditEndpoint:

    def test_it01_list_retorna_200(self, client_acc09):
        """CA-01: GET → 200 con results."""
        client, _ = client_acc09
        response = client.get(_acc_audit_url())
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_it02_solo_eventos_access(self, client_acc09):
        """CA-02: solo event_types de ACCESS_EVENT_TYPES."""
        from apps.audit.access_audit_service import ACCESS_EVENT_TYPES
        client, _ = client_acc09
        # Crear un evento ACCESS y uno AUTH
        AuditLog.objects.create(action='FUNCTIONS_ASSIGNED', user=None, resource='test', result='SUCCESS')
        AuditLog.objects.create(action='LOGIN', user=None, resource='test', result='SUCCESS')
        response = client.get(_acc_audit_url())
        for item in response.data.get('results', []):
            assert item.get('action') in ACCESS_EVENT_TYPES or item.get('event_type') in ACCESS_EVENT_TYPES

    def test_it03_target_user_id_emite_audit(self, client_acc09):
        """CA-03: ?target_user_id=42 → ACCESS_AUDIT_VIEWED emitido."""
        client, _ = client_acc09
        before = AuditLog.objects.filter(action='ACCESS_AUDIT_VIEWED').count()
        client.get(_acc_audit_url(), {'target_user_id': '42'})
        assert AuditLog.objects.filter(action='ACCESS_AUDIT_VIEWED').count() > before

    def test_it04_sin_target_no_emite_audit(self, client_acc09):
        """CA-04: sin target_user_id → ZERO ACCESS_AUDIT_VIEWED."""
        client, _ = client_acc09
        before = AuditLog.objects.filter(action='ACCESS_AUDIT_VIEWED').count()
        client.get(_acc_audit_url())
        assert AuditLog.objects.filter(action='ACCESS_AUDIT_VIEWED').count() == before

    def test_it06_ordering_sqli_retorna_400(self, client_acc09):
        """CA-07: ordering con SQL injection → 400 BAD_FILTER."""
        client, _ = client_acc09
        response = client.get(_acc_audit_url(), {'ordering': "'; DROP TABLE users;--"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it09_aggregations_sin_audit(self, client_acc09):
        """CA-10: aggregations → 200, ZERO AuditEvent generado."""
        client, _ = client_acc09
        before = AuditLog.objects.count()
        response = client.get(_acc_audit_agg_url(), {'group_by': 'event_type'})
        assert response.status_code == status.HTTP_200_OK
        assert AuditLog.objects.count() == before

    def test_sec_sin_permiso_retorna_403(self, client_sin):
        """CA-05: sin ACC-012 → 403."""
        response = client_sin.get(_acc_audit_url())
        assert response.status_code == status.HTTP_403_FORBIDDEN