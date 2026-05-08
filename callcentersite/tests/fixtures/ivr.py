"""
tests/fixtures/ivr.py

Fixtures para tests de integración que usan la conexión 'ivr' (MariaDB).

Arquitectura (MIGRATE=False, CREATE_DB=False en testing_local.py):

    ensure_mariadb  — proceso mariadbd vivo + test_ivr_legacy existe
    ivr_schema      — tablas y SP sp_rpt_clientes en test_ivr_legacy
    ivr_job_*       — datos de job_execution_log para un test, limpia al final
    ivr_quarter_*   — datos base_ivr_clientes/detalle para un test, limpia

    test_ivr_legacy persiste entre sesiones de pytest.
    pytest-django no la toca (MIGRATE=False, CREATE_DB=False).
    Los fixtures de datos usan subprocess para garantizar COMMIT inmediato:
    los datos son visibles para el endpoint en cualquier conexión.

Escenario A confirmado (verificado 2026-05-08):
    sp_rpt_clientes no tiene prefijo 'ivr_legacy.' en el body del SP.
    El SP ejecuta contra la BD seleccionada en la conexión ('ivr' → test_ivr_legacy).
"""
import subprocess

import pytest

SOCKET = '/run/mysqld/mysqld.sock'
DB     = 'test_ivr_legacy'


def _sql(statements: str) -> subprocess.CompletedProcess:
    """Ejecuta SQL en test_ivr_legacy. Commit implícito."""
    return subprocess.run(
        ['mysql', f'--socket={SOCKET}', DB],
        input=statements, text=True, capture_output=True,
    )


# ---------------------------------------------------------------------------
# Constantes de schema — fuente única de verdad
# ---------------------------------------------------------------------------

_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS job_execution_log (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    job_name         VARCHAR(100) NOT NULL,
    quarter_name     VARCHAR(20),
    step_name        VARCHAR(50),
    tabla_origen     VARCHAR(100),
    start_time       DATETIME NOT NULL,
    end_time         DATETIME,
    status           ENUM('RUNNING','SUCCESS','PARTIAL','FAILED','SKIP','TIMEOUT')
                     NOT NULL DEFAULT 'RUNNING',
    records_procesados INT DEFAULT 0,
    duracion_seg     INT AS (TIMESTAMPDIFF(SECOND, start_time, end_time)) STORED,
    error_message    TEXT,
    ejecutado_por    VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS base_ivr_detalle (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    trimestre            VARCHAR(10) NOT NULL,
    fecha                VARCHAR(6)  NOT NULL,
    segmento             VARCHAR(20) NOT NULL,
    centro_transferencia VARCHAR(100) NOT NULL,
    menu                 VARCHAR(100) NOT NULL,
    opcion               VARCHAR(100) NOT NULL,
    total_llamadas       INT NOT NULL DEFAULT 0,
    misma_linea          INT NOT NULL DEFAULT 0,
    linea_diferente      INT NOT NULL DEFAULT 0,
    no_digito_telefono   INT NOT NULL DEFAULT 0,
    llamadas_entre_semana INT NOT NULL DEFAULT 0,
    llamadas_fines_semana INT NOT NULL DEFAULT 0,
    cargado_en           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_trimestre (trimestre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS base_ivr_clientes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    trimestre       VARCHAR(10) NOT NULL,
    segmento        VARCHAR(20) NOT NULL,
    clientes_unicos INT NOT NULL DEFAULT 0,
    cargado_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_grain (trimestre, segmento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

# SP sin prefijo de schema (Escenario A).
# Se recrea en test_ivr_legacy en cada sesión via ensure_mariadb → ivr_schema.
_SP_BODY = """\
CREATE PROCEDURE sp_rpt_clientes(IN p_quarter VARCHAR(10))
BEGIN
    SELECT
        c.trimestre,
        c.segmento,
        c.clientes_unicos,
        ROUND(
            c.clientes_unicos
            / (SELECT SUM(c2.clientes_unicos)
               FROM base_ivr_clientes c2
               WHERE c2.trimestre = p_quarter)
            * 100, 2
        ) AS pct_del_total,
        c.cargado_en AS ultima_actualizacion
    FROM base_ivr_clientes c
    WHERE c.trimestre = p_quarter
    ORDER BY c.clientes_unicos DESC;
END"""


# ---------------------------------------------------------------------------
# ivr_schema — session-scoped: crea tablas y SP una vez por sesión
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def ivr_schema(ensure_mariadb):
    """
    Crea el schema IVR en test_ivr_legacy.
    Depende de ensure_mariadb que garantiza que MariaDB corre y la DB existe.

    Crea: job_execution_log, base_ivr_detalle, base_ivr_clientes, sp_rpt_clientes.
    Idempotente: CREATE TABLE IF NOT EXISTS + DROP/CREATE para el SP.
    No destruye al final — test_ivr_legacy persiste entre sesiones.
    """
    _sql(_TABLES_SQL)

    # SP: DROP + CREATE para garantizar que está actualizado
    _sql("DROP PROCEDURE IF EXISTS sp_rpt_clientes;")
    subprocess.run(
        ['mysql', f'--socket={SOCKET}', DB,
         '--delimiter=$$', '-e', f'{_SP_BODY}$$'],
        capture_output=True,
    )

    yield
    # Sin teardown de schema — la DB persiste


# ---------------------------------------------------------------------------
# ivr_job_execution_data — datos de job_execution_log para un test
# ---------------------------------------------------------------------------

@pytest.fixture
def ivr_job_execution_data(ivr_schema):
    """
    Siembra job_execution_log con ejecuciones SUCCESS para Q01_25.
    Limpia al final del test.
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
# ivr_quarter_data — datos de clientes/detalle para un test
# ---------------------------------------------------------------------------

@pytest.fixture
def ivr_quarter_data(ivr_schema):
    """
    Siembra base_ivr_detalle y base_ivr_clientes con datos de Q01_25.
    Limpia al final del test.
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
