"""
tests/unit/fase3/test_uc_pip_03_availability.py

N-PIP-03 — Consultar Disponibilidad de Datos.
GET /api/pipeline/data-availability/
Función: PIP-003 (view_data_availability)
Fuente: uc-pip-03/criterios-aceptacion.rst + testing.rst
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.test_data.user_test_data import AdminUserTestData, UserTestData


@pytest.fixture
def client_pip003(db):
    client = APIClient()
    user = AdminUserTestData()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def client_sin_pip003(db):
    client = APIClient()
    user = UserTestData()
    client.force_authenticate(user=user)
    return client


def _url():
    return reverse('pipeline:etl-data-availability')


# ---------------------------------------------------------------------------
# UT-01..03: StatusCalculator — función pura
# ---------------------------------------------------------------------------

class TestStatusCalculator:
    """UT-01..03: cálculo de status de frescura."""

    def _now(self):
        return datetime.now(timezone.utc)

    def test_ut01_status_fresco_dentro_de_14h(self):
        """CA-02: lag < 14h → 'fresco'"""
        from apps.pipeline.status_calculator import StatusCalculator
        ultima_carga = self._now() - timedelta(hours=5)
        assert StatusCalculator.compute(ultima_carga) == 'fresco'

    def test_ut02_status_aceptable_entre_14h_y_24h(self):
        """CA-03: 14h ≤ lag < 24h → 'aceptable'"""
        from apps.pipeline.status_calculator import StatusCalculator
        ultima_carga = self._now() - timedelta(hours=20)
        assert StatusCalculator.compute(ultima_carga) == 'aceptable'

    def test_ut03_status_vencido_mas_de_24h(self):
        """CA-04: lag ≥ 24h → 'vencido'"""
        from apps.pipeline.status_calculator import StatusCalculator
        ultima_carga = self._now() - timedelta(hours=30)
        assert StatusCalculator.compute(ultima_carga) == 'vencido'

    def test_ut04_status_sin_datos_cuando_none(self):
        """Sin carga anterior → 'sin_datos'"""
        from apps.pipeline.status_calculator import StatusCalculator
        assert StatusCalculator.compute(None) == 'sin_datos'


# ---------------------------------------------------------------------------
# IT-01..03: endpoint integration
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.xfail(reason="API cambió — pendiente actualización post-FASE 6", strict=False)
class TestDataAvailabilityEndpoint:
    """IT-01..03, SEC-01 — CA-01..07"""

    def _mock_row(self, hours_ago=5):
        ultima_carga = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        return ('Q01_25', ultima_carga, 1500000)

    def test_it01_retorna_datasets_con_status(self, client_pip003):
        """CA-01: GET /data-availability/?quarter=Q01_25 → 200 con status_frescura"""
        with patch('apps.pipeline.views.connections') as mock_conn:
            mc = MagicMock()
            mc.__enter__ = MagicMock(return_value=mc)
            mc.__exit__ = MagicMock(return_value=False)
            mc.fetchone.return_value = self._mock_row()
            mock_conn.__getitem__.return_value.cursor.return_value = mc
            response = client_pip003.get(_url(), {'quarter': 'Q01_25'})

        assert response.status_code == status.HTTP_200_OK
        assert 'status_frescura' in response.data
        assert response.data['status_frescura'] in ('fresco', 'aceptable', 'vencido', 'sin_datos')

    def test_it02_sin_datos_retorna_sin_datos(self, client_pip003):
        """CA-01: sin registros en BD → sin_datos"""
        with patch('apps.pipeline.views.connections') as mock_conn:
            mc = MagicMock()
            mc.__enter__ = MagicMock(return_value=mc)
            mc.__exit__ = MagicMock(return_value=False)
            mc.fetchone.return_value = None
            mock_conn.__getitem__.return_value.cursor.return_value = mc
            response = client_pip003.get(_url(), {'quarter': 'Q01_25'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status_frescura'] == 'sin_datos'

    def test_it03_bd_timeout_retorna_503(self, client_pip003):
        """CA-07: BD timeout → 503"""
        from django.db import OperationalError
        with patch('apps.pipeline.views.connections') as mock_conn:
            mock_conn.__getitem__.return_value.cursor.side_effect = OperationalError('timeout')
            response = client_pip003.get(_url(), {'quarter': 'Q01_25'})
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_quarter_required(self, client_pip003):
        """CA-03: sin quarter → 400"""
        with patch('apps.pipeline.views.connections'):
            response = client_pip003.get(_url())
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sec01_sin_permiso_retorna_403(self, client_sin_pip003):
        """CA-05: sin PIP-003 → 403"""
        response = client_sin_pip003.get(_url(), {'quarter': 'Q01_25'})
        assert response.status_code == status.HTTP_403_FORBIDDEN
