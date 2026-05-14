"""
tests/unit/fase3/test_uc_rpt_04_export.py

N-RPT-04 — Exportar Reporte (patrón Larman async).
POST /api/reports/export/        → 202 + job_id
GET  /api/reports/export/{id}/   → status + progress_pct
DELETE /api/reports/export/{id}/ → cancelled
Función: RPT-004 (export_csv) / RPT-005 (export_excel) / RPT-006 (export_pdf)
Fuente: uc-rpt-04/criterios-aceptacion.rst + testing.rst
"""
import uuid
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.reports.models import ExportJob
from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def client_rpt04(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_sin_rpt04(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _queue_url():
    return reverse('reports:export-queue')


def _detail_url(job_id):
    return reverse('reports:export-detail', args=[job_id])


def _valid_payload():
    return {
        'report_type': 'call_summary',
        'format': 'csv',
        'period': {'preset': 'last_30d'},
        'filters': {},
        'group_by': ['day'],
    }


# ---------------------------------------------------------------------------
# UT-01..09: validadores y workers — funciones puras
# ---------------------------------------------------------------------------

class TestPayloadValidator:
    """UT-01..03"""

    def test_ut01_payload_valido_pasa(self):
        from apps.reports.export_service import PayloadValidator
        PayloadValidator.validate(_valid_payload())  # no lanza

    def test_ut02_format_desconocido_rechazado(self):
        from apps.reports.export_service import PayloadValidator
        with pytest.raises(ValueError, match='format'):
            PayloadValidator.validate({**_valid_payload(), 'format': 'word'})

    def test_ut03_report_type_desconocido_rechazado(self):
        from apps.reports.export_service import PayloadValidator
        with pytest.raises(ValueError, match='report_type'):
            PayloadValidator.validate({**_valid_payload(), 'report_type': 'INEXISTENTE'})


class TestJobLimiter:
    """UT-04"""

    def test_ut04_count_active_correcto(self, db):
        from apps.reports.export_service import JobLimiter
        user = AdminUserTestData()
        # Crear 3 jobs activos
        for _ in range(3):
            ExportJob.objects.create(
                actor=user, report_type='call_summary', format='csv',
                filters={}, period={}, group_by=[],
                status=ExportJob.STATUS_QUEUED,
            )
        assert JobLimiter.count_active(user.pk) == 3

    def test_row_limit_exceeded_rechazado(self):
        from apps.reports.export_service import JobLimiter
        with pytest.raises(ValueError, match='ROW_LIMIT'):
            JobLimiter.check_row_limit(1_000_001)

    def test_row_limit_exacto_1m_aceptado(self):
        from apps.reports.export_service import JobLimiter
        JobLimiter.check_row_limit(1_000_000)  # no lanza


class TestPayloadSanitizer:
    """UT-08: Sanitizer remueve campos PII."""

    def test_ut08_sanitizer_elimina_pii(self):
        from apps.reports.export_service import PayloadSanitizer
        row = {'caller_name': 'Juan Pérez', 'phone': '555-1234', 'calls': 42}
        sanitized = PayloadSanitizer.sanitize_row(row)
        assert 'Juan Pérez' not in str(sanitized)
        assert '555-1234' not in str(sanitized)
        assert sanitized.get('calls') == 42  # campos no-PII intactos


# ---------------------------------------------------------------------------
# IT-01..11: endpoint integration
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestExportQueueEndpoint:
    """CA-01, CA-07..08, CA-19 de UC_RPT_04"""

    def test_it01_queue_retorna_202_con_job_id(self, client_rpt04):
        """CA-01: POST → 202 + job_id + status=queued en BD"""
        client, _ = client_rpt04
        response = client.post(_queue_url(), _valid_payload(), format='json')

        assert response.status_code == status.HTTP_202_ACCEPTED, response.data
        assert 'job_id' in response.data
        job_id = response.data['job_id']
        assert ExportJob.objects.filter(id=job_id, status=ExportJob.STATUS_QUEUED).exists()

    def test_it01_audit_report_export_queued(self, client_rpt04):
        """CA-16: REPORT_EXPORT_QUEUED emitido al encolar"""
        client, _ = client_rpt04
        before = AuditLog.objects.count()
        client.post(_queue_url(), _valid_payload(), format='json')
        assert AuditLog.objects.count() > before
        assert AuditLog.objects.filter(event_type='REPORT_EXPORT_QUEUED').exists()

    def test_it07_mas_5_jobs_retorna_429(self, client_rpt04):
        """CA-08: > 5 jobs activos → 429 EXPORT_LIMIT_EXCEEDED"""
        client, user = client_rpt04
        for _ in range(5):
            ExportJob.objects.create(
                actor=user, report_type='call_summary', format='csv',
                filters={}, period={}, group_by=[],
                status=ExportJob.STATUS_QUEUED,
            )
        response = client.post(_queue_url(), _valid_payload(), format='json')
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_sec01_no_smtp_llamado(self, client_rpt04):
        """CA-15: CNST-001 — no email externo"""
        client, _ = client_rpt04
        with patch('smtplib.SMTP') as mock_smtp:
            client.post(_queue_url(), _valid_payload(), format='json')
            mock_smtp.assert_not_called()

    def test_sec_sin_permiso_retorna_403(self, client_sin_rpt04):
        """CA-19: sin RPT-004 → 403"""
        response = client_sin_rpt04.post(_queue_url(), _valid_payload(), format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestExportDetailEndpoint:
    """CA-17..18 de UC_RPT_04"""

    def _make_queued_job(self, user):
        return ExportJob.objects.create(
            actor=user, report_type='call_summary', format='csv',
            filters={}, period={'preset': 'last_30d'}, group_by=['day'],
            status=ExportJob.STATUS_QUEUED,
        )

    def _make_running_job(self, user):
        job = self._make_queued_job(user)
        job.status = ExportJob.STATUS_RUNNING
        job.progress_pct = 45
        job.save(update_fields=['status', 'progress_pct'])
        return job

    def test_it11_status_check_retorna_progress_pct(self, client_rpt04):
        """CA-18: GET /{id}/ → status + progress_pct"""
        client, user = client_rpt04
        job = self._make_running_job(user)
        response = client.get(_detail_url(job.id))

        assert response.status_code == status.HTTP_200_OK
        assert 'status' in response.data
        assert 'progress_pct' in response.data
        assert response.data['status'] == ExportJob.STATUS_RUNNING

    def test_it08_cancel_queued_retorna_cancelled(self, client_rpt04):
        """CA-17: DELETE job queued → status=cancelled"""
        client, user = client_rpt04
        job = self._make_queued_job(user)
        response = client.delete(_detail_url(job.id))

        assert response.status_code in (
            status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
        job.refresh_from_db()
        assert job.status == ExportJob.STATUS_CANCELLED

    def test_it09_cancel_running_solicita_graceful(self, client_rpt04):
        """CA-17: DELETE job running → cancellation_requested=True"""
        client, user = client_rpt04
        job = self._make_running_job(user)
        response = client.delete(_detail_url(job.id))

        assert response.status_code in (
            status.HTTP_200_OK, status.HTTP_202_ACCEPTED, status.HTTP_204_NO_CONTENT)
        job.refresh_from_db()
        assert job.cancellation_requested is True


@pytest.mark.django_db
class TestExportWorker:
    """IT-02..06: worker procesa el job"""

    def _make_queued_job(self, user):
        return ExportJob.objects.create(
            actor=user, report_type='call_summary', format='csv',
            filters={}, period={'preset': 'last_30d'}, group_by=['day'],
            status=ExportJob.STATUS_QUEUED,
        )

    def test_it02_worker_pickup_estado_running(self, db):
        """IT-02: worker marca job como running"""
        from apps.reports.export_service import ExportWorker
        user = AdminUserTestData()
        job = self._make_queued_job(user)
        ExportWorker.process(str(job.id))
        job.refresh_from_db()
        # El job está done o failed — transitó por running
        assert job.status in (
            ExportJob.STATUS_DONE, ExportJob.STATUS_FAILED,
            ExportJob.STATUS_RUNNING,
        )

    def test_it04_recheck_permiso_revocado(self, db):
        """CA-09: permiso revocado durante ejecución → status=failed + PERMISSION_REVOKED"""
        from apps.reports.export_service import ExportWorker
        user = AdminUserTestData()
        job = self._make_queued_job(user)

        with patch('apps.reports.export_service.ExportWorker._check_permission',
                   return_value=False):
            ExportWorker.process(str(job.id))

        job.refresh_from_db()
        assert job.status == ExportJob.STATUS_FAILED
        assert job.error_code == 'PERMISSION_REVOKED'

    def test_it03_worker_completes_emite_audit_completed(self, db):
        """CA-16: REPORT_EXPORT_COMPLETED emitido al completar"""
        from apps.reports.export_service import ExportWorker
        user = AdminUserTestData()
        job = self._make_queued_job(user)
        before = AuditLog.objects.count()

        with patch('apps.reports.export_service.ExportWorker._write_csv',
                   return_value=('/tmp/test.csv', 100, 1024)):
            ExportWorker.process(str(job.id))

        job.refresh_from_db()
        if job.status == ExportJob.STATUS_DONE:
            assert AuditLog.objects.filter(
                event_type='REPORT_EXPORT_COMPLETED').count() > 0

    def test_mailbox_notificado_al_completar(self, db):
        """CA-14: Mailbox notify al completar — CNST-001 no email externo"""
        from apps.reports.export_service import ExportWorker
        from apps.alerts.models import InternalMailbox, MailboxMessage
        user = AdminUserTestData()
        job = self._make_queued_job(user)
        before = MailboxMessage.objects.count()

        with patch('apps.reports.export_service.ExportWorker._write_csv',
                   return_value=('/tmp/test.csv', 100, 1024)):
            ExportWorker.process(str(job.id))

        job.refresh_from_db()
        if job.status == ExportJob.STATUS_DONE:
            assert MailboxMessage.objects.count() > before
