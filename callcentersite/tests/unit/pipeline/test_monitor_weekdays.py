"""
tests/unit/pipeline/test_monitor_weekdays.py

TDD — Monitor de distribución de llamadas por dias de semana
via vw_monitor_dias_semana.

Endpoint:
  GET /api/pipeline/monitor/weekdays/   PIP-001  view_pipeline_status

Contrato de vw_monitor_dias_semana:
  trimestre, fecha(YYYYMM), total, habiles, fin_semana,
  error_suma, pct_entre_semana, estado_monitor
"""
import pytest
from decimal import Decimal
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


MONITOR_ROWS = [
    {'trimestre': 'Q01_25', 'fecha': '202501', 'total': Decimal('40918'),
     'habiles': Decimal('30383'), 'fin_semana': Decimal('10535'),
     'error_suma': Decimal('0'), 'pct_entre_semana': Decimal('74.3'),
     'estado_monitor': 'OK'},
    {'trimestre': 'Q01_25', 'fecha': '202502', 'total': Decimal('37077'),
     'habiles': Decimal('26583'), 'fin_semana': Decimal('10494'),
     'error_suma': Decimal('0'), 'pct_entre_semana': Decimal('71.7'),
     'estado_monitor': 'OK'},
    {'trimestre': 'Q02_26', 'fecha': '202604', 'total': Decimal('9500'),
     'habiles': Decimal('6800'), 'fin_semana': Decimal('2710'),
     'error_suma': Decimal('10'), 'pct_entre_semana': Decimal('71.6'),
     'estado_monitor': 'ALERTA'},
]


def _mock_cursor(rows):
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__  = MagicMock(return_value=False)
    if rows:
        cols = list(rows[0].keys())
        cur.description = [(c,) + (None,)*6 for c in cols]
        cur.fetchall.return_value = [tuple(r.values()) for r in rows]
    else:
        cur.description = []
        cur.fetchall.return_value = []
    return cur


class TestMonitorWeekdaysEndpoint:
    """Monitor de distribución días semana — vw_monitor_dias_semana."""

    def test_it01_retorna_filas_con_campos_correctos(self, client_pip):
        """CA-01: retorna trimestre, fecha, total, habiles, fin_semana, estado."""
        url = reverse('pipeline:monitor-weekdays')
        with patch('apps.pipeline.monitor_weekday_views.connections') as mc:
            mc.__getitem__.return_value.cursor.return_value = _mock_cursor(MONITOR_ROWS)
            response = client_pip.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'filas' in response.data
        fila = response.data['filas'][0]
        assert fila['trimestre'] == 'Q01_25'
        assert fila['fecha'] == '202501'
        assert 'total' in fila
        assert 'habiles' in fila
        assert 'fin_semana' in fila
        assert 'estado_monitor' in fila

    def test_it02_filtra_por_trimestre(self, client_pip):
        """CA-02: ?quarter=Q01_25 → solo ese trimestre."""
        url = reverse('pipeline:monitor-weekdays') + '?quarter=Q01_25'
        filtered = [r for r in MONITOR_ROWS if r['trimestre'] == 'Q01_25']
        with patch('apps.pipeline.monitor_weekday_views.connections') as mc:
            mc.__getitem__.return_value.cursor.return_value = _mock_cursor(filtered)
            response = client_pip.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert all(f['trimestre'] == 'Q01_25' for f in response.data['filas'])

    def test_it03_quarter_invalido_retorna_400(self, client_pip):
        """CA-03: formato inválido → 400."""
        url = reverse('pipeline:monitor-weekdays') + '?quarter=MALO'
        response = client_pip.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it04_resumen_incluye_alertas(self, client_pip):
        """CA-04: resumen indica cuántas filas tienen estado_monitor != OK."""
        url = reverse('pipeline:monitor-weekdays')
        with patch('apps.pipeline.monitor_weekday_views.connections') as mc:
            mc.__getitem__.return_value.cursor.return_value = _mock_cursor(MONITOR_ROWS)
            response = client_pip.get(url)

        assert 'resumen' in response.data
        assert 'total_filas' in response.data['resumen']
        assert 'alertas' in response.data['resumen']
        assert response.data['resumen']['alertas'] == 1  # Q02_26 ALERTA

    def test_it05_sin_datos_retorna_vacio(self, client_pip):
        """CA-05: sin datos → filas=[]."""
        url = reverse('pipeline:monitor-weekdays')
        with patch('apps.pipeline.monitor_weekday_views.connections') as mc:
            mc.__getitem__.return_value.cursor.return_value = _mock_cursor([])
            response = client_pip.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['filas'] == []
        assert response.data['resumen']['total_filas'] == 0

    def test_it06_mariadb_no_disponible_retorna_503(self, client_pip):
        """CA-06: MariaDB caída → 503."""
        url = reverse('pipeline:monitor-weekdays')
        from django.db import OperationalError
        with patch('apps.pipeline.monitor_weekday_views.connections') as mc:
            mc.__getitem__.return_value.cursor.side_effect = OperationalError('t')
            response = client_pip.get(url)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_sec01_sin_permiso_retorna_403(self, client_sin_pip):
        """SEC-01: sin PIP-001 → 403."""
        url = reverse('pipeline:monitor-weekdays')
        response = client_sin_pip.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_it07_decimales_serializados_como_float(self, client_pip):
        """CA-07: Decimal serializa como float."""
        url = reverse('pipeline:monitor-weekdays')
        with patch('apps.pipeline.monitor_weekday_views.connections') as mc:
            mc.__getitem__.return_value.cursor.return_value = _mock_cursor(MONITOR_ROWS)
            response = client_pip.get(url)

        fila = response.data['filas'][0]
        assert isinstance(fila['pct_entre_semana'], (int, float))
        assert isinstance(fila['total'], (int, float))
