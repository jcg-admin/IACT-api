"""
tests/fixtures/ivr.py

Pytest fixtures for integration tests that use the 'ivr' MariaDB connection.

Usage:
    @pytest.mark.django_db(databases=['default', 'ivr'])
    def test_something(ivr_schema, ivr_job_execution_data):
        from apps.reports import ivr_services as svc
        clients = svc.get_clients('Q01_25')
        assert len(clients) >= 0
"""
import pytest
from django.db import connections


@pytest.fixture(scope='session')
def ivr_schema(django_db_setup, django_db_blocker):
    """
    Creates the minimum IVR schema needed for integration tests.

    Creates:
      - job_execution_log  (pipeline status tests)
      - base_ivr_detalle   (quarter validation and report tests)
      - base_ivr_clientes  (client report tests)

    Scope: session — created once, shared across all tests.
    CNST-003: uses connections['ivr'] directly (no Django ORM).
    """
    with django_db_blocker.unblock():
        with connections['ivr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_execution_log (
                    id               INT AUTO_INCREMENT PRIMARY KEY,
                    job_name         VARCHAR(100) NOT NULL,
                    quarter_name     VARCHAR(20),
                    step_name        VARCHAR(50),
                    tabla_origen     VARCHAR(100),
                    start_time       DATETIME NOT NULL,
                    end_time         DATETIME,
                    status           ENUM('RUNNING','SUCCESS','PARTIAL',
                                         'FAILED','SKIP','TIMEOUT')
                                     NOT NULL DEFAULT 'RUNNING',
                    records_procesados INT DEFAULT 0,
                    duracion_seg     INT AS (TIMESTAMPDIFF(SECOND, start_time, end_time)) STORED,
                    error_message    TEXT,
                    ejecutado_por    VARCHAR(50)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cursor.execute("""
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS base_ivr_clientes (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    trimestre   VARCHAR(10) NOT NULL,
                    segmento    VARCHAR(20) NOT NULL,
                    clientes    INT NOT NULL DEFAULT 0,
                    cargado_en  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
    yield
    # Cleanup: drop test tables after session
    with django_db_blocker.unblock():
        with connections['ivr'].cursor() as cursor:
            for table in ('base_ivr_clientes', 'base_ivr_detalle',
                          'job_execution_log'):
                cursor.execute(f"DROP TABLE IF EXISTS {table}")


@pytest.fixture
def ivr_job_execution_data(ivr_schema, django_db_blocker):
    """
    Seeds job_execution_log with test data for pipeline tests.
    Inserts rows for Q01_25 with SUCCESS status.
    """
    with django_db_blocker.unblock():
        with connections['ivr'].cursor() as cursor:
            cursor.execute("DELETE FROM job_execution_log")
            cursor.execute("""
                INSERT INTO job_execution_log
                    (job_name, quarter_name, step_name, tabla_origen,
                     start_time, end_time, status, records_procesados, ejecutado_por)
                VALUES
                    ('etl_Q01_25', 'Q01_25', 'etl_base_detalle', 'base_ivr_detalle',
                     NOW() - INTERVAL 1 HOUR, NOW(), 'SUCCESS', 1000, 'test'),
                    ('etl_Q01_25', 'Q01_25', 'etl_base_clientes', 'base_ivr_clientes',
                     NOW() - INTERVAL 30 MINUTE, NOW(), 'SUCCESS', 3, 'test')
            """)
    yield
    with django_db_blocker.unblock():
        with connections['ivr'].cursor() as cursor:
            cursor.execute("DELETE FROM job_execution_log")


@pytest.fixture
def ivr_quarter_data(ivr_schema, django_db_blocker):
    """
    Seeds base_ivr_detalle and base_ivr_clientes with test data for Q01_25.
    """
    with django_db_blocker.unblock():
        with connections['ivr'].cursor() as cursor:
            cursor.execute("DELETE FROM base_ivr_detalle")
            cursor.execute("DELETE FROM base_ivr_clientes")
            # base_ivr_detalle — sample rows
            cursor.execute("""
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
                     'Opcion1', 200, 120, 60, 20, 160, 40)
            """)
            # base_ivr_clientes — one row per segment
            cursor.execute("""
                INSERT INTO base_ivr_clientes
                    (trimestre, segmento, clientes)
                VALUES
                    ('Q01_25', 'nacional_A', 1500),
                    ('Q01_25', 'nacional_B', 800),
                    ('Q01_25', 'puebla', 400)
            """)
    yield
    with django_db_blocker.unblock():
        with connections['ivr'].cursor() as cursor:
            cursor.execute("DELETE FROM base_ivr_detalle")
            cursor.execute("DELETE FROM base_ivr_clientes")
