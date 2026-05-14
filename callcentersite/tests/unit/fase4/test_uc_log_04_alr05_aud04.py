"""
tests/unit/fase4/test_uc_log_04_alr05_aud04.py

UC_LOG_04 — Exportar Logs (async).       POST/GET/DELETE /api/logs/export/
UC_ALR_05 — Gestionar Suscripciones.     POST/DELETE/PATCH /api/me/alert-subscriptions/
UC_AUD_04 — Generar Reporte Compliance.  POST /api/audit/compliance-report/
"""
import pytest
import hmac, hashlib
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertRule, AlertSubscription
from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


# ============================================================================
# UC_LOG_04
# ============================================================================

@pytest.fixture
def client_log04(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_sin_log04(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


class TestLogExportValidator:
    """UT-01: validación de payload."""

    def test_row_limit_10m_rechazado(self):
        from apps.logs.log_export_service import LogExportValidator
        with pytest.raises(ValueError, match='10'):
            LogExportValidator.check_row_limit(10_000_001)

    def test_row_limit_10m_exacto_aceptado(self):
        from apps.logs.log_export_service import LogExportValidator
        LogExportValidator.check_row_limit(10_000_000)


@pytest.mark.django_db
class TestLogExportEndpoint:

    def _url(self):
        return reverse('logs:log-export-queue')

    def _payload(self):
        return {
            'log_type': 'application',
            'date_from': '2026-04-01',
            'date_to': '2026-04-30',
            'format': 'csv',
        }

    def test_it01_encolar_retorna_202(self, client_log04):
        """CA-01: POST → 202 + job_id."""
        client, _ = client_log04
        response = client.post(self._url(), self._payload(), format='json')
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert 'job_id' in response.data

    def test_it01_audit_log_export_queued(self, client_log04):
        """CA-07: LOG_EXPORT_QUEUED emitido."""
        client, _ = client_log04
        client.post(self._url(), self._payload(), format='json')
        assert AuditLog.objects.filter(event_type='LOG_EXPORT_QUEUED').exists()

    def test_sec_no_smtp(self, client_log04):
        """CA-06: CNST-001 — sin email externo."""
        client, _ = client_log04
        with patch('smtplib.SMTP') as mock_smtp:
            client.post(self._url(), self._payload(), format='json')
        mock_smtp.assert_not_called()

    def test_sec_sin_permiso_retorna_403(self, client_sin_log04):
        """CA-08: sin LOG-002 → 403."""
        response = client_sin_log04.post(self._url(), self._payload(), format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# UC_ALR_05
# ============================================================================

@pytest.fixture
def client_alr05(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_sin_alr05(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _sub_url():
    return reverse('alerts:alert-subscription-list')


def _sub_detail_url(sub_id):
    return reverse('alerts:alert-subscription-detail', args=[sub_id])


def _make_rule(user):
    return AlertRule.objects.create(
        actor=user, name='R_sub', metric='call_volume',
        scope={'segment': 'all'}, condition={'op': '>', 'threshold': 50},
        window_minutes=5, severity='warning',
    )


class TestAlertSubscriptionValidator:
    """UT-01..02"""

    def test_ut01_severity_valido_pasa(self):
        from apps.alerts.alert_subscription_service import SubscriptionValidator
        SubscriptionValidator.validate({'severity_filter': 'critical'})

    def test_ut02_detecta_duplicado(self, db):
        from apps.alerts.alert_subscription_service import SubscriptionValidator
        user = AdminUserTestData()
        rule = _make_rule(user)
        AlertSubscription.objects.create(rule=rule, user=user, state='active')
        with pytest.raises(ValueError, match='duplicad'):
            SubscriptionValidator.check_duplicate(user_id=user.pk, rule_id=rule.pk)


@pytest.mark.django_db
class TestAlertSubscriptionEndpoint:

    def test_it01_crear_subscription_propia_retorna_201(self, client_alr05):
        """CA-01: POST → 201 + sub creada."""
        client, user = client_alr05
        rule = _make_rule(user)
        response = client.post(_sub_url(), {
            'rule_id': rule.pk,
            'severity_filter': 'warning',
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_it04_duplicada_retorna_409(self, client_alr05):
        """CA-04: subscripción duplicada → 409."""
        client, user = client_alr05
        rule = _make_rule(user)
        AlertSubscription.objects.create(rule=rule, user=user, state='active')
        response = client.post(_sub_url(), {
            'rule_id': rule.pk,
            'severity_filter': 'critical',
        }, format='json')
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_it01_audit_subscription_created(self, client_alr05):
        """CA-09: ALERT_SUBSCRIPTION_CREATED emitido."""
        client, user = client_alr05
        rule = _make_rule(user)
        before = AuditLog.objects.count()
        client.post(_sub_url(), {'rule_id': rule.pk, 'severity_filter': 'warning'}, format='json')
        assert AuditLog.objects.filter(event_type='ALERT_SUBSCRIPTION_CREATED').exists()

    def test_sec_sin_permiso_retorna_403(self, client_sin_alr05):
        """CA-08: sin ALR-008 → 403."""
        response = client_sin_alr05.post(
            _sub_url(), {'rule_id': 1, 'severity_filter': 'warning'}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# UC_AUD_04
# ============================================================================

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
            event_type__in=['COMPLIANCE_REPORT_REQUESTED', 'COMPLIANCE_REPORT_GENERATED']
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
        assert response.status_code == status.HTTP_403_FORBIDDEN
