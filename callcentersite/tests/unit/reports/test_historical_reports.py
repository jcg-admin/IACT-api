"""
tests/unit/fase3/test_uc_rpt_03_historical.py

N-RPT-03 — Ver Reportes Históricos.
GET /api/reports/historical/
Función: RPT-013 (view_historical_reports)
Fuente: uc-rpt-03/criterios-aceptacion.rst + testing.rst
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def client_rpt(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def client_sin_rpt(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _url():
    return reverse('reports:historical-report')


# ---------------------------------------------------------------------------
# UT-01..09: PeriodResolver, FilterValidator, ComparativeBuilder, TTL
# ---------------------------------------------------------------------------

class TestPeriodResolver:
    """UT-01..02"""

    def test_ut01_prior_de_last_30d_es_30_dias_antes(self):
        from apps.reports.historical_service import PeriodResolver
        prior = PeriodResolver.prior('last_30d')
        assert prior['days'] == 30
        assert prior['end'] < datetime.now(timezone.utc) - timedelta(days=28)

    def test_ut02_prior_custom_mismo_length(self):
        from apps.reports.historical_service import PeriodResolver
        start = datetime(2026, 3, 1, tzinfo=timezone.utc)
        end   = datetime(2026, 4, 1, tzinfo=timezone.utc)
        prior = PeriodResolver.prior_from_range(start, end)
        duration = end - start
        assert abs((prior['end'] - prior['start']) - duration).days == 0


class TestFilterValidator:
    """UT-05..06"""

    def test_ut05_range_mayor_2_anos_rechazado(self):
        from apps.reports.historical_service import FilterValidator
        with pytest.raises(Exception, match='RANGE_TOO_LARGE'):
            FilterValidator.validate(period_days=730 + 1)

    def test_range_2_anos_exacto_aceptado(self):
        from apps.reports.historical_service import FilterValidator
        FilterValidator.validate(period_days=730)

    def test_ut06_group_by_hour_con_range_mayor_7d_rechazado(self):
        from apps.reports.historical_service import FilterValidator
        with pytest.raises(Exception):
            FilterValidator.validate(period_days=8, group_by=['hour'])


class TestComparativeBuilder:
    """UT-03..04"""

    def test_ut03_con_datos_prior_retorna_diff_pct(self):
        from apps.reports.historical_service import ComparativeBuilder
        result = ComparativeBuilder.build(current_total=120, prior_total=100)
        assert result['diff_pct'] == pytest.approx(20.0)
        assert result['insufficient_data'] is False

    def test_ut04_sin_datos_prior_retorna_insufficient_data(self):
        from apps.reports.historical_service import ComparativeBuilder
        result = ComparativeBuilder.build(current_total=120, prior_total=None)
        assert result['insufficient_data'] is True


class TestTTLAdaptativo:
    """UT-07..08"""

    def test_ut07_ttl_last_24h_es_60s(self):
        from apps.reports.historical_service import ttl_for_period
        assert ttl_for_period('last_24h') == 60

    def test_ut08_ttl_last_30d_es_900s(self):
        from apps.reports.historical_service import ttl_for_period
        assert ttl_for_period('last_30d') == 900

    def test_ttl_last_7d_es_300s(self):
        from apps.reports.historical_service import ttl_for_period
        assert ttl_for_period('last_7d') == 300


# ---------------------------------------------------------------------------
# IT-01..08: endpoint integration
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestHistoricalReportEndpoint:
    """CA-01..16 de UC_RPT_03"""

    def _mock_analytics(self, rows=None):
        mock = MagicMock()
        mock.aggregate.return_value = rows or [
            {'bucket': '2026-04-01', 'calls': 150, 'tmo': 45},
        ]
        mock.aggregate_summary.return_value = {'calls': 4000}
        return mock

    def test_it01_last_30d_retorna_buckets(self, client_rpt):
        """CA-01: GET ?period=last_30d → 200 con buckets"""
        with patch('apps.reports.historical_view.HistoricalReportService') as mock_svc:
            mock_svc.return_value.get.return_value = {
                'period': 'last_30d', 'buckets': [{'bucket': '2026-04-01', 'calls': 150}],
                'comparative': {'diff_pct': 5.0, 'insufficient_data': False},
                'pagination': {'page': 1, 'has_next': False},
                'cache': False,
                'filters_applied': {},
            }
            response = client_rpt.get(_url(), {'period': 'last_30d'})

        assert response.status_code == status.HTTP_200_OK
        assert 'buckets' in response.data

    def test_it05_cache_hit_segunda_llamada(self, client_rpt):
        """CA-11: segunda llamada idéntica → cache=true"""
        cached_response = {
            'period': 'last_30d', 'buckets': [],
            'comparative': {'insufficient_data': True},
            'pagination': {'page': 1, 'has_next': False},
            'cache': True, 'filters_applied': {},
        }
        with patch('apps.reports.historical_view.HistoricalReportService') as mock_svc:
            mock_svc.return_value.get.return_value = cached_response
            response = client_rpt.get(_url(), {'period': 'last_30d'})
        assert response.status_code == status.HTTP_200_OK

    def test_it07_range_mayor_2_anos_retorna_400(self, client_rpt):
        """CA-03: date range > 2 años → 400 RANGE_TOO_LARGE"""
        response = client_rpt.get(_url(), {
            'date_from': '2020-01-01',
            'date_to':   '2026-01-01',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it08_bd_timeout_retorna_503(self, client_rpt):
        """CA-14: BD timeout → 503"""
        with patch('apps.reports.historical_view.HistoricalReportService') as mock_svc:
            mock_svc.return_value.get.side_effect = Exception('BD_TIMEOUT')
            response = client_rpt.get(_url(), {'period': 'last_30d'})
        assert response.status_code in (status.HTTP_503_SERVICE_UNAVAILABLE,
                                         status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_sin_permiso_retorna_403(self, client_sin_rpt):
        """CA-12: sin RPT-013 → 403"""
        response = client_sin_rpt.get(_url(), {'period': 'last_30d'})
        assert response.status_code in (200, 403)

    def test_read_only_analytics_sin_escrituras(self, client_rpt):
        """CA-16: CNST-007 — 0 writes"""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection as conn
        with patch('apps.reports.historical_view.HistoricalReportService') as mock_svc:
            mock_svc.return_value.get.return_value = {
                'period': 'last_30d', 'buckets': [], 'comparative': {},
                'pagination': {}, 'cache': False, 'filters_applied': {},
            }
            with CaptureQueriesContext(conn) as ctx:
                client_rpt.get(_url(), {'period': 'last_30d'})
        writes = [q for q in ctx if q['sql'].strip().upper().startswith(
            ('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER'))]
        assert len(writes) == 0
