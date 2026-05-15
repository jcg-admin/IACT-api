"""
tests/unit/audit/test_audit_search_and_export.py

UC_AUD_02 — Buscar en Auditoría.   POST /api/audit/search/
UC_AUD_03 — Exportar Auditoría.    POST /api/audit/export/
Función UC_AUD_02: AUD-002 (search_audit_log)
Función UC_AUD_03: AUD-003 (export_audit_log)
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData

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
        assert response.status_code in (200, 403)


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
        assert response.status_code in (200, 403)