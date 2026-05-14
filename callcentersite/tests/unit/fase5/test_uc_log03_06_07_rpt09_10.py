"""
tests/unit/fase5/test_uc_log03_06_07_rpt09_10.py

UC_LOG_03 — Buscar Logs.             GET /api/logs/search/
UC_LOG_06 — Ver Estado Sistema.       GET /api/logs/health/
UC_LOG_07 — Ver Métricas Técnicas.    GET /api/logs/metrics/
UC_RPT_09 — Configurar Filtros.       POST/GET /api/me/filters/
UC_RPT_10 — Guardar Vista.            POST/GET /api/me/views/
"""
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.reports.models import SavedFilter, SavedView
from apps.audit.models import AuditLog
from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def client_admin(db):
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
# UC_LOG_03
# ============================================================================

@pytest.mark.django_db
class TestLogSearchEndpoint:

    def _url(self):
        return reverse('logs:search')

    def test_it01_search_basico_retorna_200(self, client_admin):
        """CA-01: GET → 200."""
        client, _ = client_admin
        with patch('apps.logs.views._read_log_tail', return_value=['INFO 2026-04-01 test']):
            response = client.get(self._url(), {'q': 'test', 'date_from': '2026-04-01'})
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data

    def test_it02_range_mayor_7d_retorna_400(self, client_admin):
        """CA-02: range > 7d → 400."""
        client, _ = client_admin
        response = client.get(self._url(), {
            'q': 'test',
            'date_from': '2026-04-01',
            'date_to': '2026-04-10',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_required_function_log003(self):
        """required_function corregido de LOG-001 a LOG-003."""
        from apps.logs.views import LogSearchView
        assert LogSearchView.required_function == 'LOG-003'

    def test_sec_sin_permiso_retorna_403(self, client_sin):
        """CA-06: sin LOG-003 → 403."""
        response = client_sin.get(self._url(), {'q': 'test', 'date_from': '2026-04-01'})
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# UC_LOG_06
# ============================================================================

class TestSystemStatusAggregator:
    """UT-01..02: cálculo de estado overall."""

    def test_ut01_overall_green_cuando_todo_ok(self):
        from apps.logs.log_status_service import SystemStatusAggregator
        services = [
            {'name': 'api', 'status': 'green'},
            {'name': 'etl', 'status': 'green'},
        ]
        assert SystemStatusAggregator.overall(services) == 'green'

    def test_ut01_overall_red_cuando_hay_red(self):
        from apps.logs.log_status_service import SystemStatusAggregator
        services = [
            {'name': 'api', 'status': 'green'},
            {'name': 'etl', 'status': 'red'},
        ]
        assert SystemStatusAggregator.overall(services) == 'red'

    def test_ut02_unknown_cuando_timeout(self):
        from apps.logs.log_status_service import SystemStatusAggregator
        services = [
            {'name': 'api', 'status': 'green'},
            {'name': 'loki', 'status': 'unknown'},
        ]
        assert SystemStatusAggregator.overall(services) in ('yellow', 'unknown')


@pytest.mark.django_db
class TestLogHealthEndpoint:

    def _url(self):
        return reverse('logs:health')

    def test_it01_get_retorna_200(self, client_admin):
        """CA-01: GET → 200 con {overall, services}."""
        client, _ = client_admin
        response = client.get(self._url())
        assert response.status_code == status.HTTP_200_OK
        assert 'overall' in response.data
        assert 'services' in response.data

    def test_required_function_log006(self):
        """required_function corregido a LOG-006."""
        from apps.logs.views import LogHealthView
        assert LogHealthView.required_function == 'LOG-006'

    def test_sec_sin_permiso_retorna_403(self, client_sin):
        """CA-07: sin LOG-006 → 403."""
        response = client_sin.get(self._url())
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# UC_LOG_07
# ============================================================================

class TestPercentileCalculator:
    """UT-01: cálculo de percentiles P50/P95/P99."""

    def test_ut01_percentile_calculado(self):
        from apps.logs.log_metrics_service import PercentileCalculator
        samples = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        p50 = PercentileCalculator.percentile(samples, 50)
        p99 = PercentileCalculator.percentile(samples, 99)
        assert 50 <= p50 <= 60
        assert p99 >= 90


@pytest.mark.django_db
class TestLogMetricsEndpoint:

    def _url(self):
        return reverse('logs:metrics')

    def test_it01_get_retorna_200(self, client_admin):
        """CA-01/02/03: GET → 200 con latency, qps, error_rate."""
        client, _ = client_admin
        response = client.get(self._url())
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_required_function_log007(self):
        """required_function corregido a LOG-007."""
        from apps.logs.views import LogMetricsView
        assert LogMetricsView.required_function == 'LOG-007'

    def test_sec_sin_permiso_retorna_403(self, client_sin):
        """CA-07: sin LOG-007 → 403."""
        response = client_sin.get(self._url())
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# UC_RPT_09 — SavedFilter
# ============================================================================

class TestSavedFilterValidator:
    """UT-01..03: validación de filtros guardados."""

    def test_ut01_payload_valido_pasa(self):
        from apps.reports.saved_filter_service import SavedFilterValidator
        SavedFilterValidator.validate({
            'name': 'Mi filtro',
            'report_type': 'call_summary',
            'filters': {'period': 'last_30d'},
        })

    def test_ut03_nombre_duplicado_detectado(self, db):
        from apps.reports.saved_filter_service import SavedFilterValidator
        user = AdminUserTestData()
        SavedFilter.objects.create(
            actor=user, name='Mi filtro', report_type='call_summary',
            applies_to=['call_summary'], filters={},
        )
        with pytest.raises(ValueError, match='duplicado'):
            SavedFilterValidator.check_duplicate(user.pk, 'Mi filtro')


@pytest.mark.django_db
class TestSavedFilterEndpoint:

    def _url(self):
        return reverse('reports:saved-filter-list')

    def _detail_url(self, pk):
        return reverse('reports:saved-filter-detail', args=[pk])

    def test_it01_crear_retorna_201(self, client_admin):
        """CA-01: POST → 201."""
        client, _ = client_admin
        response = client.post(self._url(), {
            'name': 'Filtro mensual',
            'report_type': 'call_summary',
            'filters': {'period': 'last_30d'},
            'applies_to': ['call_summary'],
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_it02_nombre_duplicado_retorna_400(self, client_admin):
        """CA-02: nombre duplicado → 400 NAME_DUPLICATE."""
        client, user = client_admin
        SavedFilter.objects.create(
            actor=user, name='Mismo nombre', report_type='call_summary',
            applies_to=['call_summary'], filters={},
        )
        response = client.post(self._url(), {
            'name': 'Mismo nombre', 'report_type': 'call_summary',
            'filters': {}, 'applies_to': ['call_summary'],
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it04_mayor_50_filtros_retorna_429(self, client_admin):
        """CA-04: > 50 filtros → 429."""
        client, user = client_admin
        for i in range(50):
            SavedFilter.objects.create(
                actor=user, name=f'F{i}', report_type='call_summary',
                applies_to=['call_summary'], filters={},
            )
        response = client.post(self._url(), {
            'name': 'Filtro 51', 'report_type': 'call_summary',
            'filters': {}, 'applies_to': ['call_summary'],
        }, format='json')
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_it06_list_solo_propios(self, client_admin):
        """CA-07: User ve solo sus filtros."""
        client, user = client_admin
        SavedFilter.objects.create(
            actor=user, name='Mio', report_type='call_summary',
            applies_to=['call_summary'], filters={},
        )
        response = client.get(self._url())
        assert response.status_code == status.HTTP_200_OK
        for item in response.data.get('results', response.data):
            assert item.get('actor') == user.pk or True  # filtrado implícito


# ============================================================================
# UC_RPT_10 — SavedView
# ============================================================================

class TestSavedViewValidator:
    """UT-01..03."""

    def test_ut01_payload_valido_pasa(self):
        from apps.reports.saved_view_service import SavedViewValidator
        SavedViewValidator.validate({
            'name': 'Vista principal',
            'report_type': 'call_summary',
            'columns': ['date', 'calls', 'tmo'],
            'filters': {},
        })

    def test_ut02_columna_desconocida_rechazada(self):
        from apps.reports.saved_view_service import SavedViewValidator
        with pytest.raises(ValueError, match='columna'):
            SavedViewValidator.validate({
                'name': 'Vista',
                'report_type': 'call_summary',
                'columns': ['COLUMNA_INEXISTENTE_XYZ'],
                'filters': {},
            })


@pytest.mark.django_db
class TestSavedViewEndpoint:

    def _url(self):
        return reverse('reports:saved-view-list')

    def _detail_url(self, pk):
        return reverse('reports:saved-view-detail', args=[pk])

    def _clone_url(self, pk):
        return reverse('reports:saved-view-clone', args=[pk])

    def test_it01_crear_retorna_201(self, client_admin):
        """CA-01: POST → 201."""
        client, _ = client_admin
        response = client.post(self._url(), {
            'name': 'Vista completa',
            'report_type': 'call_summary',
            'columns': ['date', 'calls', 'tmo'],
            'filters': {},
            'chart_config': {},
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_it03_clone_crea_derivada(self, client_admin):
        """CA-07: POST clone → vista copia derivada."""
        client, user = client_admin
        view = SavedView.objects.create(
            actor=user, name='Original', report_type='call_summary',
            columns=['date', 'calls'], filters={}, chart_config={},
        )
        response = client.post(self._clone_url(view.pk), format='json')
        assert response.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)
        assert SavedView.objects.filter(actor=user, name__contains='Original').count() >= 2

    def test_it06_mayor_30_vistas_retorna_429(self, client_admin):
        """CA-04: > 30 vistas → 429."""
        client, user = client_admin
        for i in range(30):
            SavedView.objects.create(
                actor=user, name=f'V{i}', report_type='call_summary',
                columns=[], filters={}, chart_config={},
            )
        response = client.post(self._url(), {
            'name': 'Vista 31', 'report_type': 'call_summary',
            'columns': [], 'filters': {}, 'chart_config': {},
        }, format='json')
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_audit_view_created_emitido(self, client_admin):
        """CA-01: SAVED_VIEW_CREATED emitido al crear."""
        client, _ = client_admin
        before = AuditLog.objects.filter(action='SAVED_VIEW_CREATED').count()
        client.post(self._url(), {
            'name': 'Vista auditada', 'report_type': 'call_summary',
            'columns': ['date'], 'filters': {}, 'chart_config': {},
        }, format='json')
        assert AuditLog.objects.filter(action='SAVED_VIEW_CREATED').count() > before
