"""
Database router for dual-database setup.
PostgreSQL (default) for all apps except ivr_legacy.
MariaDB (legacy) for ivr_legacy - READ-ONLY (CNST-003).
"""

LEGACY_APPS = {'ivr_legacy'}
DEFAULT_APPS = {
    'access', 'alerts', 'audit', 'authentication', 'core',
    'dashboard', 'ivr', 'pipeline', 'reports', 'users',
}


class DatabaseRouter:
    """
    Routes ivr_legacy to read-only MariaDB.
    All other apps use PostgreSQL (default).
    """

    def db_for_read(self, model, **hints):
        if model._meta.app_label in LEGACY_APPS:
            return 'legacy'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in LEGACY_APPS:
            raise Exception("ivr_legacy is READ-ONLY (CNST-003). Write operations are not allowed.")
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        db1 = 'legacy' if obj1._meta.app_label in LEGACY_APPS else 'default'
        db2 = 'legacy' if obj2._meta.app_label in LEGACY_APPS else 'default'
        return db1 == db2

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in LEGACY_APPS:
            return db == 'legacy'
        return db == 'default'
