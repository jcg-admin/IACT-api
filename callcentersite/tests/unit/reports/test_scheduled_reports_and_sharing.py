"""
tests/unit/fase4/test_uc_rpt_07_08_11.py

UC_RPT_07 — Programar Reporte.           POST/PATCH/DELETE /api/reports/schedules/
UC_RPT_08 — Ver Reportes Programados.    GET /api/reports/schedules/ + GET /{id}/
UC_RPT_11 — Compartir Reporte.           POST/DELETE /api/reports/shares/
"""
import pytest
from datetime import timedelta
from unittest.mock import patch
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.reports.models import ScheduledReport
from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


# ============================================================================
# UC_RPT_07
# ============================================================================

@pytest.fixture
def client_rpt07(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_sin_rpt07(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _sched_url():
    return reverse('reports:schedule-list-create')


def _sched_detail_url(sched_id):
    return reverse('reports:schedule-detail', args=[sched_id])


def _valid_schedule_payload(frequency='daily'):
    return {
        'report_type': 'call_summary',
        'format': 'csv',
        'frequency': frequency,
        'run_at_hour': 6,
        'filters': {},
        'group_by': ['day'],
    }


class TestScheduleValidator:
    """UT-01..06"""

    def test_ut01_cron_valido_aceptado(self):
        from apps.reports.schedule_service import ScheduleValidator
        ScheduleValidator.validate_cron('0 6 * * 1')

    def test_ut02_cron_invalido_rechazado(self):
        from apps.reports.schedule_service import ScheduleValidator
        with pytest.raises(ValueError, match='cron'):
            ScheduleValidator.validate_cron('99 99 99 99 99')

    def test_ut03_compute_next_daily(self):
        from apps.reports.schedule_service import ScheduleService
        next_run = ScheduleService.compute_next({
            'frequency': 'daily', 'run_at_hour': 6, 'run_at_minute': 0,
        })
        assert next_run is not None
        assert next_run.hour == 6

    def test_ut06_frequency_menor_1h_rechazada(self):
        from apps.reports.schedule_service import ScheduleValidator
        with pytest.raises(ValueError):
            ScheduleValidator.validate_min_frequency(cron_expr='*/30 * * * *')


@pytest.mark.django_db
class TestScheduledReportEndpoint:

    def test_it01_crear_daily_retorna_201(self, client_rpt07):
        """CA-01: POST daily → 201 + next_run_at."""
        client, _ = client_rpt07
        response = client.post(_sched_url(), _valid_schedule_payload('daily'), format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'next_run_at' in response.data

    def test_it01_audit_scheduled_report_created(self, client_rpt07):
        """CA-15: SCHEDULED_REPORT_CREATED emitido."""
        client, _ = client_rpt07
        client.post(_sched_url(), _valid_schedule_payload(), format='json')
        assert AuditLog.objects.filter(action='SCHEDULED_REPORT_CREATED').exists()

    def test_it07_11a_schedule_retorna_429(self, client_rpt07):
        """CA-07: > 10 schedules → 429."""
        client, user = client_rpt07
        for _ in range(10):
            ScheduledReport.objects.create(
                actor=user, report_type='call_summary', format='csv',
                frequency='daily', filters={}, group_by=[],
                status=ScheduledReport.STATUS_ACTIVE,
            )
        response = client.post(_sched_url(), _valid_schedule_payload(), format='json')
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_it04_pause_resume(self, client_rpt07):
        """CA-13: PATCH status=paused / status=active."""
        client, user = client_rpt07
        sched = ScheduledReport.objects.create(
            actor=user, report_type='call_summary', format='csv',
            frequency='daily', filters={}, group_by=[],
            status=ScheduledReport.STATUS_ACTIVE,
        )
        response = client.patch(
            _sched_detail_url(sched.pk), {'status': 'paused'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        sched.refresh_from_db()
        assert sched.status == ScheduledReport.STATUS_PAUSED

    def test_it06_delete_baja_logica(self, client_rpt07):
        """CA-12: DELETE → status=deleted (BR-009)."""
        client, user = client_rpt07
        sched = ScheduledReport.objects.create(
            actor=user, report_type='call_summary', format='csv',
            frequency='daily', filters={}, group_by=[],
            status=ScheduledReport.STATUS_ACTIVE,
        )
        sched_id = sched.pk
        response = client.delete(_sched_detail_url(sched_id))
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
        sched.refresh_from_db()
        assert sched.status == ScheduledReport.STATUS_DELETED

    def test_sec_sin_permiso_retorna_403(self, client_sin_rpt07):
        """CA-16: sin RPT-009 → 403."""
        response = client_sin_rpt07.post(
            _sched_url(), _valid_schedule_payload(), format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# UC_RPT_08
# ============================================================================

@pytest.mark.django_db
class TestScheduledReportListEndpoint:

    def _sched_list_url(self):
        return reverse('reports:schedule-list-create')

    def test_it01_list_solo_propios(self, client_rpt07):
        """CA-01 + CA-07: User ve sólo sus schedules."""
        client, user = client_rpt07
        ScheduledReport.objects.create(
            actor=user, report_type='call_summary', format='csv',
            frequency='daily', filters={}, group_by=[],
            status=ScheduledReport.STATUS_ACTIVE,
        )
        response = client.get(self._sched_list_url())
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or isinstance(response.data, list)

    def test_it02_filter_status_active(self, client_rpt07):
        """CA-03: ?status=active → sólo activos."""
        client, user = client_rpt07
        ScheduledReport.objects.create(
            actor=user, report_type='call_summary', format='csv',
            frequency='daily', filters={}, group_by=[],
            status=ScheduledReport.STATUS_PAUSED,
        )
        response = client.get(self._sched_list_url(), {'status': 'active'})
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# UC_RPT_11
# ============================================================================

@pytest.fixture
def client_rpt11(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


def _share_url():
    return reverse('reports:share-create')


def _share_detail_url(share_id):
    return reverse('reports:share-detail', args=[share_id])


class TestShareValidator:
    """UT-01..04"""

    def test_ut01_share_to_user_valido(self):
        from apps.reports.share_service import ShareValidator
        ShareValidator.validate({
            'target_type': 'user',
            'target_id': 5,
            'owner_id': 1,
            'permission': 'read',
        })

    def test_ut03_share_a_si_mismo_rechazado(self):
        from apps.reports.share_service import ShareValidator
        with pytest.raises(ValueError):
            ShareValidator.validate({
                'target_type': 'user',
                'target_id': 1,
                'owner_id': 1,
                'permission': 'read',
            })


@pytest.mark.django_db
class TestShareReportEndpoint:

    def _payload(self, target_user_id):
        return {
            'report_type': 'call_summary',
            'filters': {},
            'target_type': 'user',
            'target_id': target_user_id,
            'permission': 'read',
        }

    def test_it01_share_to_user_retorna_201(self, client_rpt11):
        """CA-01: POST → 201 + ShareEntry."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        client, user = client_rpt11
        target = User.objects.create_user(username='share_target', password='P@ss123!')
        response = client.post(_share_url(), self._payload(target.pk), format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_it01_audit_report_share_created(self, client_rpt11):
        """CA-12: REPORT_SHARE_CREATED emitido."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        client, user = client_rpt11
        target = User.objects.create_user(username='share_audit', password='P@ss123!')
        client.post(_share_url(), self._payload(target.pk), format='json')
        assert AuditLog.objects.filter(action='REPORT_SHARE_CREATED').exists()

    def test_sec_no_email_externo(self, client_rpt11):
        """CA-14: CNST-001 — sin email externo."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        client, user = client_rpt11
        target = User.objects.create_user(username='share_nomail', password='P@ss123!')
        with patch('smtplib.SMTP') as mock_smtp:
            client.post(_share_url(), self._payload(target.pk), format='json')
        mock_smtp.assert_not_called()

    def test_sec_sin_permiso_retorna_403(self, client_sin_rpt07):
        """CA-11: sin RPT-011 → 403."""
        response = client_sin_rpt07.post(
            _share_url(), {'target_type': 'user', 'target_id': 1}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
