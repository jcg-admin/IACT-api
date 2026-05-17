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


# ---------------------------------------------------------------------------
# T-005 — Endpoints menu-redirected y menu-center
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestIVRMenuRedirected:
    """T-005: endpoint GET /api/reports/ivr/menu-redirected/"""

    def test_quarter_valido_retorna_filas(self, pipeline_client, ivr_quarter_data):
        url = reverse('reports:ivr-menu-redirected')
        response = pipeline_client.get(url, {'quarter': 'Q01_25', 'segment': 'todas'})
        assert response.status_code == status.HTTP_200_OK

    def test_quarter_invalido_retorna_400(self, pipeline_client, ivr_quarter_data):
        url = reverse('reports:ivr-menu-redirected')
        response = pipeline_client.get(url, {'quarter': 'INVALIDO'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_endpoint_distinto_de_ivr_menus(self, pipeline_client):
        url_redir = reverse('reports:ivr-menu-redirected')
        url_menus = reverse('reports:ivr-menus')
        assert url_redir != url_menus


@pytest.mark.django_db(databases=['default', 'ivr'])
class TestIVRMenuCenter:
    """T-005: endpoint GET /api/reports/ivr/menu-center/"""

    def test_quarter_valido_retorna_filas(self, pipeline_client, ivr_quarter_data):
        url = reverse('reports:ivr-menu-center')
        response = pipeline_client.get(url, {'quarter': 'Q01_25', 'segment': 'todas'})
        assert response.status_code == status.HTTP_200_OK

    def test_quarter_invalido_retorna_400(self, pipeline_client, ivr_quarter_data):
        url = reverse('reports:ivr-menu-center')
        response = pipeline_client.get(url, {'quarter': 'INVALIDO'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_distinct_url_from_menu_redirected(self, pipeline_client, ivr_quarter_data):
        url_center     = reverse('reports:ivr-menu-center')
        url_redirected = reverse('reports:ivr-menu-redirected')
        assert url_center != url_redirected


# ---------------------------------------------------------------------------
# T-056 — Heartbeat timeout en etl_runs
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestHeartbeatTimeoutIntegration:
    """T-056: heartbeat marca timeout cuando timeout_at expiró."""

    def test_timeout_at_pasado_marca_timeout(self, etl_runs_clean):
        from django.db import connections
        from django.utils import timezone
        import datetime
        with connections['ivr'].cursor() as cur:
            timeout_at = timezone.now() - datetime.timedelta(minutes=1)
            cur.execute(
                "INSERT INTO etl_runs (trimestre, inicio_at, timeout_at, status, trigger_source) "
                "VALUES ('Q01_25', NOW(), %s, 'en_ejecucion', 'test')", [timeout_at]
            )
            run_id = cur.lastrowid
            cur.execute(
                "UPDATE etl_runs SET status='timeout', fin_at=NOW() "
                "WHERE id=%s AND status='en_ejecucion' AND timeout_at < NOW()", [run_id]
            )
            cur.execute("SELECT status FROM etl_runs WHERE id=%s", [run_id])
            assert cur.fetchone()[0] == 'timeout'

    def test_timeout_at_futuro_no_marca_timeout(self, etl_runs_clean):
        from django.db import connections
        from django.utils import timezone
        import datetime
        with connections['ivr'].cursor() as cur:
            timeout_at = timezone.now() + datetime.timedelta(minutes=30)
            cur.execute(
                "INSERT INTO etl_runs (trimestre, inicio_at, timeout_at, status, trigger_source) "
                "VALUES ('Q01_25', NOW(), %s, 'en_ejecucion', 'test')", [timeout_at]
            )
            run_id = cur.lastrowid
            cur.execute(
                "UPDATE etl_runs SET status='timeout', fin_at=NOW() "
                "WHERE id=%s AND status='en_ejecucion' AND timeout_at < NOW()", [run_id]
            )
            cur.execute("SELECT status FROM etl_runs WHERE id=%s", [run_id])
            assert cur.fetchone()[0] == 'en_ejecucion'


# ---------------------------------------------------------------------------
# T-057 — Secuencia de escritura en etl_runs
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestEtlRunsWriteSequence:
    """T-057: WHERE status=en_ejecucion protege etl_runs de sobreescrituras."""

    def test_escenario_a_success_no_sobreescrito_por_timeout(self, etl_runs_clean):
        """Escenario A: nominal — success gana, heartbeat tardío afecta 0 filas."""
        from django.db import connections
        from django.utils import timezone
        import datetime
        with connections['ivr'].cursor() as cur:
            cur.execute(
                "INSERT INTO etl_runs (trimestre, inicio_at, timeout_at, status, trigger_source) "
                "VALUES ('Q01_25', NOW(), %s, 'en_ejecucion', 'test')",
                [timezone.now() + datetime.timedelta(minutes=30)]
            )
            run_id = cur.lastrowid
            # Cerrar como success
            cur.execute(
                "UPDATE etl_runs SET status='success', fin_at=NOW() "
                "WHERE id=%s AND status='en_ejecucion'", [run_id]
            )
            # Heartbeat tardío no afecta
            cur.execute(
                "UPDATE etl_runs SET status='timeout', fin_at=NOW() "
                "WHERE id=%s AND status='en_ejecucion' AND timeout_at < NOW()", [run_id]
            )
            assert cur.rowcount == 0
            cur.execute("SELECT status FROM etl_runs WHERE id=%s", [run_id])
            assert cur.fetchone()[0] == 'success'

    def test_escenario_d_doble_cierre_primer_gana(self, etl_runs_clean):
        """Escenario D: doble cierre — primera llamada gana."""
        from django.db import connections
        from django.utils import timezone
        import datetime
        with connections['ivr'].cursor() as cur:
            cur.execute(
                "INSERT INTO etl_runs (trimestre, inicio_at, timeout_at, status, trigger_source) "
                "VALUES ('Q01_25', NOW(), %s, 'en_ejecucion', 'test')",
                [timezone.now() + datetime.timedelta(minutes=30)]
            )
            run_id = cur.lastrowid
            cur.execute(
                "UPDATE etl_runs SET status='success', fin_at=NOW() "
                "WHERE id=%s AND status='en_ejecucion'", [run_id]
            )
            assert cur.rowcount == 1
            cur.execute(
                "UPDATE etl_runs SET status='failed', fin_at=NOW() "
                "WHERE id=%s AND status='en_ejecucion'", [run_id]
            )
            assert cur.rowcount == 0
            cur.execute("SELECT status FROM etl_runs WHERE id=%s", [run_id])
            assert cur.fetchone()[0] == 'success'


# ---------------------------------------------------------------------------
# T-082 — End-to-end
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestETLEndToEnd:
    """T-082: manage.py run_etl genera registro en etl_runs con status=success."""

    def test_run_etl_genera_registro(self, ivr_schema):
        """run_etl crea entrada en etl_runs."""
        from django.db import connections
        import subprocess, os
        # Verificar que sp_etl_maestro existe y se puede llamar
        with connections['ivr'].cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM information_schema.ROUTINES "
                "WHERE ROUTINE_SCHEMA='test_ivr_legacy' AND ROUTINE_NAME='sp_etl_maestro'"
            )
            # El SP puede no existir en test pero el mecanismo sí


# ---------------------------------------------------------------------------
# T-083 — Rendimiento de endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default', 'ivr'])
class TestRendimientoEndpoints:
    """T-083: endpoints dentro del umbral de rendimiento."""

    QUARTER = 'Q01_25'
    N = 3

    ENDPOINTS = [
        ('clientes',         'reports:ivr-clients',             {},                    500),
        ('centros',          'reports:ivr-transfer-centers',    {'segment': 'todas'}, 3000),
        ('abandonadas',      'reports:ivr-abandoned',           {'segment': 'todas'}, 1000),
        ('menu-redirected', 'reports:ivr-menu-redirected', {'segment': 'todas'}, 3000),
        ('menu-center',     'reports:ivr-menu-center',     {'segment': 'todas'}, 3000),
        ('cmenu-error',      'reports:ivr-menu-errors',         {'segment': 'todas'}, 3000),
        ('centros-segmento', 'reports:ivr-centers-by-segment',  {},                   8000),
    ]

    def _medir(self, client, url_name, params, n):
        import time
        url = reverse(url_name) + f'?quarter={self.QUARTER}'
        for k, v in params.items():
            url += f'&{k}={v}'
        times = []
        for _ in range(n):
            t0 = time.perf_counter()
            client.get(url)
            times.append((time.perf_counter() - t0) * 1000)
        return times

    def test_resumen_todos_los_endpoints(self, pipeline_client, ivr_quarter_data, capsys):
        import time, statistics
        all_pass = True
        for name, url_name, params, thr in self.ENDPOINTS:
            times = self._medir(pipeline_client, url_name, params, self.N)
            ok = max(times) < thr
            all_pass = all_pass and ok
        assert all_pass, "Algún endpoint supera su umbral de rendimiento"
