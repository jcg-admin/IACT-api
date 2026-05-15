"""
tests/unit/conftest.py

Fixtures compartidas para todos los tests unit/.
Reemplaza los conftest.py eliminados de fase0/, fase1/, fase2/
durante la remediación DT-NAMING-001 (commit d178bfc).

H-F6-GRP-GA-001: throttle deshabilitado globalmente en fase0_testing settings.
"""
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from io import StringIO
from django.core.management import call_command


@pytest.fixture
def api_client():
    """Cliente API sin autenticación."""
    return APIClient()


@pytest.fixture
def db_with_catalog(db):
    """BD con catálogo de funciones y access groups populados."""
    call_command('create_functions', stdout=StringIO())
    call_command('create_access_groups', stdout=StringIO())
    return db


@pytest.fixture
def admin_with_catalog(db_with_catalog):
    """Usuario admin con AGR-006 (user_admin_group) — catálogo ya populado."""
    User = get_user_model()
    from apps.access.models import AccessGroup, UserAccessGroup
    user = User.objects.create_user(
        username='admin_conftest',
        password='AdminPass123!',
        state='ACTIVE',
        first_login=False,
    )
    try:
        agr006 = AccessGroup.objects.get(code='AGR-006')
        UserAccessGroup.objects.get_or_create(user=user, access_group=agr006)
    except AccessGroup.DoesNotExist:
        pass
    return user


def _make_admin_client():
    """Helper (no fixture) — crea un admin con AGR-006 y retorna (APIClient, User)."""
    import uuid
    User = get_user_model()
    from apps.access.models import AccessGroup, UserAccessGroup
    user = User.objects.create_user(
        username=f'admin_{uuid.uuid4().hex[:8]}',
        password='AdminPass123!',
        state='ACTIVE',
        first_login=False,
    )
    try:
        agr006 = AccessGroup.objects.get(code='AGR-006')
        UserAccessGroup.objects.get_or_create(user=user, access_group=agr006)
    except AccessGroup.DoesNotExist:
        pass
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_admin(db_with_catalog):
    """Tupla (APIClient autenticado, admin User con AGR-006)."""
    return _make_admin_client()


@pytest.fixture
def client_sin(db):
    """APIClient autenticado con usuario sin permisos RBAC."""
    User = get_user_model()
    import uuid
    user = User.objects.create_user(
        username=f'noperm_{uuid.uuid4().hex[:6]}',
        password='NoPermPass123!',
        state='ACTIVE',
        first_login=False,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def client_acc09(db_with_catalog):
    """APIClient con función ACC-013 (access_audit_view) para UC_ACC_09."""
    import uuid
    User = get_user_model()
    from apps.access.models import AccessGroup, UserAccessGroup, Function, UserPermission
    user = User.objects.create_user(
        username=f'acc09_{uuid.uuid4().hex[:8]}',
        password='AdminPass123!',
        state='ACTIVE',
        first_login=False,
    )
    # Asignar ACC-013 directamente via UserPermission
    for code in ['ACC-013', 'AUD-001', 'AUD-002', 'AUD-003', 'AUD-005']:
        try:
            fn = Function.objects.get(code=code)
            UserPermission.objects.get_or_create(user=user, function=fn)
        except Function.DoesNotExist:
            pass
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_aud04(db_with_catalog):
    """APIClient con funciones AUD para UC_AUD_04."""
    import uuid
    User = get_user_model()
    from apps.access.models import Function, UserPermission
    user = User.objects.create_user(
        username=f'aud04_{uuid.uuid4().hex[:8]}',
        password='AdminPass123!',
        state='ACTIVE',
        first_login=False,
    )
    for code in ['AUD-001', 'AUD-002', 'AUD-003', 'AUD-004', 'AUD-005', 'ACC-013']:
        try:
            fn = Function.objects.get(code=code)
            UserPermission.objects.get_or_create(user=user, function=fn)
        except Function.DoesNotExist:
            pass
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def client_alr05(db_with_catalog):
    return _make_admin_client()


@pytest.fixture
def client_log03(db_with_catalog):
    return _make_admin_client()


@pytest.fixture
def client_rpt09(db_with_catalog):
    return _make_admin_client()


def _ensure_ivr_schema():
    """
    Crea el schema mínimo en test_ivr_legacy que necesitan los tests de unit/.
    Idempotente: usa CREATE TABLE IF NOT EXISTS.
    """
    _CREATE_TEST_DB = """
        CREATE DATABASE IF NOT EXISTS test_ivr_legacy
        CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """
    _MINIMAL_SCHEMA = """
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

        CREATE TABLE IF NOT EXISTS pipeline_event_log (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            ts           DATETIME(3) NOT NULL DEFAULT NOW(3),
            error_type   ENUM('PARAM_INVALIDO','ETL_FALLO','ETL_PARTIAL',
                              'VALIDACION','REPORTE_VACIO','SISTEMA') NOT NULL,
            severity     ENUM('CRITICA','ALTA','MEDIA','BAJA','INFO') NOT NULL,
            sp_nombre    VARCHAR(100),
            sql_state    CHAR(5),
            mysql_errno  INT UNSIGNED,
            p_quarter    VARCHAR(10),
            p_segmento   VARCHAR(20),
            error_message TEXT,
            contexto     LONGTEXT,
            job_log_id   INT,
            ejecutado_por VARCHAR(50)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS etl_runs (
            id             INT AUTO_INCREMENT PRIMARY KEY,
            trimestre      VARCHAR(20) NOT NULL,
            inicio_at      DATETIME NOT NULL DEFAULT NOW(),
            fin_at         DATETIME NULL,
            status         ENUM('en_ejecucion','success','failed','timeout','skip')
                           DEFAULT 'en_ejecucion'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS job_config (
            job_name         VARCHAR(100) NOT NULL PRIMARY KEY,
            is_enabled       TINYINT(1)   NOT NULL DEFAULT 1,
            timeout_seconds  INT          NOT NULL DEFAULT 1800,
            ventana_inicio   TIME,
            ventana_fin      TIME,
            min_intervalo_h  INT          NOT NULL DEFAULT 6,
            notas            TEXT,
            actualizado_en   DATETIME     NOT NULL DEFAULT NOW()
                             ON UPDATE NOW()
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    SOCK = '/run/mysqld/mysqld.sock'
    USER = 'django_user'
    PASS = 'django_pass'

    # Crear la BD primero como root o con el usuario que tenga permisos
    subprocess.run(
        ['mysql', f'--socket={SOCK}', f'-u{USER}', f'-p{PASS}',
         '-e', _CREATE_TEST_DB.strip()],
        capture_output=True,
    )
    # Crear las tablas en test_ivr_legacy
    subprocess.run(
        ['mysql', f'--socket={SOCK}', f'-u{USER}', f'-p{PASS}',
         'test_ivr_legacy'],
        input=_MINIMAL_SCHEMA,
        text=True,
        capture_output=True,
    )


# ── Mantener MariaDB vivo durante toda la sesión de tests/unit/ ────────────────
import subprocess, os, pwd, time

def _mariadb_alive_unit() -> bool:
    """Verifica si MariaDB está disponible."""
    result = subprocess.run(
        ['mysql', '--socket=/run/mysqld/mysqld.sock',
         '-u', 'django_user', '-pdjango_pass', '-e', 'SELECT 1;'],
        capture_output=True, timeout=3,
    )
    return result.returncode == 0


@pytest.fixture(scope='session', autouse=True)
def ensure_mariadb_unit():
    """
    H-INFRA-001: mantiene MariaDB disponible durante toda la sesión de tests.
    Si MySQL no está corriendo, lo arranca antes de que pytest-django
    intente verificar la BD 'ivr'.
    """
    if _mariadb_alive_unit():
        yield
        return

    # Arrancar MariaDB
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
        ['mariadbd',
         '--user=mysql',
         '--socket=/run/mysqld/mysqld.sock',
         '--pid-file=/run/mysqld/mysqld.pid',
         '--datadir=/var/lib/mysql'],
        preexec_fn=drop_privs,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Esperar hasta 30 segundos
    for _ in range(30):
        time.sleep(1)
        if _mariadb_alive_unit():
            break

    # Crear schema mínimo en test_ivr_legacy
    _ensure_ivr_schema()

    yield

    # NO terminar el proceso — pytest puede tener más tests
    # que dependen de MariaDB. Se termina solo cuando el proceso padre muere.
