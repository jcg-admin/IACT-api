"""
tests/integration/pipeline/conftest.py

Gestión del ciclo de vida de MariaDB para tests de integración IVR.

En el entorno de desarrollo (sandbox sin systemd), MariaDB no persiste
entre comandos shell. Este conftest lo arranca como proceso HIJO de pytest
usando subprocess.Popen directo a mariadbd (sin capa runuser).

La clave: Popen tiene referencia directa a mariadbd.
El proceso vive mientras el fixture vive — que es toda la sesión de pytest.

Ver: IACT-db/docs/architecture/HALLAZGOS-ENTORNO.md H-001-01
"""
import os
import pwd
import subprocess
import time

import pytest
from django.db import connections


def _mariadb_alive() -> bool:
    result = subprocess.run(
        ['mysql', '--socket=/run/mysqld/mysqld.sock', '-e', 'SELECT 1;'],
        capture_output=True, timeout=3,
    )
    return result.returncode == 0


def _create_schema():
    """
    Crea test_ivr_legacy con el schema mínimo necesario para los tests IVR.
    Idempotente: usa CREATE TABLE IF NOT EXISTS y CREATE PROCEDURE IF NOT EXISTS.
    Con MIGRATE=False y CREATE_DB=False, pytest-django no toca esta DB.
    La DB persiste entre sesiones de pytest — se recrea solo si MariaDB reinicia.
    """
    sql = """
        CREATE DATABASE IF NOT EXISTS test_ivr_legacy CHARACTER SET utf8mb4;
        USE test_ivr_legacy;

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
    subprocess.run(
        ['mysql', '--socket=/run/mysqld/mysqld.sock'],
        input=sql, text=True, capture_output=True,
    )

    # SP: DROP primero, luego CREATE con DELIMITER $$ para que el parser
    # no confunda los ; internos del BEGIN...END con fin de sentencia.
    subprocess.run(
        ['mysql', '--socket=/run/mysqld/mysqld.sock', 'test_ivr_legacy',
         '-e', 'DROP PROCEDURE IF EXISTS sp_rpt_clientes;'],
        capture_output=True,
    )
    sp_body = (
        'CREATE PROCEDURE sp_rpt_clientes(IN p_quarter VARCHAR(10))\n'
        'BEGIN\n'
        '    SELECT\n'
        '        c.trimestre,\n'
        '        c.segmento,\n'
        '        c.clientes_unicos,\n'
        '        ROUND(\n'
        '            c.clientes_unicos\n'
        '            / (SELECT SUM(c2.clientes_unicos)\n'
        '               FROM base_ivr_clientes c2\n'
        '               WHERE c2.trimestre = p_quarter)\n'
        '            * 100, 2\n'
        '        ) AS pct_del_total,\n'
        '        c.cargado_en AS ultima_actualizacion\n'
        '    FROM base_ivr_clientes c\n'
        '    WHERE c.trimestre = p_quarter\n'
        '    ORDER BY c.clientes_unicos DESC;\n'
        'END'
    )
    subprocess.run(
        ['mysql', '--socket=/run/mysqld/mysqld.sock',
         'test_ivr_legacy',
         '--delimiter=$$',
         '-e', f'{sp_body}$$'],
        capture_output=True,
    )


@pytest.fixture(scope='session', autouse=True)
def ensure_mariadb():
    """
    Session-scoped fixture que garantiza que MariaDB está disponible
    durante toda la sesión de pytest.

    Usa subprocess.Popen directo a mariadbd con preexec_fn para bajar
    privilegios. Esto elimina la capa de runuser que causaba que el
    proceso quedara huérfano cuando runuser terminaba.
    """
    proc = None

    if not _mariadb_alive():
        mysql_uid = pwd.getpwnam('mysql').pw_uid
        mysql_gid = pwd.getpwnam('mysql').pw_gid

        os.makedirs('/run/mysqld', exist_ok=True)
        try:
            os.chown('/run/mysqld', mysql_uid, mysql_gid)
        except PermissionError:
            pass

        for f in ('/run/mysqld/mysqld.sock', '/run/mysqld/mysqld.pid'):
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

        def drop_privs():
            os.setgid(mysql_gid)
            os.setuid(mysql_uid)

        proc = subprocess.Popen(
            [
                '/usr/sbin/mariadbd',
                '--user=mysql',
                '--socket=/run/mysqld/mysqld.sock',
                '--datadir=/var/lib/mysql',
                '--pid-file=/run/mysqld/mysqld.pid',
                '--skip-grant-tables',
                '--innodb-buffer-pool-size=64M',
            ],
            preexec_fn=drop_privs,
            stderr=open('/tmp/mdb_conftest.log', 'w'),
            stdout=subprocess.DEVNULL,
        )

        for _ in range(30):
            if _mariadb_alive():
                break
            if proc.poll() is not None:
                pytest.exit('mariadbd murió durante el arranque')
            time.sleep(1)
        else:
            proc.terminate()
            pytest.exit('MariaDB no arrancó en 30s')

    # Schema mínimo para etl_status (job_execution_log)
    _create_schema()

    yield

    if proc is not None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
