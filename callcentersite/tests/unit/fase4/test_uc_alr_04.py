"""
tests/unit/fase4/test_uc_alr_04.py

UC_ALR_04 — Ver Historial de Alertas.
GET /api/alerts/history/
Función: ALR-006 (view_alert_history)
Fuente: uc-alr-04/criterios-aceptacion.rst
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from django.urls import reverse
from django.utils import timezone as tz
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertRule, Alert
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def client_alr04(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_sin_alr04(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _url():
    return reverse('alerts:alert-history')


def _make_resolved_alert(user):
    rule = AlertRule.objects.create(
        actor=user, name='R_hist', metric='call_volume',
        scope={'segment': 'all'}, condition={'op': '>', 'threshold': 50},
        window_minutes=5, severity='warning',
    )
    return Alert.objects.create(
        rule=rule, rule_name=rule.name,
        metric={'name': 'call_volume'}, scope={'segment': 'all'},
        severity='warning', state=Alert.STATE_RESOLVED,
        fired_at=tz.now() - timedelta(hours=2),
    )


class TestTimingCalculator:
    """UT-01..02: métricas de tiempo."""

    def test_ut01_time_to_ack_calculado(self):
        from apps.alerts.alert_history_service import TimingCalculator
        fired = datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc)
        acked = datetime(2026, 5, 1, 10, 15, tzinfo=timezone.utc)
        assert TimingCalculator.time_to_ack(fired, acked) == 15 * 60

    def test_ut02_time_to_resolve_calculado(self):
        from apps.alerts.alert_history_service import TimingCalculator
        fired    = datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc)
        resolved = datetime(2026, 5, 1, 11, 0, tzinfo=timezone.utc)
        assert TimingCalculator.time_to_resolve(fired, resolved) == 3600

    def test_no_acked_retorna_none(self):
        from apps.alerts.alert_history_service import TimingCalculator
        assert TimingCalculator.time_to_ack(datetime.now(timezone.utc), None) is None


@pytest.mark.django_db
class TestAlertHistoryEndpoint:

    def test_it01_list_con_range(self, client_alr04):
        """CA-01: GET → 200 con {items, summary}."""
        client, user = client_alr04
        _make_resolved_alert(user)
        response = client.get(_url(), {'days': 7})
        assert response.status_code == status.HTTP_200_OK
        assert 'items' in response.data
        assert 'summary' in response.data

    def test_it02_filtros_aplican(self, client_alr04):
        """CA-02: ?severity=warning → sólo ese severity."""
        client, user = client_alr04
        _make_resolved_alert(user)
        response = client.get(_url(), {'severity': 'warning', 'days': 30})
        assert response.status_code == status.HTTP_200_OK
        for item in response.data.get('items', []):
            assert item['severity'] == 'warning'

    def test_it04_range_mayor_1_anio_retorna_400(self, client_alr04):
        """CA-03: range > 1 año → 400."""
        client, _ = client_alr04
        response = client.get(_url(), {'days': 366})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it05_summary_con_top_rules(self, client_alr04):
        """CA-07 + CA-08: summary.total y top_rules presentes."""
        client, user = client_alr04
        _make_resolved_alert(user)
        response = client.get(_url(), {'days': 30})
        assert response.status_code == status.HTTP_200_OK
        summary = response.data.get('summary', {})
        assert 'total' in summary
        assert 'top_rules' in summary

    def test_sec_sin_permiso_retorna_403(self, client_sin_alr04):
        """CA-10: sin ALR-006 → 403."""
        response = client_sin_alr04.get(_url(), {'days': 7})
        assert response.status_code == status.HTTP_403_FORBIDDEN
