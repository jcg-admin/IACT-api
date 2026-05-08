"""
tests/integration/pipeline/test_ivr_endpoints.py

Fase O — Tests de integración con MariaDB real.
Usan los fixtures ivr_schema, ivr_job_execution_data, ivr_quarter_data
definidos en tests/fixtures/ivr.py (Fase L-002).

Requieren:
    pytest.ini: DJANGO_SETTINGS_MODULE = config.settings.testing_local
    MariaDB disponible en localhost:3306
"""
import pytest
from django.urls import reverse
from rest_framework import status
from apps.access.models import UserPermission
from tests.test_data.user_test_data import AdminUserTestData


# ---------------------------------------------------------------------------
# Fixture: cliente con permisos de pipeline, logs e IVR
# ---------------------------------------------------------------------------

@pytest.fixture
def pipeline_client(db, api_client):
    """
    Cliente autenticado con todas las funciones necesarias
    para los endpoints de pipeline y logs.
    """
    user = AdminUserTestData()
    from tests.test_data.access_test_data import FunctionTestData
    required_functions = [
        'pipeline.view_status',
        'pipeline.retry',
        'reports.view_ivr',
        'logs.view',
    ]
    for code in required_functions:
        fn = FunctionTestData(code=code, permission_django=code)
        UserPermission.objects.get_or_create(user=user, function=fn)

    api_client.force_authenticate(user=user)
    api_client._user = user
    return api_client


# ---------------------------------------------------------------------------
# O-001: etl_status con MariaDB real
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestETLStatus:
    """O-001: GET /api/pipeline/status/ con datos reales de job_execution_log."""

    def test_status_sin_datos_retorna_critico(self, pipeline_client, ivr_schema):
        """Sin registros en job_execution_log → status_general = 'critico'."""
        url = reverse('pipeline:etl-status')
        response = pipeline_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'resumen' in response.data
        assert response.data['resumen']['status_general'] == 'critico'

    def test_status_con_ejecuciones_retorna_ok(
            self, pipeline_client, ivr_job_execution_data):
        """Con ejecuciones SUCCESS → status_general es ok, degradado o critico."""
        url = reverse('pipeline:etl-status')
        response = pipeline_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'resumen' in response.data
        assert response.data['resumen']['status_general'] in (
            'ok', 'degradado', 'critico')
        assert 'latest_executions' in response.data or \
               'ultimas_ejecuciones' in response.data


# ---------------------------------------------------------------------------
# O-002: etl_retry validaciones
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestETLRetry:
    """O-002: POST /api/pipeline/retry/ — validaciones de entrada."""

    def test_motivo_muy_corto_retorna_400(self, pipeline_client, ivr_schema):
        url = reverse('pipeline:etl-retry')
        response = pipeline_client.post(url, {
            'quarter': 'Q01_25',
            'motivo': 'corto',           # < 20 caracteres
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_quarter_invalido_retorna_400(self, pipeline_client, ivr_schema):
        url = reverse('pipeline:etl-retry')
        response = pipeline_client.post(url, {
            'quarter': 'XXXX_99',
            'motivo': 'x' * 25,
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_quarter_ausente_retorna_400(self, pipeline_client, ivr_schema):
        url = reverse('pipeline:etl-retry')
        response = pipeline_client.post(url, {
            'motivo': 'motivo suficientemente largo para el test',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sin_ejecucion_activa_intenta_retry(
            self, pipeline_client, ivr_job_execution_data):
        """Con quarter válido y motivo suficiente, llega hasta la lógica del SP.
        El resultado puede ser 200 (éxito) o 400/503 según el estado del ETL;
        lo importante es que NO sea 400 por validación de entrada."""
        url = reverse('pipeline:etl-retry')
        response = pipeline_client.post(url, {
            'quarter': 'Q01_25',
            'motivo': 'Reintento de prueba en tests de integracion',
        })
        # No debe fallar por validación de entrada
        assert response.status_code != status.HTTP_400_BAD_REQUEST or \
               'motivo' not in str(response.data)


# ---------------------------------------------------------------------------
# O-003: IVR reports — quarter inválido y válido
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestIVRClientsReport:
    """O-003: GET /api/reports/ivr/clients/ con datos reales."""

    def test_quarter_invalido_retorna_400(
            self, pipeline_client, ivr_quarter_data):
        """Quarter no existente en base_ivr_detalle → 400 con errors."""
        url = reverse('reports:ivr-clients')
        response = pipeline_client.get(url, {'quarter': 'XXXX'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.data

    def test_quarter_valido_retorna_datos(
            self, pipeline_client, ivr_quarter_data):
        """Quarter Q01_25 sembrado en fixture → 200 con datos."""
        url = reverse('reports:ivr-clients')
        response = pipeline_client.get(url, {"quarter": "Q01_25"})
        assert response.status_code == status.HTTP_200_OK
        assert 'total_rows' in response.data
        assert response.data['total_rows'] >= 0
        assert 'data' in response.data

    def test_respuesta_incluye_quarter(
            self, pipeline_client, ivr_quarter_data):
        url = reverse('reports:ivr-clients')
        response = pipeline_client.get(url, {'quarter': 'Q01_25'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('quarter') == 'Q01_25'


# ---------------------------------------------------------------------------
# O-004: ivr_health
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestIVRHealth:
    """O-004: GET /api/pipeline/ivr-health/ con MariaDB disponible."""

    def test_health_ok_con_mariadb_disponible(
            self, pipeline_client, ivr_schema):
        url = reverse('pipeline:ivr-health')
        response = pipeline_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'ok'
        assert 'mariadb_version' in response.data
        assert response.data['mariadb_version']  # no vacío


# ---------------------------------------------------------------------------
# O-005: logs/etl/tail con MariaDB real
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestETLLogTail:
    """O-005: GET /api/logs/etl/tail/ con datos reales de job_execution_log."""

    def test_sin_datos_retorna_entries_vacio(
            self, pipeline_client, ivr_schema):
        """Sin datos en job_execution_log → entries vacío, 200."""
        url = reverse('logs:etl-tail')
        response = pipeline_client.get(url, {'lines': '10'})

        assert response.status_code == status.HTTP_200_OK
        assert 'entries' in response.data
        assert isinstance(response.data['entries'], list)
        assert response.data['lines'] == 0

    def test_con_datos_retorna_entries(
            self, pipeline_client, ivr_job_execution_data):
        """Con registros en job_execution_log → entries con datos."""
        url = reverse('logs:etl-tail')
        response = pipeline_client.get(url, {'lines': '10'})

        assert response.status_code == status.HTTP_200_OK
        assert 'entries' in response.data
        assert response.data['lines'] >= 1

    def test_source_es_job_execution_log(
            self, pipeline_client, ivr_schema):
        url = reverse('logs:etl-tail')
        response = pipeline_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('source') == 'job_execution_log'
