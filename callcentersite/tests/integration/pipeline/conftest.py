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
    Crea test_ivr_legacy si no existe.
    Responsabilidad: existencia de la BD.
    El schema (tablas, SPs) es responsabilidad de ivr_schema.
    """
    subprocess.run(
        ['mysql', '--socket=/run/mysqld/mysqld.sock', '-e',
         'CREATE DATABASE IF NOT EXISTS test_ivr_legacy '
         'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'],
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
