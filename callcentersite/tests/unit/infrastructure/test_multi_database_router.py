"""
tests/unit/infrastructure/test_multi_database_router.py

DB router multi-base-de-datos — infraestructura de conexiones PostgreSQL/MariaDB.
"""
import pytest
from django.conf import settings


@pytest.mark.unit
class TestDatabaseRouter:
    """
    Verifica que el DatabaseRouter implementa CNST-003 correctamente.
    BR-001: IVR read-only. El router nunca migra en ivr_legacy.
    """

    def test_allow_migrate_default_returns_true(self):
        """Migraciones Django solo en PostgreSQL (default)."""
        from config.db_router import DatabaseRouter
        router = DatabaseRouter()
        for app in ('access', 'users', 'auth', 'audit', 'authentication'):
            assert router.allow_migrate('default', app) is True, \
                f"allow_migrate('default', '{app}') debe ser True"

    def test_allow_migrate_ivr_returns_false_not_none(self):
        """
        BR-001: Django nunca migra en MariaDB (ivr).
        CRÍTICO: debe ser False, no None.
        None delega la decisión a otros routers — no garantiza el bloqueo.
        False bloquea explícitamente.
        """
        from config.db_router import DatabaseRouter
        router = DatabaseRouter()
        result = router.allow_migrate('ivr', 'access')
        assert result is False, (
            f"allow_migrate('ivr', 'access') retorna {result!r}. "
            "Debe ser False (no None) para bloquear explícitamente. "
            "None delega a otros routers — comportamiento no determinista."
        )

    def test_allow_migrate_ivr_any_app_returns_false(self):
        """Ninguna app migra a ivr — bloqueo universal."""
        from config.db_router import DatabaseRouter
        router = DatabaseRouter()
        for app in ('access', 'users', 'reports', 'pipeline', 'alerts', 'audit'):
            assert router.allow_migrate('ivr', app) is False, \
                f"allow_migrate('ivr', '{app}') debe ser False"

    def test_db_for_read_returns_default(self):
        """Todos los modelos ORM leen de PostgreSQL."""
        from config.db_router import DatabaseRouter
        from apps.users.models import User
        router = DatabaseRouter()
        assert router.db_for_read(User) == 'default'

    def test_db_for_write_returns_default(self):
        """Todos los modelos ORM escriben en PostgreSQL."""
        from config.db_router import DatabaseRouter
        from apps.users.models import User
        router = DatabaseRouter()
        assert router.db_for_write(User) == 'default'


@pytest.mark.unit
class TestIvrTestDatabaseConfig:
    """
    F0-T6: La BD 'ivr' en testing_local tiene MIGRATE: False, CREATE_DB: False.
    El settings/fase0_testing.py tiene TEST: {NAME: None}.
    Ambas configuraciones previenen que Django intente crear test_ivr_legacy.
    """

    def test_ivr_test_name_is_real_db_in_fase0_settings(self):
        """
        Desde la migración a BDs reales (H-INT-007): ivr TEST NAME es
        'test_ivr_legacy'. fase0_testing ya no usa SQLite en memoria.
        """
        ivr_test = settings.DATABASES.get('ivr', {}).get('TEST', {})
        assert ivr_test.get('NAME') == 'test_ivr_legacy', (
            "fase0_testing usa test_ivr_legacy desde H-INT-007."
        )
    def test_ivr_database_engine_is_defined(self):
        """La BD 'ivr' tiene ENGINE configurado."""
        assert 'ivr' in settings.DATABASES
        assert settings.DATABASES['ivr']['ENGINE']
