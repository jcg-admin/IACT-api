"""
tests/fixtures/ivr.py

Fixtures para tests de integración que usan la conexión 'ivr' (MariaDB).

Arquitectura:
    test_ivr_legacy persiste entre sesiones de pytest.
    pytest-django NO la destruye ni la gestiona (MIGRATE=False, CREATE_DB=False).
    El schema se crea una vez en el conftest de integración (ensure_mariadb).

    Los fixtures de datos usan subprocess para insertar y limpiar.
    Esto garantiza COMMIT inmediato — los datos son visibles para el endpoint
    en cualquier conexión, incluyendo la del request Django del test.

Responsabilidades:
    ivr_schema            — verifica que las tablas existen (session-scoped)
    ivr_job_execution_data — siembra job_execution_log, limpia al final
    ivr_quarter_data       — siembra base_ivr_clientes + detalle, limpia al final
"""
import subprocess

import pytest
from django.db import connections


SOCKET = '/run/mysqld/mysqld.sock'
DB     = 'test_ivr_legacy'


def _sql(statements: str) -> subprocess.CompletedProcess:
    """Ejecuta SQL directamente en test_ivr_legacy via mysql CLI.
    Commit implícito — los datos son visibles para todas las conexiones.
    """
    return subprocess.run(
        ['mysql', f'--socket={SOCKET}', DB],
        input=statements,
        text=True,
        capture_output=True,
    )


# ---------------------------------------------------------------------------
# ivr_schema — session-scoped, verifica que el schema existe
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def ivr_schema(ensure_mariadb):
    """
    Garantiza que test_ivr_legacy tiene el schema IVR mínimo.
    El schema lo crea ensure_mariadb (conftest de integración).
    Este fixture es el punto de dependencia declarativa para los fixtures
    de datos — hace que el orden de setup sea explícito.

    No destruye tablas al final: test_ivr_legacy persiste entre sesiones.
    """
    # Verificar que las tablas existen — si no, el conftest falló
    result = _sql("SHOW TABLES;")
    tables = result.stdout.strip().splitlines()
    required = {'job_execution_log', 'base_ivr_detalle', 'base_ivr_clientes'}
    missing  = required - set(tables)
    if missing:
        pytest.fail(
            f"test_ivr_legacy no tiene las tablas requeridas: {missing}. "
            "Verificar ensure_mariadb en conftest de integración."
        )
    yield
    # Sin teardown — la DB persiste entre sesiones


# ---------------------------------------------------------------------------
# ivr_job_execution_data — datos para TestETLStatus y TestETLLogTail
# ---------------------------------------------------------------------------

@pytest.fixture
def ivr_job_execution_data(ivr_schema):
    """
    Siembra job_execution_log con ejecuciones SUCCESS para Q01_25.
    Usa subprocess — commit inmediato, visible para el endpoint.
    """
    _sql("""
        DELETE FROM job_execution_log;
        INSERT INTO job_execution_log
            (job_name, quarter_name, step_name, tabla_origen,
             start_time, end_time, status, records_procesados, ejecutado_por)
        VALUES
            ('etl_Q01_25', 'Q01_25', 'etl_base_detalle', 'base_ivr_detalle',
             NOW() - INTERVAL 1 HOUR, NOW(), 'SUCCESS', 1000, 'test'),
            ('etl_Q01_25', 'Q01_25', 'etl_base_clientes', 'base_ivr_clientes',
             NOW() - INTERVAL 30 MINUTE, NOW(), 'SUCCESS', 3, 'test');
    """)
    yield
    _sql("DELETE FROM job_execution_log;")


# ---------------------------------------------------------------------------
# ivr_quarter_data — datos para TestIVRClientsReport
# ---------------------------------------------------------------------------

@pytest.fixture
def ivr_quarter_data(ivr_schema):
    """
    Siembra base_ivr_detalle y base_ivr_clientes con datos de Q01_25.
    Usa subprocess — commit inmediato, visible para sp_rpt_clientes.
    """
    _sql("""
        DELETE FROM base_ivr_detalle;
        DELETE FROM base_ivr_clientes;

        INSERT INTO base_ivr_detalle
            (trimestre, fecha, segmento, centro_transferencia, menu, opcion,
             total_llamadas, misma_linea, linea_diferente, no_digito_telefono,
             llamadas_entre_semana, llamadas_fines_semana)
        VALUES
            ('Q01_25', '202501', 'nacional_A', 'CentroA', 'MenuPrincipal',
             'Opcion1', 500, 300, 150, 50, 400, 100),
            ('Q01_25', '202502', 'nacional_B', 'CentroB', 'MenuPrincipal',
             'Opcion2', 300, 200, 80, 20, 250, 50),
            ('Q01_25', '202503', 'puebla', 'CentroC', 'MenuSecundario',
             'Opcion1', 200, 120, 60, 20, 160, 40);

        INSERT INTO base_ivr_clientes
            (trimestre, segmento, clientes_unicos)
        VALUES
            ('Q01_25', 'nacional_A', 1500),
            ('Q01_25', 'nacional_B', 800),
            ('Q01_25', 'puebla', 400);
    """)
    yield
    _sql("""
        DELETE FROM base_ivr_detalle;
        DELETE FROM base_ivr_clientes;
    """)
