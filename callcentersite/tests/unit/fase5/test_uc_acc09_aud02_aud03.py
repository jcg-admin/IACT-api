"""
tests/unit/fase5/test_uc_acc09_aud02_aud03.py

UC_ACC_09 — Auditar Cambios de Acceso.  GET /api/access/audit/
UC_AUD_02 — Buscar en Auditoría.        POST /api/audit/search/
UC_AUD_03 — Exportar Auditoría.         POST /api/audit/export/
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def client_acc09(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_sin(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


# ============================================================================
# UC_ACC_09 — Auditar Cambios de Acceso
# ============================================================================

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


# ============================================================================
# UC_AUD_02 — Buscar en Auditoría
# ============================================================================

def _aud_search_url():
    return reverse('audit:audit-search')


@pytest.mark.django_db
class TestAuditSearchEndpoint:

    def test_it01_search_basico_retorna_200(self, client_acc09):
        """CA-01: POST con query → 200."""
        client, _ = client_acc09
        response = client.post(_aud_search_url(), {
            'q': 'LOGIN',
            'date_from': '2026-04-01',
            'date_to': '2026-04-30',
        }, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_it02_range_mayor_90_retorna_400(self, client_acc09):
        """CA-02: range > 90 días → 400."""
        client, _ = client_acc09
        response = client.post(_aud_search_url(), {
            'q': 'test',
            'date_from': '2026-01-01',
            'date_to': '2026-05-01',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it03_range_obligatorio(self, client_acc09):
        """CA-03: date_from ausente → 400."""
        client, _ = client_acc09
        response = client.post(_aud_search_url(), {'q': 'test'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it05_meta_audit_emitido(self, client_acc09):
        """CA-06: AUDIT_SEARCH_QUERIED emitido."""
        client, _ = client_acc09
        client.post(_aud_search_url(), {
            'q': 'LOGIN', 'date_from': '2026-04-01', 'date_to': '2026-04-30',
        }, format='json')
        assert AuditLog.objects.filter(action='AUDIT_SEARCH_QUERIED').exists()

    def test_sec_sin_permiso_retorna_403(self, client_sin):
        """CA-08: sin AUD-002 → 403."""
        response = client_sin.post(_aud_search_url(), {
            'q': 'test', 'date_from': '2026-04-01', 'date_to': '2026-04-30',
        }, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# UC_AUD_03 — Exportar Auditoría
# ============================================================================

def _aud_export_url():
    return reverse('audit:audit-export')


@pytest.mark.django_db
class TestAuditExportEndpoint:

    def test_it01_encolar_retorna_202(self, client_acc09):
        """CA-01: POST → 202 + job_id."""
        client, _ = client_acc09
        response = client.post(_aud_export_url(), {
            'date_from': '2026-04-01',
            'date_to': '2026-04-30',
            'format': 'csv',
        }, format='json')
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert 'job_id' in response.data

    def test_it04_mayor_5m_filas_retorna_400(self, client_acc09):
        """CA-04: estimated_rows > 5M → 400."""
        client, _ = client_acc09
        response = client.post(_aud_export_url(), {
            'date_from': '2000-01-01',
            'date_to': '2026-05-01',
            'format': 'csv',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it07_audit_export_queued_emitido(self, client_acc09):
        """CA-08: AUDIT_EXPORT_QUEUED emitido."""
        client, _ = client_acc09
        client.post(_aud_export_url(), {
            'date_from': '2026-04-01',
            'date_to': '2026-04-30',
            'format': 'csv',
        }, format='json')
        assert AuditLog.objects.filter(action='AUDIT_EXPORT_QUEUED').exists()

    def test_sec_no_email_externo(self, client_acc09):
        """CA-07: CNST-001 — sin email externo."""
        from unittest.mock import patch
        client, _ = client_acc09
        with patch('smtplib.SMTP') as mock_smtp:
            client.post(_aud_export_url(), {
                'date_from': '2026-04-01', 'date_to': '2026-04-30', 'format': 'csv',
            }, format='json')
        mock_smtp.assert_not_called()

    def test_sec_sin_permiso_retorna_403(self, client_sin):
        """CA-09: sin AUD-003 → 403."""
        response = client_sin.post(_aud_export_url(), {
            'date_from': '2026-04-01', 'date_to': '2026-04-30', 'format': 'csv',
        }, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
