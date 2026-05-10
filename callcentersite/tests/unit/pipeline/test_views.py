import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
User = get_user_model()
from django.urls import reverse
from rest_framework.test import APIClient
from datetime import date


@pytest.mark.unit
@pytest.mark.django_db
class TestETLStatusView:
    """Tests endpoint status ETL.

    Nota: etl_status consulta MariaDB ivr (connections['ivr']).
    Los tests unitarios mockean _get_pipeline_runs para no requerir
    esa conexion. Los tests de integracion reales estan en
    tests/integration/pipeline/test_ivr_endpoints.py.
    """

    def test_etl_status_requires_authentication(self):
        """Endpoint requiere autenticacion (CNST-005)."""
        client = APIClient()
        url = reverse('pipeline:etl-status')
        response = client.get(url)
        assert response.status_code == 401

    def test_etl_status_no_executions(self):
        """
        Status sin ejecuciones previas.
        Mockea _get_pipeline_runs — MariaDB ivr no disponible en tests unitarios.
        """
        user = User.objects.create_superuser(
            'testuser', email='su@t.com', password='test123')

        client = APIClient()
        client.force_authenticate(user=user)

        with patch('apps.pipeline.views._get_pipeline_runs', return_value=[]):
            url = reverse('pipeline:etl-status')
            response = client.get(url)

        assert response.status_code == 200

    def test_etl_status_with_execution(self):
        """
        Status con ejecucion reciente.
        Mockea _get_pipeline_runs — MariaDB ivr no disponible en tests unitarios.
        """
        from datetime import datetime, timezone as tz
        user = User.objects.create_superuser(
            'testuser2', email='su2@t.com', password='test123')

        client = APIClient()
        client.force_authenticate(user=user)

        fake_run = {
            'id':                 1,
            'tabla_origen':       'ivr_clientes',
            'quarter_name':       '2026Q1',
            'step_name':          'extract',
            'start_time':         datetime(2026, 1, 1, tzinfo=tz.utc),
            'end_time':           datetime(2026, 1, 2, tzinfo=tz.utc),
            'status':             'SUCCESS',
            'records_procesados': 1000,
            'duracion_seg':       3600,
            'error_message':      None,
            'ejecutado_por':      'system',
            'job_name':           'ivr_etl',
        }

        with patch('apps.pipeline.views._get_pipeline_runs',
                   return_value=[fake_run]):
            url = reverse('pipeline:etl-status')
            response = client.get(url)

        assert response.status_code == 200
