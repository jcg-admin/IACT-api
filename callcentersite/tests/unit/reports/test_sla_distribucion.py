"""
tests/unit/reports/test_sla_distribucion.py

TDD — Reporte SLA por trimestre via v_sla_distribucion.

Endpoint:
  GET /api/reports/ivr/sla/   RPT-019  view_ivr_reports

Contrato de v_sla_distribucion:
  trimestre, fuera_sla, riesgo_sla, dentro_sla, activo_hoy,
  volumen_medio, bajo_volumen, total_centros
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def client_rpt(db):
    client = APIClient()
    client.force_authenticate(user=AdminUserTestData())
    return client

@pytest.fixture
def client_sin_rpt(db):
    client = APIClient()
    client.force_authenticate(user=UserTestData())
    return client


SLA_ROWS = [
    {'trimestre': 'Q01_25', 'fuera_sla': Decimal('24'), 'riesgo_sla': Decimal('0'),
     'dentro_sla': Decimal('0'), 'activo_hoy': Decimal('0'),
     'volumen_medio': Decimal('36'), 'bajo_volumen': Decimal('24'),
     'total_centros': 84},
    {'trimestre': 'Q02_25', 'fuera_sla': Decimal('23'), 'riesgo_sla': Decimal('0'),
     'dentro_sla': Decimal('0'), 'activo_hoy': Decimal('0'),
     'volumen_medio': Decimal('42'), 'bajo_volumen': Decimal('26'),
     'total_centros': 91},
    {'trimestre': 'Q02_26', 'fuera_sla': Decimal('18'), 'riesgo_sla': Decimal('4'),
     'dentro_sla': Decimal('2'), 'activo_hoy': Decimal('1'),
     'volumen_medio': Decimal('38'), 'bajo_volumen': Decimal('21'),
     'total_centros': 84},
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


class TestSLADistribucionEndpoint:
    """Reporte SLA por trimestre — v_sla_distribucion."""

    def test_it01_retorna_todos_los_trimestres(self, client_rpt):
        """CA-01: sin filtro → todos los trimestres con categorias SLA."""
        url = reverse('reports:ivr-sla')
        with patch('apps.reports.sla_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_cursor(SLA_ROWS)
            response = client_rpt.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'trimestres' in response.data
        assert len(response.data['trimestres']) == 3

        t = response.data['trimestres'][0]
        assert t['trimestre'] == 'Q01_25'
        assert 'fuera_sla' in t
        assert 'riesgo_sla' in t
        assert 'dentro_sla' in t
        assert 'total_centros' in t

    def test_it02_filtra_por_trimestre(self, client_rpt):
        """CA-02: ?quarter=Q02_26 → solo ese trimestre."""
        url = reverse('reports:ivr-sla') + '?quarter=Q02_26'
        filtered = [r for r in SLA_ROWS if r['trimestre'] == 'Q02_26']
        with patch('apps.reports.sla_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_cursor(filtered)
            response = client_rpt.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['trimestres']) == 1
        assert response.data['trimestres'][0]['trimestre'] == 'Q02_26'

    def test_it03_quarter_invalido_retorna_400(self, client_rpt):
        """CA-03: quarter con formato inválido → 400."""
        url = reverse('reports:ivr-sla') + '?quarter=INVALIDO'
        response = client_rpt.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_it04_sin_datos_retorna_lista_vacia(self, client_rpt):
        """CA-04: sin datos → 200 con trimestres=[]."""
        url = reverse('reports:ivr-sla')
        with patch('apps.reports.sla_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = _mock_cursor([])
            response = client_rpt.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['trimestres'] == []

    def test_it05_incluye_resumen_global(self, client_rpt):
        """CA-05: respuesta incluye resumen con total de centros únicos."""
        url = reverse('reports:ivr-sla')
        with patch('apps.reports.sla_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_cursor(SLA_ROWS)
            response = client_rpt.get(url)

        assert 'resumen' in response.data
        assert 'trimestres_con_datos' in response.data['resumen']
        assert response.data['resumen']['trimestres_con_datos'] == 3

    def test_it06_mariadb_no_disponible_retorna_503(self, client_rpt):
        """CA-06: MariaDB caída → 503."""
        url = reverse('reports:ivr-sla')
        from django.db import OperationalError
        with patch('apps.reports.sla_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.side_effect = OperationalError('t')
            response = client_rpt.get(url)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_sec01_sin_permiso_retorna_403(self, client_sin_rpt):
        """SEC-01: sin RPT-019 → 403."""
        url = reverse('reports:ivr-sla')
        response = client_sin_rpt.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_it07_valores_decimales_serializables(self, client_rpt):
        """CA-07: Decimal serializa correctamente a número."""
        url = reverse('reports:ivr-sla')
        with patch('apps.reports.sla_views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.return_value = \
                _mock_cursor(SLA_ROWS)
            response = client_rpt.get(url)

        t = response.data['trimestres'][0]
        # Deben ser int o float, no Decimal
        assert isinstance(t['fuera_sla'], (int, float))
        assert isinstance(t['total_centros'], (int, float))
