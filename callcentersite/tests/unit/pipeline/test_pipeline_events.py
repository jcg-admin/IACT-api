"""
tests/unit/pipeline/test_pipeline_events.py

TDD — UC_PIP_02 extension: eventos recientes del pipeline via v_eventos_recientes.

Endpoint:
  GET /api/pipeline/events/    PIP-002  eventos recientes enriquecidos con join a job_execution_log
"""
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def client_pip(db):
    client = APIClient()
    client.force_authenticate(user=AdminUserTestData())
    return client

@pytest.fixture
def client_sin_pip(db):
    client = APIClient()
    client.force_authenticate(user=UserTestData())
    return client


EVENT_ROWS = [
    {
        'id': 10, 'ts': '2026-05-13 17:57:38',
        'error_type': 'PARAM_INVALIDO', 'severity': 'MEDIA',
        'sp_nombre': 'sp_rpt_resumen_abandono_rollup', 'sql_state': '22023',
        'p_quarter': 'INVALIDO', 'p_segmento': None,
        'error_resumen': 'p_quarter invalido: INVALIDO',
        'ejecutado_por': 'django_api',
        'job_status': None, 'job_step': None, 'job_inicio': None,
    },
    {
        'id': 9, 'ts': '2026-05-13 14:26:14',
        'error_type': 'ETL_FALLO', 'severity': 'CRITICA',
        'sp_nombre': 'sp_etl_historico', 'sql_state': '45000',
        'p_quarter': 'Q01_25', 'p_segmento': None,
        'error_resumen': 'Fallo etl_base_detalle: Table no existe',
        'ejecutado_por': 'manual',
        'job_status': 'FAILED', 'job_step': 'etl_base_detalle',
        'job_inicio': '2026-05-13 14:26:14',
    },
]

def _mock_cursor(rows):
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    if rows:
        cols = list(rows[0].keys())
        cur.description = [(c,) + (None,)*6 for c in cols]
        cur.fetchall.return_value = [tuple(r.values()) for r in rows]
    else:
        cur.description = []
        cur.fetchall.return_value = []
    return cur


class TestPipelineEventsEndpoint:
    """UC_PIP_02 — eventos recientes del pipeline (v_eventos_recientes)."""

    def test_it01_lista_eventos_recientes(self, client_pip):
        """CA-01: retorna lista de eventos con error_type, severity, sp_nombre."""
        url = reverse('pipeline:events-list')
        with patch('apps.pipeline.pipeline_event_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_cursor(EVENT_ROWS)
            response = client_pip.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'events' in response.data
        assert len(response.data['events']) == 2
        ev = response.data['events'][0]
        assert ev['error_type'] == 'PARAM_INVALIDO'
        assert ev['severity'] == 'MEDIA'
        assert ev['sp_nombre'] == 'sp_rpt_resumen_abandono_rollup'

    def test_it02_filtra_por_severity(self, client_pip):
        """CA-02: ?severity=CRITICA filtra por nivel de severidad."""
        url = reverse('pipeline:events-list') + '?severity=CRITICA'
        critica_rows = [r for r in EVENT_ROWS if r['severity'] == 'CRITICA']
        with patch('apps.pipeline.pipeline_event_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_cursor(critica_rows)
            response = client_pip.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert all(e['severity'] == 'CRITICA' for e in response.data['events'])

    def test_it03_filtra_por_error_type(self, client_pip):
        """CA-03: ?error_type=ETL_FALLO filtra por tipo."""
        url = reverse('pipeline:events-list') + '?error_type=ETL_FALLO'
        etl_rows = [r for r in EVENT_ROWS if r['error_type'] == 'ETL_FALLO']
        with patch('apps.pipeline.pipeline_event_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_cursor(etl_rows)
            response = client_pip.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert all(e['error_type'] == 'ETL_FALLO' for e in response.data['events'])

    def test_it04_sin_eventos_retorna_lista_vacia(self, client_pip):
        """CA-04: sin eventos → 200 con events=[]."""
        url = reverse('pipeline:events-list')
        with patch('apps.pipeline.pipeline_event_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = _mock_cursor([])
            response = client_pip.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['events'] == []
        assert response.data['total'] == 0

    def test_it05_incluye_contexto_job(self, client_pip):
        """CA-05: eventos con job activo incluyen job_status y job_step."""
        url = reverse('pipeline:events-list')
        with patch('apps.pipeline.pipeline_event_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_cursor(EVENT_ROWS)
            response = client_pip.get(url)

        ev_etl = next(e for e in response.data['events'] if e['error_type'] == 'ETL_FALLO')
        assert ev_etl['job_status'] == 'FAILED'
        assert ev_etl['job_step'] == 'etl_base_detalle'

    def test_it06_mariadb_no_disponible_retorna_503(self, client_pip):
        """CA-06: MariaDB caída → 503."""
        url = reverse('pipeline:events-list')
        from django.db import OperationalError
        with patch('apps.pipeline.pipeline_event_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.side_effect = OperationalError('t')
            response = client_pip.get(url)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_sec01_sin_permiso_retorna_403(self, client_sin_pip):
        """SEC-01: sin PIP-002 → 403."""
        url = reverse('pipeline:events-list')
        response = client_sin_pip.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_it07_limit_defecto_50(self, client_pip):
        """CA-07: sin ?limit, devuelve hasta 50 filas."""
        url = reverse('pipeline:events-list')
        with patch('apps.pipeline.pipeline_event_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_cursor(EVENT_ROWS)
            response = client_pip.get(url)

        assert 'limit' in response.data
        assert response.data['limit'] == 50
