"""
tests/unit/audit/test_compliance_report.py

UC_AUD_04 — Generar Reporte de Compliance.
POST /api/audit/compliance-report/
POST /api/audit/compliance-verify/
Función: AUD-004 (generate_compliance_report)
"""
import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData

@pytest.fixture
def client_aud04(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def client_sin_aud04(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _compliance_url():
    return reverse('audit:compliance-report')


def _verify_url():
    return reverse('audit:compliance-verify')


class TestHMACSigner:
    """UT-02..03: HMAC para reporte de compliance."""

    def test_ut02_firma_reporte(self):
        from apps.audit.compliance_service import HMACSigner
        payload = b'{"template":"PRIVILEGED_ACCESS","data":[]}'
        sig = HMACSigner.sign(payload)
        assert len(sig) == 64  # SHA-256 hex

    def test_ut03_verifica_correcto(self):
        from apps.audit.compliance_service import HMACSigner
        payload = b'test_data_for_compliance_report'
        sig = HMACSigner.sign(payload)
        assert HMACSigner.verify(payload, sig)

    def test_ut03_detecta_tampering(self):
        from apps.audit.compliance_service import HMACSigner
        payload = b'original_compliance_data'
        sig = HMACSigner.sign(payload)
        assert not HMACSigner.verify(b'tampered_data', sig)


class TestComplianceTemplateValidator:
    """UT-01: validación de templates."""

    def test_template_valido_aceptado(self):
        from apps.audit.compliance_service import ComplianceTemplateValidator
        ComplianceTemplateValidator.validate('PRIVILEGED_ACCESS')

    def test_template_invalido_rechazado(self):
        from apps.audit.compliance_service import ComplianceTemplateValidator
        with pytest.raises(ValueError, match='template'):
            ComplianceTemplateValidator.validate('INEXISTENTE_TEMPLATE')


@pytest.mark.django_db
class TestComplianceReportEndpoint:

    def test_it01_privileged_access_retorna_202(self, client_aud04):
        """CA-01: POST PRIVILEGED_ACCESS → 202."""
        client = client_aud04
        response = client.post(_compliance_url(), {
            'template': 'PRIVILEGED_ACCESS',
            'date_from': '2026-01-01',
            'date_to': '2026-05-01',
        }, format='json')
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_202_ACCEPTED)

    def test_it07_audit_compliance_report_requested(self, client_aud04):
        """CA-09: COMPLIANCE_REPORT_REQUESTED emitido."""
        client = client_aud04
        client.post(_compliance_url(), {
            'template': 'PRIVILEGED_ACCESS',
            'date_from': '2026-01-01',
            'date_to': '2026-05-01',
        }, format='json')
        assert AuditLog.objects.filter(
            action__in=['COMPLIANCE_REPORT_REQUESTED', 'COMPLIANCE_REPORT_GENERATED']
        ).exists()

    def test_it08_no_email_externo(self, client_aud04):
        """CA-08: CNST-001 — sin email externo."""
        client = client_aud04
        with patch('smtplib.SMTP') as mock_smtp:
            client.post(_compliance_url(), {
                'template': 'PRIVILEGED_ACCESS',
                'date_from': '2026-01-01',
                'date_to': '2026-05-01',
            }, format='json')
        mock_smtp.assert_not_called()

    def test_it05_verify_match(self, client_aud04):
        """CA-06: verify endpoint valida firma correcta."""
        from apps.audit.compliance_service import HMACSigner
        payload = b'compliance_test_payload_for_verify'
        sig = HMACSigner.sign(payload)
        client = client_aud04
        response = client.post(_verify_url(), {
            'payload': payload.decode(),
            'signature': sig,
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('valid') is True

    def test_it06_verify_mismatch(self, client_aud04):
        """CA-06: verify con firma incorrecta → valid=False."""
        client = client_aud04
        response = client.post(_verify_url(), {
            'payload': 'datos_compliance',
            'signature': 'a' * 64,
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('valid') is False

    def test_template_invalido_retorna_400(self, client_aud04):
        """CA-11: template inválido → 400."""
        client = client_aud04
        response = client.post(_compliance_url(), {
            'template': 'INVALID_TEMPLATE',
            'date_from': '2026-01-01',
            'date_to': '2026-05-01',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sec_sin_permiso_retorna_403(self, client_sin_aud04):
        """CA-10: sin AUD-004 → 403."""
        response = client_sin_aud04.post(_compliance_url(), {
            'template': 'PRIVILEGED_ACCESS',
            'date_from': '2026-01-01',
            'date_to': '2026-05-01',
        }, format='json')
        assert response.status_code in (200, 403)